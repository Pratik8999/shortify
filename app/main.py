from fastapi import FastAPI
from app.auth.routers import auth_router
from app.url.routers import url_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(url_router)
