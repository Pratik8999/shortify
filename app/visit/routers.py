from fastapi import APIRouter, Depends, Request, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AppVisit, SupportRequest
from app.auth.country_codes import get_country_name
from app.auth.dependencies import get_client_ip
from ua_parser import user_agent_parser
from os import getenv
import requests
from app.logging_config import visit_logger
from app.visit.schemas import SupportRequestCreate, SupportRequestResponse
from app.visit.security import contact_rate_limiter, check_origin
from app.db_utils import safe_commit_with_refresh

visit_router = APIRouter(
    prefix="/api/info",
    tags=["Visit Tracking"]
)


def get_ip_info(ip: str) -> dict:
    """
    Fetch IP information from ipinfo.io API.
    """
    try:
        request_url = getenv("IPINFO_ENDPOINT") + f"/{ip}?token={getenv('IPINFO_API_KEY')}"
        response = requests.get(request_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        visit_logger.error(f"Error fetching IP info for {ip}: {str(e)}", exc_info=True)
        return {}


@visit_router.get("/ping")
async def track_visit(request: Request, db: Session = Depends(get_db)):
    """
    Track application visits by IP address.
    """
    # Get client IP address
    client_ip = get_client_ip(request)
    
    # Get user agent from request headers
    user_agent = request.headers.get("user-agent")
    
    # Parse device, browser, and OS from user agent
    device_type = None
    browser_name = None
    os_name = None
    
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
        
        # Categorize device type
        if device_family == 'Spider':
            device_type = 'Spider'
        elif device_family in ['iPhone', 'iPad']:
            device_type = device_family
        elif os_family in ['iOS', 'Android', 'Windows Phone', 'BlackBerry OS']:
            if 'tablet' in ua_lower or 'ipad' in ua_lower:
                device_type = 'Tablet'
            else:
                device_type = 'Mobile'
        elif os_family in ['Windows', 'Mac OS X', 'Linux', 'Ubuntu', 'Chrome OS']:
            device_type = 'Desktop'
        elif 'mobile' in ua_lower or 'android' in ua_lower:
            device_type = 'Mobile'
        elif 'tablet' in ua_lower:
            device_type = 'Tablet'
        else:
            device_type = 'Unknown'
    
    # New visitor - fetch IP info
    ip_info = get_ip_info(client_ip)
    
    # Extract location data if available
    loc = ip_info.get('loc', ',').split(',')
    latitude = loc[0] if len(loc) > 0 else None
    longitude = loc[1] if len(loc) > 1 else None
    
    country_code = ip_info.get('country')
    country_name = get_country_name(country_code) if country_code else None
    
    try:
        # Create new visit record
        new_visit = AppVisit(
            ip_address=client_ip,
            country=country_name,
            city=ip_info.get('city'),
            region=ip_info.get('region'),
            latitude=latitude,
            longitude=longitude,
            timezone=ip_info.get('timezone'),
            org=ip_info.get('org'),
            postal=ip_info.get('postal'),
            device=device_type,
            browser=browser_name,
            os=os_name
        )
        
        db.add(new_visit)
        db.commit()
        
        return {}
    except Exception as e:
        db.rollback()
        visit_logger.error(f"Error tracking visit from {client_ip}: {str(e)}", exc_info=True)
        return {}


@visit_router.post("/contact", response_model=SupportRequestResponse, status_code=201)
async def submit_contact_form(
    support_request: SupportRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    honeypot: str | None = Header(None, alias="X-Honeypot")
):
    """
    Submit a support/contact request.
    Rate limiting: 3 requests per hour per IP
    Origin validation: Only allowed origins can submit
    Honeypot field: Hidden field to catch bots (sent via header)
    IP logging: Track submissions by IP for abuse prevention 
    
    """
    try:
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Check rate limit
        is_allowed, rate_message = contact_rate_limiter.is_allowed(client_ip)
        if not is_allowed:
            visit_logger.warning(f"Rate limit exceeded for contact form from IP: {client_ip}")
            raise HTTPException(status_code=429, detail=rate_message)
        
        # Check origin (CORS - ensure request comes from your frontend)
        allowed_origins = getenv("CORS_ORIGINS", "").split(",")
        allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
        
        if allowed_origins and not check_origin(request, allowed_origins):
            origin = request.headers.get("origin", "unknown")
            visit_logger.warning(f"Contact form submission from unauthorized origin: {origin}, IP: {client_ip}")
            raise HTTPException(status_code=403, detail="Request not allowed from this origin")
        
        # Check honeypot (bot detection)
        if honeypot and honeypot.strip():
            visit_logger.warning(f"Bot detected in contact form (honeypot filled) from IP: {client_ip}")
            # Return success to bot but don't save
            return SupportRequestResponse(
                success=True,
                message="Thank you for your message. We'll get back to you soon!",
                request_id=None
            )
        
        # Create support request
        new_request = SupportRequest(
            name=support_request.name,
            email=support_request.email,
            message=support_request.message,
            ip_address=client_ip,
            status="pending"
        )
        
        new_request = safe_commit_with_refresh(db, new_request)
        
        visit_logger.info(f"New support request #{new_request.id} from {support_request.email}")
        
        return SupportRequestResponse(
            success=True,
            message="Thank you for your message. We'll get back to you soon!",
            request_id=new_request.id
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (rate limit, origin check)
        raise
    
    except Exception as e:
        visit_logger.error(f"Error creating support request from {client_ip}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to submit your request. Please try again later."
        )

    
