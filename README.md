# RevelioLabs

## Solution #1 & 2 Updates
1. I refactored the solutions below into multiple files / classes:
    1. **S3Handler**: Handles all S3-related operations, such as reading & writing to S3
    2. **CacheHandler**: Manages Redis caching operations
    3. **GRPCClient**: Encapsulates all gRPC related operations
    4. **JobProcessor**: Orchestrates the job processing workflow, including reading files, deduplication, interacting with the cache, making gRPC calls, and writing results.
    5. **main.py**: The entry point of initializing all components and coordinating the processing of files using multithreading

## Solution #1
The goal of this solution is to implement 2 services (cacheing & data augmentation) to decrease the amount of gRPC calls. This redis layer helps aid in the implementation of this. For a full breakdown, please view the solution #1 directory.

## Solution #2
The goal of this solution is to decrease the amount of hits we have going through gRPC and Redise. The following is a high level implementation of what I did.
  1. Create batch processing across multiple files within a specified time domain (for example, all files within the last hour).
  2. Implemented Preemptive cacheing with Bloom filters. Bloom filters sit in front of the redis cache.
  3. Precompute and cache common titles for popular companies.

For a full list of implementation details, please view the solution #2 directory.
