from pydantic import BaseModel, HttpUrl
from typing import Optional,List
from app.models import UrlAnalytics
from datetime import datetime
from pydantic import validator
from pydantic import field_validator


class UrlCreate(BaseModel):
    url: HttpUrl


class UrlCreationResponse(BaseModel):
    short_code: str
    message: str


class UrlListingResponse(BaseModel):
    id: int
    url: HttpUrl
    code: str
    createdon: int


    @field_validator("createdon", mode="before")
    def _dt_to_unix(cls, v):
        return int(v.timestamp())

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


class Pagination(BaseModel):
    current_page: int
    next_page: int | None
    prev_page: int | None
    total_pages: int
    total_items: int

class PaginatedUrlResponse(BaseModel):
    data: list[UrlListingResponse]
    pagination: Pagination
    

class PaginatedURLs(BaseModel):
    data: List[UrlListingResponse]
    pagination: Pagination


class UrlBulkDelete(BaseModel):
    url_codes: List[str]
    
    @field_validator("url_codes")
    @classmethod
    def validate_url_codes(cls, v):
        if not v:
            raise ValueError("At least one URL code must be provided")
        if len(v) > 100:  # Reasonable limit
            raise ValueError("Cannot delete more than 100 URLs at once")
        return v