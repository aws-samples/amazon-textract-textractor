from typing import Union, Tuple
from io import BytesIO
from PIL import Image

from textractor.exceptions import InputError


def s3_path_to_bucket_and_prefix(s3_path: str) -> Tuple[str, str]:
    """Converts an S3 URI to a bucket and prefix

    :param s3_path: S3 URI
    :type s3_path: str
    :raises InputError: Raised if the given path cannot be parsed
    :return: Tuple of bucket and prefix as string
    :rtype: Tuple[str, str]
    """
    try:
        bucket, prefix = s3_path.replace("s3://", "").split("/", 1)
    except IndexError:
        raise InputError(f"Could not parse {s3_path} as ")
    return bucket, prefix


def download_from_s3(client, s3_path: str, **extra_args):
    """Downloads a file from S3 and returns it as a BytesIO object

    :param client: S3 client
    :type client: Client
    :param s3_path: S3 path to download
    :type s3_path: str
    :return: S3 file as a BytesIO object
    :rtype: BytesIO
    """

    bucket, prefix = s3_path_to_bucket_and_prefix(s3_path)

    f = BytesIO()
    client.download_fileobj(bucket, prefix, f)
    return f


def upload_to_s3(
    client, s3_path: str, file_source: Union[str, bytes, Image.Image], **extra_args
):
    """Upload a file to S3

    :param client: boto3 client
    :type client: Client
    :param s3_path: S3 path to upload to
    :type s3_path: str
    :param file_source: File to upload
    :type file_source: Union[str, bytes, Image.Image]
    :raises InputError: Raised if the file_source is not of type str, bytes or Image
    """
    bucket, prefix = s3_path_to_bucket_and_prefix(s3_path)
    if isinstance(file_source, Image.Image):
        fake_file = BytesIO()
        file_source.save(fake_file, format="PNG")
        fake_file.seek(0)
        client.upload_fileobj(fake_file, bucket, prefix, extra_args)
    elif isinstance(file_source, bytes):
        fake_file = BytesIO(file_source)
        client.upload_fileobj(fake_file, bucket, prefix, extra_args)
    elif isinstance(file_source, str):
        client.upload_file(file_source, bucket, prefix, extra_args)
    else:
        raise InputError(
            f"{file_source} must be of type str or bytes, not {type(file_source)}"
        )


def delete_from_s3(client, s3_path: str):
    """Delete a file from S3

    :param client: boto3 client
    :type client: Client
    :param s3_path: S3 path to the object to delete
    :type s3_path: str
    """
    bucket, prefix = s3_path_to_bucket_and_prefix(s3_path)

    client.delete_object(bucket, prefix)
