from hashids import Hashids
from os import getenv
from app.db_utils import safe_commit, safe_commit_with_refresh
from sqlalchemy.orm import Session,load_only
from app.models import Url,UrlAnalytics
from user_agents import parse as parse_ua


hash = Hashids(min_length=8, salt=getenv("SALT"))


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
    db: Session,
    url_id: int,
    ip_address: str,
    referrer: str,
    user_agent: str,
    country: str | None = None
):
    """Create analytics record for a given short URL visit."""
    
    # Validate URL exists
    url_obj = db.query(Url).options(load_only(
                Url.id,Url.click_count)).filter(Url.id == url_id).first()
    
    if not url_obj:
        return False
    
    # Parse device/browser/os from UA
    ua = parse_ua(user_agent) if user_agent else None
    
    analytics = UrlAnalytics(
        url=url_id,
        ip_address=ip_address,
        referrer=referrer,
        country=country,
        device=ua.device.family if ua else None,
        browser=ua.browser.family if ua else None,
        os=ua.os.family if ua else None,
        user_agent=user_agent
    )

    safe_commit(db, analytics)

    # increment click count
    url_obj.click_count += 1
    safe_commit(db, url_obj)

    return True
