from concurrent.futures import ThreadPoolExecutor, as_completed
from s3_handler import S3Handler
from cache_handler import CacheHandler
from grpc_client import GRPCClient
from job_processor import JobProcessor

def main():
    # Configuration
    S3_BUCKET_RAW = "rl-data/job-postings-raw"
    S3_BUCKET_MOD = "rl-data/job-postings-mod"
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    GRPC_SERVER = "localhost:50051"
    BLOOM_CAPACITY = 1000000
    BLOOM_ERROR_RATE = 0.001

    # Initialize handlers and client
    s3_handler = S3Handler(S3_BUCKET_RAW, S3_BUCKET_MOD)
    cache_handler = CacheHandler(REDIS_HOST, REDIS_PORT, BLOOM_CAPACITY, BLOOM_ERROR_RATE)
    grpc_client = GRPCClient(GRPC_SERVER)

    # Initialize Job Processor
    job_processor = JobProcessor(s3_handler, cache_handler, grpc_client)

    # Get files to process
    files_to_process = s3_handler.get_files_from_s3()

    # Process files in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(job_processor.process_files, [file_key]) for file_key in files_to_process]
        for future in as_completed(futures):
            future.result()

if __name__ == "__main__":
    main()
