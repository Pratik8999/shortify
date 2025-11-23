import redis
from functools import lru_cache


@lru_cache()
def get_redis_client() -> redis.Redis:
    
    return redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True
    )