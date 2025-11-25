from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routers import auth_router
from app.url.routers import url_router
from dotenv import load_dotenv
from os import getenv

# Load environment variables
load_dotenv()

app = FastAPI()

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
