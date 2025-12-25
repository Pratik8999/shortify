from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class SupportRequestCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of the person")
    email: EmailStr = Field(..., description="Valid email address")
    message: str = Field(..., min_length=10, max_length=2000, description="Support query message")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and sanitize name"""
        # Remove extra whitespace
        v = ' '.join(v.split())
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")
        
        return v
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate and sanitize message"""
        # Remove extra whitespace but preserve line breaks
        v = '\n'.join(' '.join(line.split()) for line in v.split('\n'))
        v = v.strip()
        
        # Check minimum length after sanitization
        if len(v) < 10:
            raise ValueError("Message must be at least 10 characters long")
        
        return v


class SupportRequestResponse(BaseModel):
    success: bool
    message: str
    request_id: int | None = None
    
    model_config = {"from_attributes": True}
