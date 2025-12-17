from hashids import Hashids
from os import getenv
from app.db_utils import safe_commit, safe_commit_with_refresh
from sqlalchemy.orm import Session,load_only
from app.models import Url,UrlAnalytics
from ua_parser import user_agent_parser
from app.auth.dependencies import (get_country_by_ip)
from app.database import db_connection
from app.redis_client import get_redis_client
from sqlalchemy import func
from urllib.parse import urlparse


hash = Hashids(min_length=8, salt=getenv("SALT"))


def categorize_referrer(referrer: str) -> str:
    """Categorize referrer into meaningful source categories"""
    if not referrer:
        return "Direct"
    
    referrer_lower = referrer.lower()
    
    # Social Media
    social_platforms = ['facebook', 'twitter', 'instagram', 'linkedin', 'pinterest', 
                       'reddit', 'tiktok', 'snapchat', 'whatsapp', 'telegram']
    if any(platform in referrer_lower for platform in social_platforms):
        return "Social Media"
    
    # Search Engines
    search_engines = ['google', 'bing', 'yahoo', 'duckduckgo', 'baidu', 'yandex']
    if any(engine in referrer_lower for engine in search_engines):
        return "Google" if 'google' in referrer_lower else "Search Engine"
    
    # Email
    if 'mail' in referrer_lower or 'android-app://com.google.android.gm' in referrer_lower:
        return "Email"
    
    # Developer platforms
    dev_platforms = ['github', 'gitlab', 'stackoverflow', 'stackexchange']
    for platform in dev_platforms:
        if platform in referrer_lower:
            return platform.replace('stack', 'Stack ').title()
    
    # Try to extract domain
    try:
        parsed = urlparse(referrer if referrer.startswith('http') else f'http://{referrer}')
        domain = parsed.netloc or parsed.path
        if domain:
            # Remove www. prefix
            domain = domain.replace('www.', '')
            return domain
    except:
        pass
    
    return "Other"


def url_hash(url_db_id:str) -> str:
    # Now implement a hashing function to generate a unique code for the URL.
    """Generate Base62-style short code from DB ID."""
    return hash.encode(url_db_id)



def create_short_url(db:Session, user_id:int, original_url:str) -> tuple[str, bool]:
    # First, check if the URL already exists for the user

    existing = (db.query(Url).options(load_only(
                Url.id, Url.code)).filter(
                Url.user == user_id,
                Url.url == original_url
            ).first())
    
    if existing:
        return existing.code, False
    else:
        new_url = Url(url=original_url, user=user_id)
        new_url = safe_commit_with_refresh(db, new_url)
        short_code = url_hash(url_db_id=new_url.id)
        new_url.code = short_code
        safe_commit(db, new_url)
        
        return short_code, True


