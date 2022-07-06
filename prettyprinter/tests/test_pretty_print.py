from textractcaller.t_call import Textract_Features
from textractcaller.t_call import call_textract
from trp.trp2 import TDocumentSchema
from textractprettyprinter.t_pretty_print import convert_form_to_list_trp2, convert_queries_to_list_trp2, get_tables_string
import boto3
import os
import json


def test_pretty_with_tables():
    features = [Textract_Features.FORMS, Textract_Features.TABLES]
    textract_client = boto3.client('textract', region_name='us-east-2')

    response = call_textract(input_document="s3://amazon-textract-public-content/blogs/w2-example.png",
                             features=features,
                             boto3_textract_client=textract_client)
    assert response
    tables_result = get_tables_string(textract_json=response)
    assert len(tables_result) > 0

    response = call_textract(input_document="s3://amazon-textract-public-content/blogs/employmentapp.png",
                             features=features,
                             boto3_textract_client=textract_client)
    assert response
    tables_result = get_tables_string(textract_json=response)
    assert len(tables_result) > 0


def test_pretty_with_forms_and_trp2():

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/multi_page_example_file.json")
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        trp2_doc = TDocumentSchema().load(json.load(input_fp))
        assert trp2_doc
        forms_as_list = convert_form_to_list_trp2(trp2_doc=trp2_doc)    #type: ignore
        print(forms_as_list)
        assert len(forms_as_list) == 2
        assert len(forms_as_list[0]) == 30
        assert len(forms_as_list[1]) == 4


def test_pretty_with_queries_and_trp2():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/analyzeDocResponse.json")
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        trp2_doc = TDocumentSchema().load(json.load(input_fp))
        assert trp2_doc
        queries_as_list = convert_queries_to_list_trp2(trp2_doc=trp2_doc)    #type: ignore
        assert len(queries_as_list) == 1
        assert len(queries_as_list[0]) == 3
