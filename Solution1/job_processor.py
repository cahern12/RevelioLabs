from s3_handler import S3Handler
from cache_handler import CacheHandler
from grpc_client import GRPCClient

class JobProcessor:
    def __init__(self, s3_handler, cache_handler, grpc_client):
        self.s3_handler = s3_handler
        self.cache_handler = cache_handler
        self.grpc_client = grpc_client

    def process_file(self, file_key):
        """Process a single JSONL file from S3."""
        job_postings = self.s3_handler.read_jsonl_file(file_key)

        # Deduplicate by (company, title) pair
        unique_pairs = {}
        for job in job_postings:
            pair_key = (job["company"], job["title"])
            if pair_key not in unique_pairs:
                unique_pairs[pair_key] = {"uuid": len(unique_pairs), "company": job["company"], "title": job["title"]}

        # Check cache and prepare gRPC requests for missing pairs
        grpc_requests = []
        for (company, title), request in unique_pairs.items():
            seniority = self.cache_handler.get_seniority_from_cache(company, title)
            if seniority is None:
                grpc_requests.append(request)
            else:
                unique_pairs[(company, title)]["seniority"] = int(seniority)

        # Make gRPC calls for uncached pairs
        if grpc_requests:
            inferred_seniority = self.grpc_client.infer_seniority_batch(grpc_requests)
            for request in grpc_requests:
                seniority = inferred_seniority[request["uuid"]]
                self.cache_handler.set_seniority_in_cache(request["company"], request["title"], seniority)
                unique_pairs[(request["company"], request["title"])]["seniority"] = seniority

        # Write augmented data to S3
        output_data = []
        for job in job_postings:
            seniority = unique_pairs[(job["company"], job["title"])]["seniority"]
            job["seniority"] = seniority
            output_data.append(job)

        output_key = file_key.replace("job-postings-raw", "job-postings-mod")
        self.s3_handler.write_jsonl_file(output_key, output_data)
