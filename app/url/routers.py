from fastapi.routing import APIRouter
from fastapi import Depends,Response,Query,BackgroundTasks
import json
from app.auth.dependencies import (get_current_user)
from app.models import (User, Url)
from app.url.schemas import (UrlCreate, Pagination, PaginatedUrlResponse, 
                            UrlBulkDelete)
from app.database import get_db
from app.url.url_utils import (create_short_url,add_url_analytics, async_cache_fill, 
                            invalidate_cache, get_top_performing_urls, get_global_analytics)
from sqlalchemy.orm import Session,load_only


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
                                            ), media_type="application/json", status_code=400)


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


@url_router.post("/delete")
def delete_urls(bulk_delete: UrlBulkDelete, background_tasks: BackgroundTasks,
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Delete one or multiple URLs by their codes.
    Highly optimized with single query and bulk deletion.
    Works for both single URL and multiple URLs.
    """
    url_codes = bulk_delete.url_codes
    
    try:
        # Optimized query - only fetch codes we need to verify
        existing_urls = db.query(Url).options(load_only(Url.code)).filter(
            Url.code.in_(url_codes),
            Url.user == user.id
        ).all()
        
        existing_codes = [url.code for url in existing_urls]
        
        db.query(Url).filter(
            Url.code.in_(url_codes),
            Url.user == user.id
        ).delete(synchronize_session=False)

        db.commit()
        
        # Add cache invalidation to background task
        background_tasks.add_task(invalidate_cache, existing_codes)
        
        return Response(json.dumps({"message":"URLs deleted successfully."}), media_type="application/json", status_code=200)
        
    except Exception as e:
        print(f"URL deletion failed: {str(e)}")
        return Response(json.dumps({"message":"URL deletion failed."}), media_type="application/json", status_code=500)


@url_router.get("/analytics/top-performing")
def get_top_performing_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(5, ge=1, le=10, description="Number of top URLs to return")
):
    """
    Get top performing URLs with analytics breakdown.
    Returns top URLs ordered by click count with country, device, and source breakdowns.
    """
    try:
        top_urls_data = get_top_performing_urls(db, user.id, limit)
        
        return Response(
            content=json.dumps({
                "data": top_urls_data,
                "count": len(top_urls_data)
            }),
            media_type="application/json",
            status_code=200
        )
    except Exception as e:
        print(f"[ERROR] Top performing analytics endpoint: {e}")
        return Response(
            content=json.dumps({"message": "Failed to fetch analytics"}),
            media_type="application/json",
            status_code=500
        )


@url_router.get("/analytics/global")
def get_global_analytics_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get global analytics across all user's URLs.
    Returns summary (total URLs, total clicks, this month clicks) and breakdowns by country, device, and source.
    """
    try:
        global_data = get_global_analytics(db, user.id)
        
        return Response(
            content=json.dumps(global_data),
            media_type="application/json",
            status_code=200
        )
    except Exception as e:
        print(f"[ERROR] Global analytics endpoint: {e}")
        return Response(
            content=json.dumps({
                "summary": {"total_urls": 0, "total_clicks": 0, "this_month_clicks": 0},
                "countries": [],
                "devices": [],
                "sources": []
            }),
            media_type="application/json",
            status_code=500
        )