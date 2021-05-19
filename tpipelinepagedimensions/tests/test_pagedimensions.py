import os
from textractpagedimensions.t_pagedimensions import add_page_dimensions
from textractcaller.t_call import call_textract
from trp.trp2 import TDocument, TDocumentSchema
import json


def test_dimensions_from_file():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR,
                              "data/Textract-orginal-2021-05-10.png")
    j = call_textract(input_document=input_file)
    t_document: TDocument = TDocumentSchema().load(j)
    add_page_dimensions(t_document=t_document, input_document=input_file)
    assert t_document.pages[0].custom['PageDimension'] == {
        'doc_width': 1544,
        'doc_height': 1065
    }


def test_dimensions_from_bytes():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(SCRIPT_DIR,
                              "data/Textract-orginal-2021-05-10.png")
    with open(input_file, 'rb') as input_document_file:
        input_document = input_document_file.read()
        j = call_textract(input_document=input_document)
        with open("output.json", 'w') as outfilebla:
            json.dump(obj=j, fp=outfilebla)
        t_document: TDocument = TDocumentSchema().load(j)

    with open(input_file, 'rb') as input_document_file:
        add_page_dimensions(t_document=t_document,
                            input_document=input_document_file.read())
        assert t_document.pages[0].custom['PageDimension'] == {
            'doc_width': 1544,
            'doc_height': 1065
        }
