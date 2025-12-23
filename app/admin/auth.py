from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth.hashing import verify_password
import secrets


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        """Handle admin login"""
        form = await request.form()
        email = form.get("username")
        password = form.get("password")
        
        # Get database session
        db: Session = next(get_db())
        
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            
            # Check if user exists, is active, is superuser, and password is correct
            if user and user.isactive and user.is_superuser and verify_password(password, user.password):
                # Store user info in session
                request.session.update({
                    "user_id": user.id,
                    "user_email": user.email,
                    "user_name": user.name,
                    "is_superuser": True
                })
                return True
            
            return False
        finally:
            db.close()
    
    async def logout(self, request: Request) -> bool:
        """Handle admin logout"""
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        """Check if user is authenticated"""
        # Check if user session exists and is superuser
        user_id = request.session.get("user_id")
        is_superuser = request.session.get("is_superuser")
        
        if not user_id or not is_superuser:
            return False
        
        # Optionally verify user still exists and is still superuser
        db: Session = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.isactive and user.is_superuser:
                return True
            return False
        finally:
            db.close()


from os import getenv

# Get secret key from environment variables
def get_secret_key():
    """Get secret key from environment for session management"""
    # Read from ADMIN_SECRET_KEY environment variable
    # This is the same secret key you set in .env file
    return getenv("ADMIN_SECRET_KEY")
