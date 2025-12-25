import pytest


class TestUserRegistration:
    
    def test_register_user_success(self, client):
        response = client.post("/api/auth/register", json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "userid" in data
        assert data["message"] == "Registration successful.."
    
    def test_register_duplicate_email(self, client, test_user):
        response = client.post("/api/auth/register", json={
            "name": "Another User",
            "email": "test@example.com",  # Same as test_user
            "password": "Password123!"
        })
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_register_invalid_email(self, client):
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "invalid-email",
            "password": "Password123!"
        })
        
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    
    def test_login_success(self, client, test_user):
        """Test successful login with correct credentials."""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["message"] == "Login successful.."
    
    def test_login_wrong_password(self, client, test_user):
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPass123!"
        })
        
        assert response.status_code == 400
        assert "Invalid Credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        })
        
        assert response.status_code == 400
        assert "doesn't exists" in response.json()["detail"]


class TestTokenRefresh:
    
    def test_refresh_token_success(self, client, test_user):
        refresh_token = test_user["refresh_token"]
        
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client):
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_token_here"
        })
        
        assert response.status_code == 403


class TestLogout:
    
    def test_logout_success(self, client, test_user):
        access_token = test_user["access_token"]
        refresh_token = test_user["refresh_token"]
        
        response = client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out."
    
    def test_logout_without_token(self, client):
        response = client.post("/api/auth/logout", json={})
        
        assert response.status_code == 401  # Unauthorized


class TestUserProfile:
    
    def test_get_profile_success(self, client, auth_headers, test_user):
        response = client.get("/api/auth/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "id" in data
    
    def test_get_profile_without_auth(self, client):
        response = client.get("/api/auth/profile")
        
        assert response.status_code == 401
    
    def test_update_profile_success(self, client, auth_headers):
        """Test updating user profile."""
        response = client.put(
            "/api/auth/profile",
            json={
                "name": "Updated Name",
                "email": "updated@example.com"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "updated@example.com"
    
    def test_update_profile_duplicate_email(self, client, auth_headers, second_user):
        response = client.put(
            "/api/auth/profile",
            json={
                "name": "Test User",
                "email": "second@example.com"  # Email of second_user
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
