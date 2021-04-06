from textractcaller.t_call import Textract_Features, Textract_Types
from textractcaller.t_call import call_textract
from textractoverlayer.t_overlay import get_bounding_boxes
from textractcaller.t_call import call_textract
from textractoverlayer.image_tools import get_size_from_document


def test_pretty_with_tables():
    input_document = "s3://sdx-textract-us-east-1/w2-example.png"
    features = [Textract_Features.FORMS, Textract_Features.TABLES]
    response = call_textract(input_document=input_document, features=features)
    assert response
    document_dimensions = get_size_from_document(input_document=input_document)
    bounding_boxes_all = get_bounding_boxes(
        textract_json=response,
        document_dimensions=document_dimensions,
        overlay_features=[Textract_Types.FORM, Textract_Types.WORD, Textract_Types.TABLE])
    print(len(bounding_boxes_all))
    assert len(bounding_boxes_all) > 0
    bounding_boxes_word = get_bounding_boxes(textract_json=response,
                                             document_dimensions=document_dimensions,
                                             overlay_features=[Textract_Types.WORD])
    print(len(bounding_boxes_word))
    assert len(bounding_boxes_word) > 0

    bounding_boxes_table = get_bounding_boxes(textract_json=response,
                                              document_dimensions=document_dimensions,
                                              overlay_features=[Textract_Types.TABLE])
    print(len(bounding_boxes_table))
    print(bounding_boxes_table)
    assert len(bounding_boxes_table) == 2

    bounding_boxes_form = get_bounding_boxes(textract_json=response,
                                             document_dimensions=document_dimensions,
                                             overlay_features=[Textract_Types.FORM])
    print(len(bounding_boxes_form))
    assert len(bounding_boxes_form) > 0
