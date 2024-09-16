import redis
from pybloom_live import BloomFilter

class CacheHandler:
    def __init__(self, host, port, bloom_capacity, bloom_error_rate):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.bloom_filter = BloomFilter(capacity=bloom_capacity, error_rate=bloom_error_rate)

    def check_bloom_filter(self, unique_pairs):
        """Use a Bloom filter to check if a (company, title) pair might be in the cache."""
        probable_cached_pairs = {}
        missing_pairs = {}
        for pair, data in unique_pairs.items():
            if pair in self.bloom_filter:
                probable_cached_pairs[pair] = data
            else:
                missing_pairs[pair] = data
                self.bloom_filter.add(pair)
        return probable_cached_pairs, missing_pairs

    def batch_redis_lookup(self, probable_cached_pairs):
        """Perform a batched lookup in Redis for probable cached pairs."""
        keys = [f"{company}|{title}" for (company, title) in probable_cached_pairs]
        results = self.redis_client.mget(keys)

        cached_pairs = {}
        missing_pairs = {}
        for i, key in enumerate(probable_cached_pairs):
            if results[i] is not None:
                cached_pairs[key] = int(results[i])
            else:
                missing_pairs[key] = probable_cached_pairs[key]
        return cached_pairs, missing_pairs

    def update_cache_with_seniority(self, inferred_seniorities, missing_pairs):
        """Update Redis cache with inferred seniority values."""
        for uuid, seniority in inferred_seniorities.items():
            pair = [(k, v) for k, v in missing_pairs.items() if v['uuid'] == uuid][0]
            company, title = pair[0]
            redis_key = f"{company}|{title}"
            self.redis_client.set(redis_key, seniority, ex=3600)  # Set with expiration, e.g., 1 hour
