import io
import os
import sys
from textractoverlayer.t_overlay import DocumentDimensions
import boto3

# Conditionally add /opt to the PYTHON PATH
if os.getenv('AWS_EXECUTION_ENV') is not None:
    sys.path.append('/opt')

from PIL import Image
from PyPDF2 import PdfReader

pdf_suffixes = ['.pdf']
image_suffixes = ['.png', '.jpg', '.jpeg']
supported_suffixes = pdf_suffixes + image_suffixes


def get_size_from_filestream(fs, ext) -> DocumentDimensions:
    if ext in image_suffixes:
        img = Image.open(fs)
        return DocumentDimensions(doc_width=img.width, doc_height=img.height)
    else:
        input1 = PdfReader(fs)
        pdf_page = input1.pages[0].mediabox
        return DocumentDimensions(doc_width=int(pdf_page[2]), doc_height=int(pdf_page[3]))


def get_size_from_s3(s3_bucket, s3_key) -> DocumentDimensions:
    _, ext = os.path.splitext(s3_key)
    if ext in supported_suffixes:
        s3 = boto3.client('s3')
        o = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        input_bytes = o.get('Body').read()
        f = io.BytesIO(input_bytes)
        return get_size_from_filestream(f, ext)
    else:
        raise ValueError(f'{s3_key} not in {supported_suffixes}')


def get_filename_from_document(input_document: str):
    file_name = ''
    if len(input_document) > 7 and input_document.lower().startswith('s3://'):
        input_document = input_document.replace('s3://', '')
        _, s3_key = input_document.split('/', 1)
        file_name, suffix = os.path.splitext(os.path.basename(s3_key))
    else:
        file_name, suffix = os.path.splitext(os.path.basename(input_document))
    return file_name, suffix


def get_size_from_document(input_document: str) -> DocumentDimensions:
    if len(input_document) > 7 and input_document.lower().startswith('s3://'):
        input_document = input_document.replace('s3://', '')
        s3_bucket, s3_key = input_document.split('/', 1)
        return get_size_from_s3(s3_bucket=s3_bucket, s3_key=s3_key)
    else:
        return get_size_from_document(input_document)


def get_width_height_from_s3_object(s3_bucket, s3_key) -> DocumentDimensions:
    return get_size_from_s3(s3_bucket, s3_key)


def get_width_height_from_file(filepath) -> DocumentDimensions:
    _, ext = os.path.splitext(filepath)
    if ext in supported_suffixes:
        with open(filepath, 'rb') as input_fs:
            return get_size_from_filestream(input_fs, ext)
    else:
        raise ValueError(f'{filepath} not in {supported_suffixes}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', required=True)
    parser.add_argument('--s3-key', required=True)
    args = parser.parse_args()
    s3_bucket = args.s3_bucket
    s3_key = args.s3_key

    print(get_width_height_from_s3_object(s3_bucket, s3_key))
