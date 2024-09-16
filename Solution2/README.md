# Solution 2
## Solution #2
###### To further decrease the number of gRPC calls in the provided solution, we need to enhance the caching and deduplication strategy. The primary idea is to reduce the frequency and volume of unique (company, title) pairs being sent to the gRPC endpoint. Here are some improvements that can be made to achieve this
1. **User Batch Processing and Deduplication Across Files**
    1. **Currently**, the algorithm processes files one at a time and deduplicates entries within each file. However, to maximize efficiency, we should consider deduplicating across multiple files within a certain timeframe (e.g., within the last minute, hour, or even daily batch). This would avoid making duplicate gRPC calls for repeated (company, title) pairs that appear in different files
    2. **Improvement**:
        1. Batch Processing Across Files: Instead of processing each file individually, collect all the (company, title) pairs from multiple files first. Deduplicate this combined list and then perform batch gRPC calls.
        2. This approach ensures that if the same (company, title) pair appears in different files, it is processed only once per batch window.
2. **Efficient Cache Eviction Strategy**
    1. To avoid redundant gRPC calls over a longer period, you can employ a more intelligence cache eviction policy in Redis
        1. Time-Based Expiry
        2. Least Recently used Eviction Policy
3. **Preemptive Caching with Bloom Filters**
    1. Bloom filters can be used as a pre-filtering mechanism to check if a (company, title) pair has potentially been seen before without having to query the Redis cache directly. Bloom filters are memory-efficient data structures that provide fast probabilistic membership tests with some acceptable false positive rates but no false negatives.
    2. **Improvements**:
        1. **Bloom Filter in Front of Redis Cache**: Use a Bloom filter that is populated with all (company, title) pairs seen in a certain window (e.g., daily). When processing new entries, check the Bloom filter first. If it indicates that the pair might be in the cache, proceed with the Redis cache lookup; otherwise, skip directly to the gRPC call and cache the result.
4. **Precompute and Cache Common Titles for Popular Companies**
    1. It might be beneficial to precompute and cache seniority levels for very common titles (e.g., "Software Engineer", "Account Manager") for popular companies (e.g., "Google", "Amazon"). You could periodically run a batch job to update the cache with these precomputed values.
    2. **Improvement**:
        1. **Periodic Cache Precomputation**: Run a background job that analyzes historical data and identifies (company, title) pairs that are frequently requested. Precompute their seniority levels and store them in the cache to avoid future gRPC calls for these pairs.
5. **Probabilistic gRPC Calls for Less Frequent Titles**
    1. If some (company, title) pairs are very rare (e.g., only appear once or twice), you might decide to use a probabilistic approach to decide whether to cache them at all.
    2. **Improvement**
        1. **Frequency-Based gRPC Call Probability**: For infrequent (company, title) pairs, decide whether to make a gRPC call or use a default "Unknown" seniority level. This reduces the number of unique gRPC calls for rare titles and ensures the cache remains optimized for more frequent requests.
6. **Data Clustering and Intelligent Inference**
    1. There might be a way to cluster job titles that are similar in nature or derive from the same base role (e.g., "Senior Software Engineer" and "Software Engineer II"). Instead of treating each job title as unique, cluster similar titles together and infer their seniority once. This requires natural language processing (NLP) techniques.
    2. **Improvement**:
        1. **Title Clustering**: Use NLP techniques like word embeddings or transformer models to cluster titles into similar groups. Make a gRPC call only for the representative title in each cluster, and infer similar titles from the same company using this result.
7. **Incremental Cache Updates with TTL Refresh**
    1. When a gRPC call is made, it can refresh the TTL for frequently accessed cache entries to avoid unnecessary evictions.
    2. **Improvement**:
        1. **Incremental TTL Refresh**: When the system sees a (company, title) pair that already exists in the cache, it increments or refreshes the TTL, ensuring that frequently accessed pairs stay cached longer.
8. **Reduce Redis Round-Trips with Multi-Get Commands**
    1. Instead of querying Redis for each (company, title) pair separately, use multi-get commands to fetch multiple pairs in one round-trip. This can reduce the network latency overhead when querying Redis.
    2. **Improvement**:
        1. **Redis MGET for Batch Cache Lookups**: Use the Redis MGET command to retrieve multiple cache values at once. This reduces the network calls to Redis, improving the overall performance
