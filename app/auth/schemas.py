from pydantic import BaseModel,EmailStr,field_validator
from typing import Optional
import re

class UserBase(BaseModel):
    name: str
    email: EmailStr
    country: str

    @field_validator("email",mode="before")
    @classmethod
    def format_email(cls, email) -> str:
        return  email.lower().strip()


    @field_validator("name")
    @classmethod
    def validate_name(cls,name:str):
        if len(name.strip()) < 3:
            raise ValueError("Name must be at least 3 characters long")
        
        return name.strip()
    

class UserCreate(UserBase):
    password: str
    
    @field_validator("password")
    @classmethod
    def validate_password(cls,password:str):
        # Using a more robust regex that combines length and character requirements:
        PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$"
        
        if not re.match(PASSWORD_REGEX, password):
            raise ValueError(
                "Password must contain at least 8 characters, "
                "one uppercase letter, one lowercase letter, one digit, "
                "and one special character (!@#$%^&*())."
            )

        return password


class UserRead(BaseModel):
    id:int
    name: str
    email: EmailStr
    country: str
    isactive: bool

    model_config = {
        "from_attributes": True
    }


class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    
    @field_validator("email",mode="before")
    @classmethod
    def format_email(cls, email) -> str:
        return email.lower().strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email",mode="before")
    @classmethod
    def format_email(cls, email) -> str:
        return email.lower().strip()


class AccessToken(BaseModel):
    access_token: str
    token_type: str


class RefreshToken(BaseModel):
    refresh_token: str


class LogoutTokens(BaseModel):
    access_token: str
    refresh_token: str
    

class LoginConfirmation(AccessToken):
    userid:int
    refresh_token: str
    message:str