def add_url_analytics(
    url_code: int,
    ip_address: str,
    referrer: str,
    user_agent: str
):
    """Create analytics record for a given short URL visit."""
    db = db_connection()

    # Validate URL exists
    url_obj = db.query(Url).options(load_only(
                Url.id,Url.click_count)).filter(Url.code == url_code).first()
    
    if not url_obj:
        return False
    
    # Get country from IP
    country= get_country_by_ip(ip_address)
    
    # Parse device/browser/os from UA using ua-parser
    device_type = None
    browser_name = None
    os_name = None
    is_bot = False
    
    if user_agent:
        parsed = user_agent_parser.Parse(user_agent)
        
        # Extract browser
        browser_family = parsed.get('user_agent', {}).get('family')
        browser_name = browser_family if browser_family != 'Other' else None
        
        # Extract OS
        os_family = parsed.get('os', {}).get('family')
        os_name = os_family if os_family != 'Other' else None
        
        # Extract and categorize device
        device_family = parsed.get('device', {}).get('family')
        ua_lower = user_agent.lower()
        
        # Bot detection logic
        bot_indicators = [
            'bot', 'crawler', 'spider', 'scraper', 'whatsapp', 'telegram',
            'facebook', 'twitter', 'linkedin', 'slack', 'discord', 'instagram',
            'snapchat', 'preview', 'fetcher', 'validator', 'checker'
        ]
        
        # Check if it's a bot
        is_bot = (
            device_family == 'Spider' or
            device_type == 'Spider' or
            (browser_name and any(indicator in browser_name.lower() for indicator in bot_indicators)) or
            any(indicator in ua_lower for indicator in bot_indicators)
        )
        
        # Categorize device type properly
        # Check for specific known devices first (iPhone, iPad, etc.)
        if device_family and device_family not in ['Other', 'K']:
            device_type = device_family
        # Handle Android "K" privacy placeholder and infer from OS/UA
        elif os_family in ['iOS', 'Android', 'Windows Phone', 'BlackBerry OS']:
            # Mobile OS detected
            if 'tablet' in ua_lower or 'ipad' in ua_lower:
                device_type = 'Tablet'
            else:
                device_type = 'Mobile'
        # Desktop OS detection
        elif os_family in ['Windows', 'Mac OS X', 'Linux', 'Ubuntu', 'Chrome OS']:
            device_type = 'Desktop'
        # Fallback: check UA string patterns
        elif 'mobile' in ua_lower or 'android' in ua_lower:
            device_type = 'Mobile'
        elif 'tablet' in ua_lower:
            device_type = 'Tablet'
        else:
            device_type = 'Unknown'
    
    # Categorize referrer source
    source_category = categorize_referrer(referrer)
    
    analytics = UrlAnalytics(
        url=url_obj.id,
        ip_address=ip_address,
        referrer=referrer,
        country=country,
        device=device_type,
        browser=browser_name,
        os=os_name,
        user_agent=user_agent,
        is_bot=is_bot
    )

    safe_commit(db, analytics)

    # Only increment click count for real users, not bots
    if not is_bot:
        url_obj.click_count += 1
        safe_commit(db, url_obj)
    
    # Update Redis analytics cache
    update_analytics_cache(
        url_id=url_obj.id,
        country=country,
        device=device_type,
        source_category=source_category,
        is_bot=is_bot
    )

    return True



def async_cache_fill(code: str, original_url: str):
    redis_client = get_redis_client()
    redis_client.set(code, original_url,ex=60*60*48)  # Cache for 48 hours
    print(f"[CACHE FILLED] {code} → {original_url}")


def update_analytics_cache(url_id: int, country: str, device: str, source_category: str, is_bot: bool):
    """Update Redis analytics cache with new data"""
    try:
        redis_client = get_redis_client()
        
        # Only update cache for real users, not bots
        if not is_bot:
            # Global analytics
            if country:
                redis_client.hincrby("analytics:global:countries", country, 1)
            if device:
                redis_client.hincrby("analytics:global:devices", device, 1)
            if source_category:
                redis_client.hincrby("analytics:global:sources", source_category, 1)
            
            # Per-URL analytics
            if country:
                redis_client.hincrby(f"analytics:url:{url_id}:countries", country, 1)
            if device:
                redis_client.hincrby(f"analytics:url:{url_id}:devices", device, 1)
            if source_category:
                redis_client.hincrby(f"analytics:url:{url_id}:sources", source_category, 1)
        
        # Track bot sources separately
        else:
            if source_category:
                redis_client.hincrby("analytics:global:bot_sources", source_category, 1)
        
        return True
    except Exception as e:
        print(f"[REDIS ERROR] Analytics cache update failed: {e}")
        return False


def invalidate_cache(url_codes: list[str]):
    """Remove URL codes from Redis cache"""
    try:
        redis_client = get_redis_client()
        if url_codes:
            deleted_keys = redis_client.delete(*url_codes)
            print(f"[CACHE INVALIDATED] Removed {deleted_keys} keys from cache")
        return True
    except Exception as e:
        print(f"[CACHE INVALIDATION ERROR] {str(e)}")
        return False


