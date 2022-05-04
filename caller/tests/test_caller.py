from textractcaller import call_textract, call_textract_analyzeid, QueriesConfig, Query
from textractcaller.t_call import Textract_Features
from trp import Document
import trp.trp2 as t2
import trp.trp2_analyzeid as t2id
import pytest
import logging
import os
import boto3


def test_get_full_json_from_file_and_bytes(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR, "data/employmentapp.png")
    with open(input_file, "rb") as sample_file:
        b = bytearray(sample_file.read())
        j = call_textract(input_document=b)
        assert j
        doc = Document(j)
        assert doc

    with open(input_file, "rb") as sample_file:
        b = sample_file.read()
        j = call_textract(input_document=b)
        assert j
        doc = Document(j)
        assert doc


def test_tiff_sync(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR, "data/employmentapp.tiff")
    j = call_textract(input_document=input_file)
    assert j
    assert 'Blocks' in j
    assert len(j['Blocks']) == 103
    doc = Document(j)
    assert doc


def test_tiff_async(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    textract_client = boto3.client('textract', region_name='us-east-2')
    input_file = os.path.join("s3://amazon-textract-public-content/blogs/employmentapp_20210510_compressed.tiff")
    j = call_textract(input_document=input_file, force_async_api=True, boto3_textract_client=textract_client)
    assert j
    assert 'Blocks' in j
    assert len(j['Blocks']) == 103
    doc = Document(j)
    assert doc


def test_tiff_async_multipage(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    textract_client = boto3.client('textract', region_name='us-east-2')
    input_file = os.path.join("s3://amazon-textract-public-content/blogs/multipage_tiff_example_small.tiff")
    j = call_textract(input_document=input_file, force_async_api=True, boto3_textract_client=textract_client)
    assert j
    assert 'Blocks' in j
    assert len(j['Blocks']) == 260
    doc = Document(j)
    assert doc


# multipage not supported on sync
def test_tiff_sync_multipage(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    textract_client = boto3.client('textract', region_name='us-east-2')
    input_file = os.path.join("s3://amazon-textract-public-content/blogs/multipage_tiff_example_small.tiff")
    with pytest.raises(textract_client.exceptions.UnsupportedDocumentException):
        call_textract(input_document=input_file, boto3_textract_client=textract_client)


def test_tiff_compressed_sync(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR, "data/employmentapp.tiff")
    j = call_textract(input_document=input_file)
    assert j
    assert 'Blocks' in j
    assert len(j['Blocks']) == 103
    doc = Document(j)
    assert doc

    with open(input_file, "rb") as sample_file:
        b = bytearray(sample_file.read())
        j = call_textract(input_document=b)
        assert j
        assert 'Blocks' in j
        assert len(j['Blocks']) == 103
        doc = Document(j)
        assert doc


def test_analyzeid(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR, "data/driverlicense.png")

    # photo from S3
    textract_client = boto3.client('textract', region_name='us-east-2')
    j = call_textract_analyzeid(document_pages=["s3://amazon-textract-public-content/analyzeid/driverlicense.png"],
                                boto3_textract_client=textract_client)
    assert j
    assert 'DocumentMetadata' in j
    assert 'IdentityDocuments' in j
    assert 'IdentityDocumentFields' in j['IdentityDocuments'][0]
    assert len(j['IdentityDocuments'][0]['IdentityDocumentFields']) == 20
    doc: t2id.TAnalyzeIdDocument = t2id.TAnalyzeIdDocumentSchema().load(j)
    assert doc

    # photo from local disk
    with open(input_file, "rb") as sample_file:
        b = bytearray(sample_file.read())
        j = call_textract_analyzeid(document_pages=[b])
        assert j
        assert 'DocumentMetadata' in j
        assert 'IdentityDocuments' in j
        assert 'IdentityDocumentFields' in j['IdentityDocuments'][0]
        assert len(j['IdentityDocuments'][0]['IdentityDocumentFields']) == 20
        doc: t2id.TAnalyzeIdDocument = t2id.TAnalyzeIdDocumentSchema().load(j)
        assert doc


def test_queries(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    queries_config = QueriesConfig(queries=[])
    assert not queries_config.get_dict()
    query1 = Query(text="What is the applicant full name?")
    query2 = Query(text="What is the applicant phone number?", alias="PHONE_NUMBER")
    query3 = Query(text="What is the applicant home address?", alias="HOME_ADDRESS", pages=["1"])
    queries_config = QueriesConfig(queries=[query1, query2, query3])

    textract_client = boto3.client('textract', region_name='us-east-2')
    j = call_textract(input_document="s3://amazon-textract-public-content/blogs/employeeapp20210510.png",
                      boto3_textract_client=textract_client,
                      features=[Textract_Features.QUERIES],
                      queries_config=queries_config)
    assert j
    tdoc = t2.TDocumentSchema().load(j)
    assert tdoc
    page = tdoc.pages[0]
    query_answers = tdoc.get_query_answers(page=page)
    assert len(query_answers) == 3
