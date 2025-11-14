from pydantic import BaseModel, HttpUrl
from typing import Optional
from app.models import UrlAnalytics
from datetime import datetime


class UrlCreate(BaseModel):
    url: HttpUrl


class UrlCreationResponse(BaseModel):
    short_code: str
    message: str


class UrlListingResponse(BaseModel):
    id:int
    url:HttpUrl
    code:str
    createdon:datetime

    class Config:
        from_attributes = True



class UrlAnalyticsCreate(BaseModel):
    url_id: int
    ip_address: Optional[str] = None
    country: Optional[str] = None
    referrer: Optional[str] = None
    device: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    user_agent: Optional[str] = None