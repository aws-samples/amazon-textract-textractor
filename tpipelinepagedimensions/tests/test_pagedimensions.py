import os
import boto3
import logging

from typing import List
from textractpagedimensions.t_pagedimensions import add_page_dimensions
from textractcaller.t_call import call_textract
from trp.trp2 import TDocument, TDocumentSchema, TBlock


def test_dimensions_from_file():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR, "data/Textract-orginal-2021-05-10.png")
    j = call_textract(input_document=input_file)
    t_document: TDocument = TDocumentSchema().load(j)
    add_page_dimensions(t_document=t_document, input_document=input_file)
    assert t_document.pages[0].custom['PageDimension'] == {'doc_width': 1544, 'doc_height': 1065}


def test_dimensions_from_tiff(caplog):
    caplog.set_level(logging.DEBUG, logger="textractcaller")
    textract_client = boto3.client('textract', region_name='us-east-2')
    input_file = "s3://amazon-textract-public-content/blogs/multipage_tiff_example_small.tiff"
    j = call_textract(input_document=input_file, force_async_api=True, boto3_textract_client=textract_client)
    t_document: TDocument = TDocumentSchema().load(j)
    add_page_dimensions(t_document=t_document, input_document=input_file)
    assert t_document.pages[0].custom['PageDimension'] == {'doc_width': 1333.0, 'doc_height': 1000.0}
    assert t_document.pages[1].custom['PageDimension'] == {'doc_width': 1362.0, 'doc_height': 1038.0}


def test_s3():
    textract_client = boto3.client('textract', region_name='us-east-2')
    input_file = "s3://amazon-textract-public-content/blogs/2-pager-different-dimensions.pdf"
    j = call_textract(input_document=input_file, boto3_textract_client=textract_client)
    t_document: TDocument = TDocumentSchema().load(j)
    add_page_dimensions(t_document=t_document, input_document=input_file)
    pages: List[TBlock] = t_document.pages
    pages[0].custom['PageDimension'] == {'doc_width': 1549.0, 'doc_height': 370.0}
    pages[1].custom['PageDimension'] == {'doc_width': 1079.0, 'doc_height': 505.0}


def test_dimensions_from_bytes():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR, "data/Textract-orginal-2021-05-10.png")
    with open(input_file, 'rb') as input_document_file:
        input_document = input_document_file.read()
        j = call_textract(input_document=input_document)
        # with open("output.json", 'w') as outfilebla:
        #     json.dump(obj=j, fp=outfilebla)
        t_document: TDocument = TDocumentSchema().load(j)

    with open(input_file, 'rb') as input_document_file:
        add_page_dimensions(t_document=t_document, input_document=input_document_file.read())
        assert t_document.pages[0].custom['PageDimension'] == {'doc_width': 1544, 'doc_height': 1065}
