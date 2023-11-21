import boto3
import os


def results_exist(job_id: str, s3_bucket: str, s3_prefix: str, s3_client=None) -> bool:
    if not s3_client:
        s3_client = boto3.client("s3")
    response = s3_client.list_objects(
        Bucket=s3_bucket,
        Prefix=os.path.join(s3_prefix, job_id + "/"),
        Delimiter="/",
        MaxKeys=2,
    )
    # The directory will have at least one file because of the S3 access check
    return "Contents" in response and len(response["Contents"]) > 1
