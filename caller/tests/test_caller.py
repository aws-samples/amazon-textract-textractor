from textractcaller import call_textract, call_textract_analyzeid, QueriesConfig, Query, AdaptersConfig, Adapter, get_full_json_from_output_config, get_full_json, call_textract_lending, get_full_json_lending
from textractcaller.t_call import OutputConfig, Textract_Features, call_textract_expense, remove_none
from trp import Document
import trp.trp2 as t2
import trp.trp2_analyzeid as t2id
import pytest
import logging
import os
import boto3
import json


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


def test_tiff_async_multipage_with_output_config(caplog):    #
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    textract_client = boto3.client('textract', region_name='us-east-2')
    input_file = os.path.join("s3://amazon-textract-public-content/blogs/multipage_tiff_example_small.tiff")
    output_config = OutputConfig(s3_bucket="sdx-objects-us-east-2", s3_prefix="test/outputconfig")
    print(output_config.get_dict())
    j = call_textract(input_document=input_file,
                      force_async_api=True,
                      output_config=output_config,
                      boto3_textract_client=textract_client,
                      return_job_id=True)
    print(j['JobId'])
    # this is just to wait for the job to finish
    get_full_json(job_id=j['JobId'], boto3_textract_client=textract_client)

    textract_json = get_full_json_from_output_config(output_config=output_config, job_id=j['JobId'])

    assert textract_json


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


