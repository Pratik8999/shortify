from fastapi.routing import APIRouter
from app.database import get_db
from fastapi import Depends,HTTPException,Request
from sqlalchemy.orm import Session
from app.db_utils import safe_commit,safe_commit_with_refresh
from app.auth.schemas import (UserCreate, UserRead, LoginConfirmation, UserLogin, AccessToken, RefreshToken, UserUpdate)
from app.auth.hashing import (hash_password, verify_password)
from app.auth.jwt_handler import (create_access_token, create_refresh_token, verify_token, invalidate_token)
from app.models import User
from sqlalchemy.orm import load_only
from fastapi.security import OAuth2PasswordBearer
from app.auth.dependencies import get_current_user, get_country_by_ip, get_client_ip
from sqlalchemy.exc import IntegrityError
from app.logging_config import auth_logger



auth_router = APIRouter(tags=["Authentication"],prefix="/api/auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@auth_router.post("/register", response_model=LoginConfirmation, status_code=201)
def register_user(user:UserCreate,request:Request, db:Session = Depends(get_db)):
    
    existing_user = db.query(User).options(load_only(User.email)).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")
    else:
        hashed_password = hash_password(user.password)
        client_ip = get_client_ip(request) 
        country= get_country_by_ip(client_ip)
        new_user = User(name=user.name, email=user.email,password=hashed_password,country=country)
        
        new_user = safe_commit_with_refresh(db,new_user)
        payload = {"sub":str(new_user.id)}

        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)
        
        return {"access_token":access_token,"refresh_token":refresh_token,"token_type": "bearer",
                "userid":new_user.id, "message":"Registration successful.."}


@auth_router.post("/login", response_model=LoginConfirmation)
def login(login_creds:UserLogin, db:Session = Depends(get_db)):
    user = db.query(User).options(load_only(User.email, User.password, 
                                            User.id)).filter(User.email == login_creds.email, User.isactive == True).first()
    if not user:
        raise HTTPException(400, "User with this email doesn't exists.")
    else:
        # Check password
        if not verify_password(login_creds.password, user.password):
            raise HTTPException(400, "Invalid Credentials.")
        else:
            payload = {"sub":str(user.id)}
            access_token = create_access_token(payload)
            refresh_token = create_refresh_token(payload)
            
            return {"access_token":access_token,"refresh_token":refresh_token,"token_type": "bearer",
                    "userid":user.id, "message":"Login successful.."}


@auth_router.post("/refresh", response_model=AccessToken)
def refresh_token(refresh_token: RefreshToken, db: Session = Depends(get_db)):
    payload = verify_token(refresh_token.refresh_token, expected_type="refresh", db=db)
    if not payload:
        raise HTTPException(status_code=403, detail="Invalid or expired refresh token")
    
    new_access_token = create_access_token({"sub": payload.get("sub")})
    return {"access_token": new_access_token, "token_type": "bearer"}



@auth_router.post("/logout", status_code=200)
def logout(body: dict, db: Session = Depends(get_db), access_token: str = Depends(oauth2_scheme)):
    try:
        if invalidate_token(access_token,body.get('refresh_token',None),db):
            return {"message": "Successfully logged out."}
        else:
            auth_logger.error("Failed to invalidate tokens during logout")
            raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    except Exception as ex:
        auth_logger.error(f"Unexpected exception during logout: {str(ex)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    

@auth_router.get("/profile", response_model=UserRead)
def get_profile(user:User = Depends(get_current_user)):
    return user


@auth_router.put("/profile", response_model=UserRead)
def update_profile(user_update:UserUpdate, user:User = Depends(get_current_user), db:Session = Depends(get_db)):
    try:
        user.name = user_update.name
        user.email = user_update.email
        
        updated_user = safe_commit_with_refresh(db, user)
        return updated_user
    
    except IntegrityError as ie:
        auth_logger.error(f"Profile update integrity error: {ie.orig.diag.message_detail}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ie.orig.diag.message_detail)) 