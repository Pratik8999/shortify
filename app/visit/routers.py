from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AppVisit
from app.auth.country_codes import get_country_name
from app.auth.dependencies import get_client_ip
from os import getenv
import requests

visit_router = APIRouter(
    prefix="/api/visit",
    tags=["Visit Tracking"]
)


def get_ip_info(ip: str) -> dict:
    """
    Fetch IP information from ipinfo.io API.
    
    Args:
        ip: IP address to lookup
        
    Returns:
        Dictionary containing IP information
    """
    try:
        request_url = getenv("IPINFO_ENDPOINT") + f"/{ip}?token={getenv('IPINFO_API_KEY')}"
        response = requests.get(request_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching IP info: {e}")
        return {}


@visit_router.get("/track")
async def track_visit(request: Request, db: Session = Depends(get_db)):
    """
    Track application visits by IP address.
    
    - If IP is new, creates a new visit record with location data
    - If IP exists, returns 200 OK without any updates
    - Returns success status
    """
    # Get client IP address
    client_ip = get_client_ip(request)
    
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
            postal=ip_info.get('postal')
        )
        
        db.add(new_visit)
        db.commit()
        
        return {}
    except Exception as e:
        db.rollback()
        print(f"Error tracking visit: {e}")
        return {}
    