def test_s3_sync_call(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    textract_client = boto3.client('textract', region_name='us-east-2')
    input_file = "s3://amazon-textract-public-content/blogs/amazon-textract-sample-text-amazon-dot-com.png"
    j = call_textract(input_document=input_file, boto3_textract_client=textract_client)
    assert j
    assert 'Blocks' in j
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
    assert len(j['IdentityDocuments'][0]['IdentityDocumentFields']) == 21
    doc: t2id.TAnalyzeIdDocument = t2id.TAnalyzeIdDocumentSchema().load(j)    #type: ignore
    assert doc

    # photo from local disk
    with open(input_file, "rb") as sample_file:
        b = bytearray(sample_file.read())
        j = call_textract_analyzeid(document_pages=[b])
        assert j
        assert 'DocumentMetadata' in j
        assert 'IdentityDocuments' in j
        assert 'IdentityDocumentFields' in j['IdentityDocuments'][0]
        assert len(j['IdentityDocuments'][0]['IdentityDocumentFields']) == 21
        doc: t2id.TAnalyzeIdDocument = t2id.TAnalyzeIdDocumentSchema().load(j)    #type: ignore
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
    tdoc: t2.TDocument = t2.TDocumentSchema().load(j)    #type: ignore
    assert tdoc
    page = tdoc.pages[0]
    query_answers = tdoc.get_query_answers(page=page)
    assert len(query_answers) == 3

def test_custom_queries(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    queries_config = QueriesConfig(queries=[])
    assert not queries_config.get_dict()
    query1 = Query(text="What is the applicant full name?")
    query2 = Query(text="What is the applicant phone number?", alias="PHONE_NUMBER")
    query3 = Query(text="What is the applicant home address?", alias="HOME_ADDRESS", pages=["1"])
    queries_config = QueriesConfig(queries=[query1, query2, query3])
    adapters_config = AdaptersConfig(adapters=[])
    assert not adapters_config.get_dict()
    adapter1 = Adapter(adapter_id="2e9bf1c4aa31", version="1", pages=["1"])
    adapters_config = AdaptersConfig(adapters=[adapter1])

    textract_client = boto3.client("textract", region_name="us-east-2")
    j = call_textract(
        input_document="s3://amazon-textract-public-content/blogs/employeeapp20210510.png",
        boto3_textract_client=textract_client,
        features=[Textract_Features.QUERIES],
        queries_config=queries_config,
        adapters_config=adapters_config
    )
    assert j
    tdoc: t2.TDocument = t2.TDocumentSchema().load(j)  # type: ignore
    assert tdoc
    page = tdoc.pages[0]
    query_answers = tdoc.get_query_answers(page=page)
    assert len(query_answers) == 3

def test_empty_features_and_queries(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    textract_client = boto3.client('textract', region_name='us-east-2')
    j = call_textract(input_document="s3://amazon-textract-public-content/blogs/employeeapp20210510.png",
                      boto3_textract_client=textract_client,
                      features=[])
    assert j


def test_expense_get_full_json_from_file_and_bytes(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR, "data/employmentapp.png")
    with open(input_file, "rb") as sample_file:
        b = bytearray(sample_file.read())
        j = call_textract_expense(input_document=b)
        assert j

    with open(input_file, "rb") as sample_file:
        b = sample_file.read()
        j = call_textract_expense(input_document=b)
        assert j


def test_expense_tiff_async(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    textract_client = boto3.client('textract', region_name='us-east-2')
    input_file = os.path.join("s3://amazon-textract-public-content/blogs/employmentapp_20210510_compressed.tiff")
    j = call_textract_expense(input_document=input_file, force_async_api=True, boto3_textract_client=textract_client)
    assert j
    assert 'ExpenseDocuments' in j


def test_expense_tiff_async_multipage(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    textract_client = boto3.client('textract', region_name='us-east-2')
    input_file = os.path.join("s3://amazon-textract-public-content/blogs/multipage_tiff_example_small.tiff")
    j = call_textract_expense(input_document=input_file, force_async_api=True, boto3_textract_client=textract_client)
    assert j
    assert 'ExpenseDocuments' in j


def test_filter_out_none_from_output_config(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR, "data/json_from_python_repl.json")
    j = dict(json.load(open(input_file)))
    assert j['Blocks'][0]["BlockType"] == "PAGE"
    assert j['Blocks'][0]["ColumnIndex"] == None
    j = remove_none(j)
    assert j
    assert 'Blocks' in j and j['Blocks'][0]["BlockType"] == "PAGE"
    assert not "ColumnIndex" in j['Blocks'][0]


def test_lending(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    input_file = "s3://sdx-textract-us-east-1/lending-package.pdf"
    textract_client = boto3.client('textract', region_name='us-east-1')
    j = call_textract_lending(input_document=input_file, boto3_textract_client=textract_client, return_job_id=True)
    assert j
    textract_json = get_full_json_lending(job_id=j['JobId'], boto3_textract_client=textract_client)
    assert textract_json


def test_signature(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    input_file = "s3://amazon-textract-public-content/blogs/signature/verification-of-employment.png"
    textract_client = boto3.client('textract', region_name='us-east-2')
    j = call_textract(input_document=input_file,
                      features=[Textract_Features.FORMS, Textract_Features.SIGNATURES],
                      boto3_textract_client=textract_client,
                      return_job_id=True)
    assert j


def test_layout(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    input_file = "s3://amazon-textract-public-content/blogs/signature/verification-of-employment.png"
    textract_client = boto3.client('textract', region_name='us-east-2')
    j = call_textract(input_document=input_file,
                      features=[Textract_Features.FORMS, Textract_Features.SIGNATURES, Textract_Features.LAYOUT],
                      boto3_textract_client=textract_client,
                      return_job_id=True)
    assert j

# def test_lending_output_config(caplog):
#     caplog.set_level(logging.DEBUG, logger="textractcaller")
#     input_file = "s3://sdx-textract-us-east-1/lending-package.pdf"
#     output_config = OutputConfig(s3_bucket="sdx-objects-us-east-1", s3_prefix="test/outputconfig")
#     textract_client = boto3.client('textract', region_name='us-east-1')
#     s3_client = boto3.client('s3', region_name='us-east-1')
#     j = call_textract_lending(input_document=input_file,
#                               boto3_textract_client=textract_client,
#                               output_config=output_config,
#                               return_job_id=True)
#     assert j
#     # this is just to wait till objects are in S3
#     textract_json = get_full_json_lending(job_id=j['JobId'], boto3_textract_client=textract_client)

#     textract_json = get_full_json_lending_from_output_config(output_config=output_config,
#                                                              job_id=j['JobId'],
#                                                              s3_client=s3_client)
#     assert textract_json
#     json.dump(textract_json, open("lending-doc-output_from_output_config.json", "w"))
