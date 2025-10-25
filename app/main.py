from fastapi import FastAPI
from app.auth.routers import auth_router

app = FastAPI()

app.include_router(auth_router)

