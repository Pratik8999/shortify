"""
Rate limiting and security utilities for contact form
"""
from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import threading


class RateLimiter:
    """
    Simple in-memory rate limiter for contact form submissions.
    In production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self, max_requests: int = 3, window_minutes: int = 60):
        """
        Args:
            max_requests: Maximum number of requests allowed per window
            window_minutes: Time window in minutes
        """
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier: str) -> Tuple[bool, str]:
        """
        Check if request is allowed for the given identifier (IP address).
        
        Returns:
            Tuple of (is_allowed, message)
        """
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=self.window_minutes)
            
            # Get requests for this identifier
            requests = self.requests[identifier]
            
            # Remove old requests outside the window
            requests[:] = [req_time for req_time in requests if req_time > cutoff]
            
            # Check if limit exceeded
            if len(requests) >= self.max_requests:
                oldest_request = min(requests)
                time_until_reset = oldest_request + timedelta(minutes=self.window_minutes) - now
                minutes_left = int(time_until_reset.total_seconds() / 60) + 1
                
                return False, f"Please try again in {minutes_left} minutes."
            
            # Add current request
            requests.append(now)
            return True, "Request allowed"


# Global rate limiter instance - 3 requests per hour per IP
contact_rate_limiter = RateLimiter(max_requests=3, window_minutes=60)


def check_origin(request: Request, allowed_origins: list[str]) -> bool:
    """
    Check if request origin is from allowed domains.
    
    Args:
        request: FastAPI Request object
        allowed_origins: List of allowed origin URLs
    
    Returns:
        True if origin is allowed, False otherwise
    """
    origin = request.headers.get("origin") or request.headers.get("referer")
    
    if not origin:
        # Allow requests without origin (e.g., direct API calls, testing)
        # In production, you might want to reject these
        return True
    
    # Check if origin matches any allowed origins
    for allowed in allowed_origins:
        if origin.startswith(allowed):
            return True
    
    return False


def validate_honeypot(honeypot_value: str | None) -> bool:
    """
    Validate honeypot field (should be empty for legitimate users).
    Bots often fill all form fields.
    
    Args:
        honeypot_value: Value of the honeypot field
    
    Returns:
        True if valid (empty), False if filled (likely bot)
    """
    return not honeypot_value or honeypot_value.strip() == ""
