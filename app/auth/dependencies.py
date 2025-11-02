from app.models import User
from fastapi.security.oauth2 import OAuth2PasswordBearer
from fastapi import Depends,HTTPException
from sqlalchemy.orm import Session,load_only,lazyload
from app.auth.jwt_handler import verify_token
from app.database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

 
def get_current_user(access_token:str = Depends(oauth2_scheme), db:Session = Depends(get_db)):
    verified_token = verify_token(token=access_token, expected_type="access", db=db)

    if not verified_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = verified_token.get("sub",None)

    user = db.query(User).options(load_only(User.country,User.id)).filter(User.id == int(user_id), User.isactive == True).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user