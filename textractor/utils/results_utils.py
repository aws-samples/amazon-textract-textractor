import time
import boto3
import os
import json
import datetime
from textractcaller.t_call import get_s3_output_config_keys, OutputConfig, remove_none


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

def get_full_json_from_output_config(
    output_config: OutputConfig, job_id: str, s3_client=None
) -> dict:
    if not output_config or not job_id:
        raise ValueError("no output_config or job_id")
    if not output_config.s3_bucket or not output_config.s3_prefix:
        raise ValueError("no output_config or job_id")
    if not s3_client:
        s3_client = boto3.client("s3")

    result_value = dict()
    last_result = None
    parsed_keys = set()
    while last_result is None or (datetime.datetime.now().astimezone() - last_result).total_seconds() < 5:
        keys = get_s3_output_config_keys(
            output_config=output_config, job_id=job_id, s3_client=s3_client
        )
        for key in keys:
            if key in parsed_keys:
                continue
            parsed_keys.add(key)
            s3_object = s3_client.get_object(Bucket=output_config.s3_bucket, Key=key)
            if last_result is None:
                last_result = s3_object["LastModified"]
            else:
                last_result = max(last_result, s3_object["LastModified"])
            body = s3_object["Body"]
            body_read = body.read()
            body_decode = body_read.decode("utf-8")
            response = dict(json.loads(body_decode))
            if "Blocks" in result_value:
                result_value["Blocks"].extend(response["Blocks"])
            else:
                result_value = response
    result_value = remove_none(result_value)
    return result_value
