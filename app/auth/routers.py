from fastapi.routing import APIRouter
from app.database import get_db
from fastapi import Depends,HTTPException,Request
from sqlalchemy.orm import Session
from app.db_utils import safe_commit,safe_commit_with_refresh
from app.auth.schemas import (UserCreate, UserBase, LoginConfirmation, UserLogin, AccessToken, RefreshToken)
from app.auth.hashing import (hash_password, verify_password)
from app.auth.jwt_handler import (create_access_token, create_refresh_token, verify_token, invalidate_token)
from app.models import User
from sqlalchemy.orm import lazyload,load_only
from fastapi.security import OAuth2PasswordBearer


auth_router = APIRouter(tags=["Authentication"],prefix="/user")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")


@auth_router.post("/register", response_model=LoginConfirmation, status_code=201)
def register_user(user:UserCreate, db:Session = Depends(get_db)):
    
    existing_user = db.query(User).options(load_only(User.email)).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")
    else:
        hashed_password = hash_password(user.password)
        new_user = User(name=user.name, email=user.email,password=hashed_password,country="India")
        
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
            return True
        else:
            print("Failed to invalidate tokens during logout")
            raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    except Exception as ex:
        print("Got unexpected exception during logout:", str(ex))
        raise HTTPException(status_code=400, detail="Invalid or expired token")