from fastapi.routing import APIRouter
from fastapi import Depends,Response,Query,BackgroundTasks,HTTPException
import json
from datetime import datetime, timezone, timedelta
from app.auth.dependencies import (get_current_user)
from app.models import (User, Url)
from app.url.schemas import (UrlCreate, Pagination, PaginatedUrlResponse, 
                            UrlBulkDelete, UrlUpdate)
from app.database import get_db
from app.url.url_utils import (create_short_url,invalidate_cache, get_top_performing_urls, get_global_analytics)
from sqlalchemy.orm import Session,load_only
from app.logging_config import url_logger


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
def get_urls_for_user(
    db:Session = Depends(get_db), 
    user:User = Depends(get_current_user), 
    page:int = Query(1, ge=1), 
    limit:int = Query(10, ge=1, le=100),
    from_date:str = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date:str = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get paginated URLs for the authenticated user with optional date range filtering.
    Maximum date range is 60 days.
    """
    # Build base query
    query = db.query(Url).filter(Url.user == user.id)
    
    # Apply date range filters if provided
    if from_date or to_date:
        try:
            # Parse dates
            start_dt = None
            end_dt = None
            
            if from_date:
                start_dt = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            if to_date:
                # Set to end of day (23:59:59)
                end_dt = datetime.strptime(to_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, tzinfo=timezone.utc
                )
            
            # Validate: both dates must be provided together
            if (from_date and not to_date) or (to_date and not from_date):
                raise HTTPException(
                    status_code=400,
                    detail="Both from_date and to_date must be provided together"
                )
            
            # Validate: from_date must be before to_date
            if start_dt and end_dt and start_dt > end_dt:
                raise HTTPException(
                    status_code=400,
                    detail="from_date must be before or equal to to_date"
                )
            
            # Validate: maximum 60-day window
            if start_dt and end_dt:
                date_diff = (end_dt - start_dt).days
                if date_diff > 60:
                    raise HTTPException(
                        status_code=400,
                        detail="Date range cannot exceed 60 days"
                    )
                
                # Apply filters
                query = query.filter(Url.createdon >= start_dt, Url.createdon <= end_dt)
                
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    # Calculate total items and pages
    offset = (page - 1) * limit
    total_items = query.count()
    total_pages = (total_items + limit - 1) // limit

    # Fetch the paginated data
    urls = (
        query
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


@url_router.put("/")
def update_url_title(
    url_update: UrlUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Update the title of a URL. Only the owner can update their URL.
    """
    try:
        # Find the URL and verify ownership
        url = db.query(Url).filter(
            Url.id == url_update.url_id,
            Url.user == user.id
        ).first()
        
        if not url:
            return Response(
                content=json.dumps({"message": "URL not found or you don't have permission to update it"}),
                media_type="application/json",
                status_code=404
            )
        
        # Update the title
        url.title = url_update.title
        db.commit()
        db.refresh(url)
        
        return Response(
            content=json.dumps({
                "message": "URL title updated successfully",
                "url_id": url.id,
                "title": url.title
            }),
            media_type="application/json",
            status_code=200
        )
        
    except Exception as e:
        url_logger.error(f"URL title update failed: {str(e)}", exc_info=True)
        db.rollback()
        return Response(
            content=json.dumps({"message": "Failed to update URL title"}),
            media_type="application/json",
            status_code=500
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
        url_logger.error(f"URL deletion failed: {str(e)}", exc_info=True)
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
        url_logger.error(f"Top performing analytics endpoint error: {str(e)}", exc_info=True)
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
        url_logger.error(f"Global analytics endpoint error: {str(e)}", exc_info=True)
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