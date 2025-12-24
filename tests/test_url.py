"""
Tests for URL shortening endpoints.
"""
import pytest


class TestUrlCreation:
    """Test URL shortening endpoint."""
    
    def test_create_short_url_success(self, client, auth_headers):
        """Test creating a short URL."""
        response = client.post(
            "/api/url-shortner/",
            json={"url": "https://www.example.com"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "short_code" in data
        assert data["message"] == "Short URL created successfully."
        assert len(data["short_code"]) > 0
    
    def test_create_short_url_duplicate(self, client, auth_headers):
        """Test creating duplicate short URL returns existing code."""
        url = {"url": "https://www.duplicate.com"}
        
        # First creation
        response1 = client.post("/api/url-shortner/", json=url, headers=auth_headers)
        assert response1.status_code == 201
        short_code1 = response1.json()["short_code"]
        
        # Duplicate creation
        response2 = client.post("/api/url-shortner/", json=url, headers=auth_headers)
        assert response2.status_code == 400
        short_code2 = response2.json()["short_code"]
        assert response2.json()["message"] == "URL already exists."
        assert short_code1 == short_code2  # Same code returned
    
    def test_create_short_url_without_auth(self, client):
        """Test creating URL without authentication."""
        response = client.post(
            "/api/url-shortner/",
            json={"url": "https://www.example.com"}
        )
        
        assert response.status_code == 401
    
    def test_create_short_url_invalid_url(self, client, auth_headers):
        """Test creating URL with invalid format."""
        response = client.post(
            "/api/url-shortner/",
            json={"url": "not-a-valid-url"},
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestGetUserUrls:
    """Test fetching user's URLs with pagination."""
    
    def test_get_urls_empty_list(self, client, auth_headers):
        """Test getting URLs when user has no URLs."""
        response = client.get("/api/url-shortner/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
        assert data["pagination"]["total_items"] == 0
    
    def test_get_urls_with_data(self, client, auth_headers):
        """Test getting URLs when user has created some."""
        # Create 3 URLs
        for i in range(3):
            client.post(
                "/api/url-shortner/",
                json={"url": f"https://example{i}.com"},
                headers=auth_headers
            )
        
        response = client.get("/api/url-shortner/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert data["pagination"]["total_items"] == 3
        assert data["pagination"]["total_pages"] == 1
    
    def test_get_urls_pagination(self, client, auth_headers):
        """Test pagination of URLs."""
        # Create 5 URLs
        for i in range(5):
            client.post(
                "/api/url-shortner/",
                json={"url": f"https://example{i}.com"},
                headers=auth_headers
            )
        
        # Get first page with limit 3
        response = client.get("/api/url-shortner/?page=1&limit=3", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert data["pagination"]["total_items"] == 5
        assert data["pagination"]["total_pages"] == 2
        assert data["pagination"]["current_page"] == 1
        assert data["pagination"]["next_page"] == 2
        
        # Get second page
        response = client.get("/api/url-shortner/?page=2&limit=3", headers=auth_headers)
        data = response.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["current_page"] == 2
        assert data["pagination"]["prev_page"] == 1
        assert data["pagination"]["next_page"] is None
    
    def test_get_urls_user_isolation(self, client, auth_headers, second_auth_headers):
        """Test that users only see their own URLs."""
        # First user creates URL
        client.post(
            "/api/url-shortner/",
            json={"url": "https://user1.com"},
            headers=auth_headers
        )
        
        # Second user creates URL
        client.post(
            "/api/url-shortner/",
            json={"url": "https://user2.com"},
            headers=second_auth_headers
        )
        
        # First user should only see 1 URL
        response1 = client.get("/api/url-shortner/", headers=auth_headers)
        assert len(response1.json()["data"]) == 1
        
        # Second user should only see 1 URL
        response2 = client.get("/api/url-shortner/", headers=second_auth_headers)
        assert len(response2.json()["data"]) == 1


class TestDeleteUrls:
    """Test URL deletion endpoint."""
    
    def test_delete_single_url(self, client, auth_headers):
        """Test deleting a single URL."""
        # Create URL
        create_response = client.post(
            "/api/url-shortner/",
            json={"url": "https://todelete.com"},
            headers=auth_headers
        )
        short_code = create_response.json()["short_code"]
        
        # Delete URL
        response = client.post(
            "/api/url-shortner/delete",
            json={"url_codes": [short_code]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "URLs deleted successfully."
        
        # Verify URL is deleted
        urls_response = client.get("/api/url-shortner/", headers=auth_headers)
        assert len(urls_response.json()["data"]) == 0
    
    def test_delete_multiple_urls(self, client, auth_headers):
        """Test bulk deletion of URLs."""
        # Create 3 URLs
        codes = []
        for i in range(3):
            response = client.post(
                "/api/url-shortner/",
                json={"url": f"https://delete{i}.com"},
                headers=auth_headers
            )
            codes.append(response.json()["short_code"])
        
        # Delete all 3 URLs
        response = client.post(
            "/api/url-shortner/delete",
            json={"url_codes": codes},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify all deleted
        urls_response = client.get("/api/url-shortner/", headers=auth_headers)
        assert len(urls_response.json()["data"]) == 0
    
    def test_delete_url_unauthorized(self, client, auth_headers, second_auth_headers):
        """Test that users cannot delete other users' URLs."""
        # First user creates URL
        create_response = client.post(
            "/api/url-shortner/",
            json={"url": "https://protected.com"},
            headers=auth_headers
        )
        short_code = create_response.json()["short_code"]
        
        # Second user tries to delete it
        response = client.post(
            "/api/url-shortner/delete",
            json={"url_codes": [short_code]},
            headers=second_auth_headers
        )
        
        # Should succeed but not actually delete (no error, just no-op)
        assert response.status_code == 200
        
        # Verify URL still exists for first user
        urls_response = client.get("/api/url-shortner/", headers=auth_headers)
        assert len(urls_response.json()["data"]) == 1


class TestUrlAnalytics:
    """Test analytics endpoints."""
    
    def test_get_top_performing_urls_empty(self, client, auth_headers):
        """Test top performing URLs when user has no URLs."""
        response = client.get("/api/url-shortner/analytics/top-performing", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
        assert data["count"] == 0
    
    def test_get_top_performing_urls_with_data(self, client, auth_headers):
        """Test top performing URLs endpoint."""
        # Create some URLs
        for i in range(3):
            client.post(
                "/api/url-shortner/",
                json={"url": f"https://analytics{i}.com"},
                headers=auth_headers
            )
        
        response = client.get("/api/url-shortner/analytics/top-performing", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
    
    def test_get_top_performing_urls_limit(self, client, auth_headers):
        """Test top performing URLs with custom limit."""
        # Create 10 URLs
        for i in range(10):
            client.post(
                "/api/url-shortner/",
                json={"url": f"https://analytics{i}.com"},
                headers=auth_headers
            )
        
        response = client.get("/api/url-shortner/analytics/top-performing?limit=3", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] <= 3
    
    def test_get_global_analytics(self, client, auth_headers):
        """Test global analytics endpoint."""
        # Create some URLs
        for i in range(2):
            client.post(
                "/api/url-shortner/",
                json={"url": f"https://global{i}.com"},
                headers=auth_headers
            )
        
        response = client.get("/api/url-shortner/analytics/global", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "countries" in data
        assert "devices" in data
        assert "sources" in data
        assert data["summary"]["total_urls"] == 2
