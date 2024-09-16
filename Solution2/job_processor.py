class JobProcessor:
    def __init__(self, s3_handler, cache_handler, grpc_client):
        self.s3_handler = s3_handler
        self.cache_handler = cache_handler
        self.grpc_client = grpc_client

    def aggregate_job_postings_from_files(self, files):
        """Aggregate all job postings from multiple JSONL files."""
        job_postings = []
        for file_key in files:
            job_postings.extend(self.s3_handler.read_jsonl_file(file_key))
        return job_postings

    def deduplicate_by_company_title(self, job_postings):
        """Deduplicate job postings by (company, title) pairs."""
        unique_pairs = {}
        for job in job_postings:
            pair_key = (job["company"], job["title"])
            if pair_key not in unique_pairs:
                unique_pairs[pair_key] = {"uuid": len(unique_pairs), "company": job["company"], "title": job["title"]}
        return unique_pairs

    def write_augmented_data_to_s3(self, job_postings, cached_pairs, inferred_seniorities, missing_pairs):
        """Write augmented job postings with inferred seniority levels back to S3."""
        output_data = []
        for job in job_postings:
            pair_key = (job["company"], job["title"])
            if pair_key in cached_pairs:
                job["seniority"] = cached_pairs[pair_key]
            elif pair_key in missing_pairs:
                job["seniority"] = inferred_seniorities[missing_pairs[pair_key]["uuid"]]
            output_data.append(job)

        output_key = "augmented_data.jsonl"
        self.s3_handler.write_jsonl_file(output_key, output_data)

    def process_files(self, files):
        """Process multiple JSONL files from S3 with optimized gRPC and caching strategy."""
        # Step 1: Aggregate all job postings from multiple files
        job_postings = self.aggregate_job_postings_from_files(files)

        # Step 2: Deduplicate entries across files by (company, title)
        unique_pairs = self.deduplicate_by_company_title(job_postings)

        # Step 3: Use a Bloom Filter to check probable cache existence
        probable_cached_pairs, missing_pairs = self.cache_handler.check_bloom_filter(unique_pairs)

        # Step 4: Batch Redis Lookup with MGET for probable cache hits
        cached_pairs, remaining_missing_pairs = self.cache_handler.batch_redis_lookup(probable_cached_pairs)

        # Step 5: Make batched gRPC calls for missing pairs and update the cache
        if remaining_missing_pairs:
            inferred_seniorities = self.grpc_client.infer_seniority(remaining_missing_pairs)
            self.cache_handler.update_cache_with_seniority(inferred_seniorities, remaining_missing_pairs)
        else:
            inferred_seniorities = {}

        # Step 6: Write augmented data back to S3
        self.write_augmented_data_to_s3(job_postings, cached_pairs, inferred_seniorities, missing_pairs)
