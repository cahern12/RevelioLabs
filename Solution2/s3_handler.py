import boto3
import json

class S3Handler:
    def __init__(self, bucket_raw, bucket_mod):
        self.bucket_raw = bucket_raw
        self.bucket_mod = bucket_mod
        self.s3_client = boto3.client("s3")

    def get_files_from_s3(self):
        """Retrieve the list of files from the specified S3 bucket."""
        response = self.s3_client.list_objects_v2(Bucket=self.bucket_raw)
        return [item["Key"] for item in response.get("Contents", [])]

    def read_jsonl_file(self, key):
        """Read a JSONL file from S3 and return the content as a list of dictionaries."""
        response = self.s3_client.get_object(Bucket=self.bucket_raw, Key=key)
        lines = response["Body"].read().decode("utf-8").splitlines()
        return [json.loads(line) for line in lines]

    def write_jsonl_file(self, key, data):
        """Write a list of dictionaries as a JSONL file to S3."""
        jsonl_data = "\n".join(json.dumps(record) for record in data)
        self.s3_client.put_object(Bucket=self.bucket_mod, Key=key, Body=jsonl_data.encode("utf-8"))
