"""
Tests for utility functions.
"""
import pytest
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, create_refresh_token, verify_token
from datetime import datetime, timedelta


class TestPasswordHashing:
    """Test password hashing utilities."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "correctpassword"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "correctpassword"
        hashed = hash_password(password)
        
        assert verify_password("wrongpassword", hashed) is False
    
    def test_hash_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        
        assert hash1 != hash2
    
    def test_hash_same_password_produces_different_hashes(self):
        """Test that hashing same password twice produces different results (salt)."""
        password = "samepassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTHandling:
    """Test JWT token utilities."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        payload = {"sub": "123"}
        token = create_access_token(payload)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        payload = {"sub": "123"}
        token = create_refresh_token(payload)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_access_token(self, db_session):
        """Test verification of valid access token."""
        payload = {"sub": "123"}
        token = create_access_token(payload)
        
        decoded = verify_token(token, expected_type="access", db=db_session)
        
        assert decoded is not None
        assert decoded["sub"] == "123"
        assert decoded["type"] == "access"
    
    def test_verify_valid_refresh_token(self, db_session):
        """Test verification of valid refresh token."""
        payload = {"sub": "456"}
        token = create_refresh_token(payload)
        
        decoded = verify_token(token, expected_type="refresh", db=db_session)
        
        assert decoded is not None
        assert decoded["sub"] == "456"
        assert decoded["type"] == "refresh"
    
    def test_verify_invalid_token(self, db_session):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        
        decoded = verify_token(invalid_token, expected_type="access", db=db_session)
        
        assert decoded is None
    
    def test_verify_token_wrong_type(self, db_session):
        """Test verification fails when token type doesn't match."""
        payload = {"sub": "123"}
        access_token = create_access_token(payload)
        
        # Try to verify access token as refresh token
        decoded = verify_token(access_token, expected_type="refresh", db=db_session)
        
        assert decoded is None
    
    def test_tokens_contain_expiry(self, db_session):
        """Test that tokens contain expiry time."""
        payload = {"sub": "123"}
        access_token = create_access_token(payload)
        
        decoded = verify_token(access_token, expected_type="access", db=db_session)
        
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)
