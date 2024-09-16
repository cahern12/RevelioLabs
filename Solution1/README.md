# Solution 1

## Solution #1
To design an efficient data augmentation service for inferring seniority levels from job postings, the primarily goal is to minimize the number of costly gRPC calls to the Revelio Labs seniority model while ensuring timely process of the JSONL files. Here is a breakdown of the proposed solution
1. **Overview of the Solution**
    1. Cacheing Service: This service will cache the results of seniority inferences to avoid redundant gRPC calls for the same (company, title) pairs. The cache should be highly performant, scalable, and able to handle billions of entries efficiently
    2. Data Augmentation Service: This service will read the JSONL files from the S3 bucket, use the caching service to check if a seniority level is already available for a given (company, title) pair, make gRPC calls when necessary, and write the output with seniority information back to another S3 bucket.
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
```
Key: hash("Revelio Labs|Senior Data Engineer - Data Flow")
Value: 3
```
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
