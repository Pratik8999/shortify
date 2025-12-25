"""
Tests for visit tracking endpoint.
"""
import pytest


class TestVisitTracking:
    """Test visit tracking endpoint."""
    
    def test_ping_endpoint_success(self, client):
        """Test ping endpoint tracks visit successfully."""
        response = client.get("/api/info/ping")
        
        assert response.status_code == 200
        # Should return empty dict on success
        assert response.json() == {}
    
    def test_ping_endpoint_with_user_agent(self, client):
        """Test ping endpoint with custom user agent."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = client.get("/api/info/ping", headers=headers)
        
        assert response.status_code == 200
        assert response.json() == {}
    
    def test_ping_endpoint_multiple_visits(self, client):
        """Test multiple visits from same client."""
        # First visit
        response1 = client.get("/api/info/ping")
        assert response1.status_code == 200
        
        # Second visit (should also succeed)
        response2 = client.get("/api/info/ping")
        assert response2.status_code == 200
    
    def test_ping_endpoint_mobile_user_agent(self, client):
        """Test ping with mobile user agent."""
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        }
        
        response = client.get("/api/info/ping", headers=headers)
        
        assert response.status_code == 200
    
    def test_ping_endpoint_bot_user_agent(self, client):
        """Test ping with bot user agent."""
        headers = {
            "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"
        }
        
        response = client.get("/api/info/ping", headers=headers)
        
        assert response.status_code == 200
