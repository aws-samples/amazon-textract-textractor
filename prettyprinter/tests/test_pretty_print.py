from textractcaller.t_call import Textract_Features
from textractcaller.t_call import call_textract
from textractprettyprinter.t_pretty_print import get_tables_string
import boto3


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
