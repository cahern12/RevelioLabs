# RevelioLabs

## Solution #1 & 2 Updates
1. I refactored the solutions below into multiple files / classes:
    1. **S3Handler**: Handles all S3-related operations, such as reading & writing to S3
    2. **CacheHandler**: Manages Redis caching operations
    3. **GRPCClient**: Encapsulates all gRPC related operations
    4. **JobProcessor**: Orchestrates the job processing workflow, including reading files, deduplication, interacting with the cache, making gRPC calls, and writing results.
    5. **main.py**: The entry point of initializing all components and coordinating the processing of files using multithreading

## Solution #1
To design an efficient data augmentation service for inferring seniority levels from job postings, the primarily goal is to minimize the number of costly gRPC calls to the Revelio Labs seniority model while ensuring timely process of the JSONL files. Here is a breakdown of the proposed solution
1. **Overview of the Solution**
    1. **Cacheing Service**: This service will cache the results of seniority inferences to avoid redundant gRPC calls for the same (company, title) pairs. The cache should be highly performant, scalable, and able to handle billions of entries efficiently
    2. **Data Augmentation Service**: This service will read the JSONL files from the S3 bucket, use the caching service to check if a seniority level is already available for a given (company, title) pair, make gRPC calls when necessary, and write the output with seniority information back to another S3 bucket.
2. **Caching Service Design**
    1. The caching service is critical for minimizing gRPC calls. The choice of caching solution is influenced by factors such as speed, scalability, persistence, and ease of integration. Given the scale (20M distinct pairs in a year), we need a cache that:
        1. Supports high read and write throughput.
        2. Can store millions of key-value pairs in memory with efficient memory usage.
        3. Can persist the cache to avoid data loss and allow cold-start optimizations.
    2. Chosen Caching Solution: Redis with Persistence (Justification)
        1. High Throughput and Low Latency: Redis is an in-memory data store, known for sub-millisecond latency and high throughput, making it ideal for caching scenarios
        2. Persistence Options: Redis provides two options for persistence: RDB (snapshotting) and AOF (Append Only File). RDB provides point-in-time snapshots, which are suitable for reducing the frequency of disk writes, while AOF logs every write operation
        3. Data Expiry: Redis allows setting expiration times on keys, which can be useful if the seniority level information becomes less relevant over time.
        4. Scalability: Redis Cluster supports horizontal scaling by sharding data across multiple nodes. This ensures the cache can grow to accommodate the 20M distinct pairs.
    3. Cache Key Design
        1. We use a hash function to prevent excessive key length and ensure fast lookups
        2. The cache key will be in combination of the company and title, normalized to ensure consistency. For example:
3. **Data Augmentation Service Design**
    1. **Read JASONL Files from S3:** The service will poll the *s3://rl-data/job-postings-raw/* bucket for new files, using S3 event notifications or a scheduled job.
    2. **Batch Processing and Deduplication:**
        1. For each file, load the JASONL lines into memory.
        2. Deduplicate the lines by (company, title) pairs. This reduces the number of cache lookups and gRPC calls.
    4. **Check Cache and infer seniority:**
        1. For each unique (company, title) pair:
            1. Cache lookup: check if the seniority level is already in the cache.
            2. gRPC Call: if not in the cache, make a batch gRPC call and store the result in the cache.
    5. **Write Output Files to S3:**
        1. Add the inferred senioirty level to each job posting
        2. write the augmented data back to *s3://rl-data/job-postings-mod/*
4. Efficiency Considerations
    1. Processing Time for a single JSONL File
        1. Reading from S3 and writing to S3: These are I/O-bound operations and are generally fast.
        2. Cache Lookup: Redis can handle around 100,000 reads/writes per second per core, meaning lookups are near-instantaneous.
        3. gRPC Calls: Each batch can handle 1000 requests per second. Given the high deduplication rate, we expect to stay within this limit.
    3. Processing Time for a Day's Worth of JSONL Files:
        1. With 8M lines per day and assuming a high deduplication rate (due to repeated (company, title) pairs), we estimate a few thousand unique pairs per day. This would result in a few seconds of gRPC processing time
        2. Cache access time remains negligible.
    4. Cache Read/Write Time:
        1. Reads and writes to Redis are in the sub-millisecond range. Given a reasonable cache hit rate, the majority of time is spent on data I/O and batching logic
    5. CPU & Memory Footprint:
        1. Redis: Memory usage depends on the dataset size and the efficiency of storage (e.g., Redis data structures, eviction policies). For 20M entries, with average size and some overhead, this can be in the range of several gigabytes.
        2. Data Augmentation Service: The CPU footprint mainly comes from JSON parsing and batch management. With efficient coding (e.g., using asynchronous I/O and multiprocessing where possible), this can be kept low.

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
        4. Precompute and Cache Common Titles for Popular Companies
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
