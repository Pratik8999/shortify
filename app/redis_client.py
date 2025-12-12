import redis
import os
from functools import lru_cache


@lru_cache()
def get_redis_client() -> redis.Redis:
    # Redis configuration from environment variables
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    redis_password = os.getenv("REDIS_PASSWORD")  # None if not set
    redis_username = os.getenv("REDIS_USERNAME")  # None if not set
    redis_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
    redis_ssl_cert_reqs = os.getenv("REDIS_SSL_CERT_REQS", "required")
    redis_connection_timeout = int(os.getenv("REDIS_CONNECTION_TIMEOUT", "5"))
    redis_socket_timeout = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
    
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        username=redis_username,
        password=redis_password,
        ssl=redis_ssl,
        ssl_cert_reqs=redis_ssl_cert_reqs if redis_ssl else None,
        socket_connect_timeout=redis_connection_timeout,
        socket_timeout=redis_socket_timeout,
        decode_responses=True
    )


def check_redis_connection() -> bool:
    """
    Check if Redis connection is healthy.
    Returns True if connection is successful, False otherwise.
    """
    try:
        client = get_redis_client()
        # Test connection with a simple ping
        response = client.ping()
        return response is True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False
