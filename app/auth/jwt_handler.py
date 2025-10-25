from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi import HTTPException
from dotenv import load_dotenv
import os
from uuid import uuid4
from app.models import BlacklistedToken
from app.db_utils import safe_commit

load_dotenv()  # Load environment variables from .env file
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh","jti": str(uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def verify_token(token: str, expected_type: str, db:Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        
        if db.query(BlacklistedToken).filter_by(jti=jti).first():
            raise HTTPException(status_code=401, detail="Token has been blacklisted")
        
        if payload.get("type") != expected_type:
            return None
        return payload
    
    except JWTError:
        return None
    

def invalidate_token(access_token:str, refresh_token:str, db:Session):
    try:
        acs_payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        rfs_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        if acs_payload.get("type") == "access" and rfs_payload.get("type") == "refresh":
            safe_commit(db=db, object=BlacklistedToken(jti=acs_payload.get('jti')))
            safe_commit(db=db, object=BlacklistedToken(jti=rfs_payload.get('jti')))
            return True
        
        return False
        
    except JWTError as je:
        raise je