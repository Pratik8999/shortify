from fastapi import FastAPI, Depends, Response, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import json
from app.auth.routers import auth_router
from app.url.routers import url_router
from app.database import get_db,engine
from app.admin.views import UserAdmin, UrlAdmin, UrlAnalyticsAdmin
from app.models import Url
from app.url.url_utils import add_url_analytics, async_cache_fill
from app.redis_client import get_redis_client
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from os import getenv
from sqladmin import Admin

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize SQLAdmin
admin = Admin(app, engine)

# Get CORS origins from environment variable
cors_origins_str = getenv("CORS_ORIGINS", "")
# print(f"Raw CORS_ORIGINS: {cors_origins_str}")

cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth_router)
app.include_router(url_router)

# Initialize admin views
admin.add_view(UserAdmin)
admin.add_view(UrlAdmin)
admin.add_view(UrlAnalyticsAdmin)


# Root level redirect endpoint for URL shortener
@app.get("/{url_code}")
def redirect_response(url_code: str, request: Request, background_tasks: BackgroundTasks,
                     db: Session = Depends(get_db)):

    ip = request.client.host
    referrer = request.headers.get("referer")
    user_agent = request.headers.get("user-agent")

    # First check in redis for the url code, if found return the url from redis cache
    redis_client = get_redis_client()

    cached_url = redis_client.get(url_code)

    if cached_url:
        print(f"[CACHE HIT] url_code={url_code} → {cached_url}")

        background_tasks.add_task(
            add_url_analytics,
            url_code=url_code,
            ip_address=ip,
            referrer=referrer,
            user_agent=user_agent,
        )
        return RedirectResponse(cached_url, status_code=307)
    
    else:
        print(f"[CACHE MISS] url_code={url_code}")
        
        # Check if the incoming url code exists in the database
        url = db.query(Url.url, Url.code).filter(Url.code == url_code).first()

        if not url:
            return Response(content=json.dumps({"message": "URL not found."}), media_type="application/json", status_code=404)
        
        # Asynchronously fill the cache
        background_tasks.add_task(
            async_cache_fill,
            code=url_code,
            original_url=url.url
        )

        # Now if the url found then return the original url for redirection with 307 temporary redirect as
        # we intentionally use 307 for temporary redirection so that everytime user's first visit is recorded in analytics
        # as 307 redirect does not cache the redirection unlike 301 permanent redirect

        # Registering background task to add analytics
        background_tasks.add_task(
            add_url_analytics,
            url_code=url_code,
            ip_address=ip,
            referrer=referrer,
            user_agent=user_agent,
        )

        return RedirectResponse(url.url, status_code=307)
