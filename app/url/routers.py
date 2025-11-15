from fastapi.routing import APIRouter
from fastapi import Depends,Response,Request,Query
import json
from app.auth.dependencies import (get_current_user)
from app.models import (User, Url, UrlAnalytics)
from app.url.schemas import (UrlCreate, UrlListingResponse,UrlAnalyticsCreate, Pagination, PaginatedUrlResponse,PaginatedURLs)
from app.database import get_db
from app.url.url_utils import (create_short_url,add_url_analytics)
from sqlalchemy.orm import Session,load_only
from app.db_utils import safe_delete


url_router = APIRouter(tags=["URLs"], prefix="/api/url-shortner")


@url_router.post("/")
def url_shortner(url_create:UrlCreate, user:User = Depends(get_current_user), db:Session = Depends(get_db)):
    incoming_url = str(url_create.url)

    short_code, created = create_short_url(db=db, user_id=user.id, original_url=incoming_url)

    if created:
        return Response(content=json.dumps({"short_code": short_code,
                                            "message": "Short URL created successfully."}
                                            ), media_type="application/json", status_code=201)
    else:
        return Response(content=json.dumps({"short_code": short_code,
                                            "message": "URL already exists."}
                                            ), media_type="application/json", status_code=200)


@url_router.get("/", response_model=PaginatedUrlResponse)
def get_urls_for_user(db:Session = Depends(get_db), user:User = Depends(get_current_user), 
                      page:int = Query(1, ge=1), limit:int = Query(10, ge=1, le=100)):
    
    # First i'll calculate the total number of items and pages
    offset = (page - 1) * limit

    total_items = db.query(Url).filter(Url.user == user.id).count()
    total_pages = (total_items + limit - 1) // limit

    # Then I'll fetch the paginated data
    urls = (
        db.query(Url)
        .filter(Url.user == user.id)
        .order_by(Url.createdon.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Prepare pagination metadata
    pagination = Pagination(
        current_page=page,
        next_page=page + 1 if page < total_pages else None,
        prev_page=page - 1 if page > 1 else None,
        total_pages=total_pages,
        total_items=total_items
    )
    
    return PaginatedUrlResponse(
        data=urls,
        pagination=pagination
    )

@url_router.get("/{url_code}")
def redirect_response(url:str,  db:Session = Depends(get_db)):
    pass



@url_router.delete("/{url_code}")
def delete_url(url_code:str, db:Session = Depends(get_db), user:User = Depends(get_current_user)):
    
    url = db.query(Url).options(load_only(Url.id)).filter(Url.code == url_code, Url.user == user.id).first()
    
    if not url:
        return Response(content=json.dumps({"message": "URL not found."}), media_type="application/json", status_code=404)
    
    safe_delete(db, url)

    return Response(content=json.dumps({"message": "URL deleted successfully."}), media_type="application/json", status_code=200)



@url_router.post("/analytics")
def post_url_analytics(
    analytics_data: UrlAnalyticsCreate,
    request: Request,
    db: Session = Depends(get_db)
):

    # Extract client-side metadata
    ip_address = request.client.host
    referrer = request.headers.get("referer")
    user_agent = request.headers.get("user-agent")


    # Country will come from analytics_data (optional)
    country = analytics_data.country

    success = add_url_analytics(
        db=db,
        url_id=analytics_data.url_id,
        ip_address=ip_address,
        referrer=referrer,
        user_agent=user_agent,
        country=country
    )

    if not success:
        return Response(
            content=json.dumps({"message": "URL not found"}),
            status_code=404,
            media_type="application/json"
        )

    return Response(
        content=json.dumps({"message": "Analytics recorded"}),
        status_code=201,
        media_type="application/json"
    )