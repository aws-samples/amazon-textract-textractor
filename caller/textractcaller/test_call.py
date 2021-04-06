from textractcaller.t_call import OutputConfig, Textract_Features
import pytest
from textractcaller.t_call import call_textract
from trp import Document
import json


def test_call_with_local_file():
    with pytest.raises(Exception):
        call_textract(input_document="/Users/schadem/code/aws/Textract-signature-demo/images/small-2x2-image.png",
                      force_async_api=True)
    response = call_textract(
        input_document="/Users/schadem/code/aws/Textract-signature-demo/images/small-2x2-image.png")
    assert response
    features = [Textract_Features.TABLES]
    response = call_textract(
        input_document="/Users/schadem/code/aws/Textract-signature-demo/images/small-2x2-image.png", features=features)
    assert response
    features = [Textract_Features.FORMS]
    response = call_textract(
        input_document="/Users/schadem/code/aws/Textract-signature-demo/images/small-2x2-image.png", features=features)
    assert response
    features = [Textract_Features.FORMS, Textract_Features.TABLES]
    response = call_textract(
        input_document="/Users/schadem/code/aws/Textract-signature-demo/images/small-2x2-image.png", features=features)
    assert response


def test_call_with_pdf_from_s3():
    response = call_textract(input_document="s3://sdx-textract-us-east-1/w2-example.pdf", force_async_api=True)
    assert response
    features = [Textract_Features.FORMS, Textract_Features.TABLES]
    response = call_textract(input_document="s3://sdx-textract-us-east-1/w2-example.pdf",
                             features=features,
                             force_async_api=True)
    assert response


def test_call_with_pdf_from_s3_with_just_return_job_id():
    response = call_textract(input_document="s3://sdx-textract-us-east-1/w2-example.pdf",
                             force_async_api=True,
                             return_job_id=True)
    print(response)
    assert len(response) == 64


def test_call_with_img_from_s3():
    response = call_textract(input_document="s3://sdx-textract-us-east-1/w2-example.png", force_async_api=True)
    assert response
    response = call_textract(input_document="s3://sdx-textract-us-east-1/w2-example.png")
    assert response


def test_call_with_png_from_s3_kmskeyid():
    response = call_textract(input_document="s3://sdx-textract-encrypted/small-2x2-image.png",
                             force_async_api=True,
                             kms_key_id="arn:aws:kms:us-east-1:913165245630:key/98799a1f-4021-4121-8605-53dbe60d8b3f",
                             return_job_id=False)

    d = Document(json.loads(response))
    assert d


def test_call_with_png_from_s3_kmskeyid_and_output_config():
    output_config = OutputConfig(s3_bucket="sdx-textract-encrypted", s3_prefix="output/")
    response = call_textract(input_document="s3://sdx-textract-encrypted/small-2x2-image.png",
                             force_async_api=True,
                             output_config=output_config,
                             kms_key_id="arn:aws:kms:us-east-1:913165245630:key/98799a1f-4021-4121-8605-53dbe60d8b3f",
                             return_job_id=False)

    d = Document(json.loads(response))
    assert d


def test_call_with_png_from_s3_kmskeyid_and_output_config_and_job_tag_and_client_request():
    output_config = OutputConfig(s3_bucket="sdx-textract-encrypted", s3_prefix="output/")
    response = call_textract(input_document="s3://sdx-textract-encrypted/small-2x2-image.png",
                             force_async_api=True,
                             output_config=output_config,
                             kms_key_id="arn:aws:kms:us-east-1:913165245630:key/98799a1f-4021-4121-8605-53dbe60d8b3f",
                             return_job_id=False,
                             job_tag="sometag",
                             client_request_token="sometoken")

    d = Document(json.loads(response))
    assert d
