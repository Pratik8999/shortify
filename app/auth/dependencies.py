from app.models import User
from fastapi.security.oauth2 import OAuth2PasswordBearer
from fastapi import Depends,HTTPException
from sqlalchemy.orm import Session,load_only
from app.auth.jwt_handler import verify_token
from app.database import get_db
from os import getenv
import requests


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

def get_country_by_ip(ip):
    request_url = getenv("IPINFO_ENDPOINT") + f"/{ip}?token={getenv('IPINFO_API_KEY')}"
    response = requests.get(request_url)
    response_data = response.json()
    return response_data.get('country')
    # lat, lon = response_data.get('loc').split(',')
    # return [country, response_data.get('region'), response_data.get('city'), lat , lon]