def get_top_performing_urls(db: Session, user_id: int, limit: int = 5):
    """Get top performing URLs with analytics breakdown"""
    try:
        redis_client = get_redis_client()
        
        # Get top URLs by click count
        top_urls = (
            db.query(Url)
            .filter(Url.user == user_id)
            .order_by(Url.click_count.desc())
            .limit(limit)
            .all()
        )
        
        result = []
        for url in top_urls:
            # Get analytics from Redis (faster) with fallback to DB
            countries = redis_client.hgetall(f"analytics:url:{url.id}:countries")
            devices = redis_client.hgetall(f"analytics:url:{url.id}:devices")
            sources = redis_client.hgetall(f"analytics:url:{url.id}:sources")
            
            # If Redis is empty, then fallback to DB query
            if not countries and not devices and not sources:
                print(f"[REDIS MISS] Analytics cache miss for URL ID {url.id}")
                # Query from DB and populate Redis
                analytics_data = (
                    db.query(
                        UrlAnalytics.country,
                        UrlAnalytics.device,
                        func.count(UrlAnalytics.id).label('count')
                    )
                    .filter(UrlAnalytics.url == url.id, UrlAnalytics.is_bot == False)
                    .group_by(UrlAnalytics.country, UrlAnalytics.device)
                    .all()
                )
                
                # Rebuild Redis cache
                for row in analytics_data:
                    if row.country:
                        redis_client.hincrby(f"analytics:url:{url.id}:countries", row.country, row.count)
                    if row.device:
                        redis_client.hincrby(f"analytics:url:{url.id}:devices", row.device, row.count)
                
                # Query sources separately
                source_data = (
                    db.query(UrlAnalytics.referrer, func.count(UrlAnalytics.id).label('count'))
                    .filter(UrlAnalytics.url == url.id, UrlAnalytics.is_bot == False)
                    .group_by(UrlAnalytics.referrer)
                    .all()
                )
                
                for row in source_data:
                    source_cat = categorize_referrer(row.referrer)
                    redis_client.hincrby(f"analytics:url:{url.id}:sources", source_cat, row.count)
                
                # Re-fetch from Redis
                countries = redis_client.hgetall(f"analytics:url:{url.id}:countries")
                devices = redis_client.hgetall(f"analytics:url:{url.id}:devices")
                sources = redis_client.hgetall(f"analytics:url:{url.id}:sources")
            
            print(f"[REDIS HIT] Analytics cache hit for URL ID {url.id}")
            # Convert Redis bytes to dict and calculate percentages
            total_clicks = url.click_count or 1  # Avoid division by zero
            
            countries_data = [
                {
                    "country": k.decode() if isinstance(k, bytes) else k,
                    "percentage": round((int(v) / total_clicks) * 100),
                    "count": int(v)
                }
                for k, v in countries.items()
            ]
            countries_data.sort(key=lambda x: x['count'], reverse=True)
            
            devices_data = [
                {
                    "device": k.decode() if isinstance(k, bytes) else k,
                    "percentage": round((int(v) / total_clicks) * 100),
                    "count": int(v)
                }
                for k, v in devices.items()
            ]
            devices_data.sort(key=lambda x: x['count'], reverse=True)
            
            sources_data = [
                {
                    "source": k.decode() if isinstance(k, bytes) else k,
                    "percentage": round((int(v) / total_clicks) * 100),
                    "count": int(v)
                }
                for k, v in sources.items()
            ]
            sources_data.sort(key=lambda x: x['count'], reverse=True)
            
            result.append({
                "url": url.url,
                "code": url.code,
                "total_clicks": url.click_count,
                "created_at": int(url.createdon.timestamp()),
                "countries": countries_data[:3],  # Top 3
                "devices": devices_data[:2],  # Top 2
                "sources": sources_data[:3]  # Top 3
            })
        
        return result
    
    except Exception as e:
        print(f"[ERROR] get_top_performing_urls: {e}")
        return []