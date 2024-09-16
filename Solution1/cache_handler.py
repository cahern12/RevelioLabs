import redis

class CacheHandler:
    def __init__(self, host, port):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)

    def get_seniority_from_cache(self, company, title):
        """Check if seniority level for a (company, title) pair is in the Redis cache."""
        key = f"{company}|{title}"
        return self.redis_client.get(key)

    def set_seniority_in_cache(self, company, title, seniority):
        """Set the seniority level for a (company, title) pair in the Redis cache."""
        key = f"{company}|{title}"
        self.redis_client.set(key, seniority)
