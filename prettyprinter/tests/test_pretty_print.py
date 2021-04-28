from textractcaller.t_call import Textract_Features
from textractcaller.t_call import call_textract
from textractprettyprinter.t_pretty_print import get_tables_string


def test_pretty_with_tables():
    features = [Textract_Features.FORMS, Textract_Features.TABLES]
    response = call_textract(input_document="s3://sdx-textract-us-east-1/w2-example.png", features=features)
    assert response
    tables_result = get_tables_string(textract_json=response)
    assert len(tables_result) > 0

    response = call_textract(input_document="s3://sdx-textract-us-east-1/textract-samples/employmentapp.png",
                             features=features)
    assert response
    tables_result = get_tables_string(textract_json=response)
    assert len(tables_result) > 0
