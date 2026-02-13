import redis
from app.db.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
    max_connections=20
)

if __name__ == "__main__":
    try:
        redis_client.ping()
        print("Redis is working!")
    except redis.RedisError as e:
        print(f"Redis connection failed: {e}")
