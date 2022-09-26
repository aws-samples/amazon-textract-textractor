import inspect
import json
import os

def get_fixture_path():
    """Uses reflection to get correct saved response file

    :return: Path to the saved response file for the calling function
    :rtype: str
    """
    return os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        f"fixtures/saved_api_responses/{inspect.currentframe().f_back.f_code.co_name}.json"
    )

def save_document_to_fixture_path(document):
    with open(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            f"fixtures/saved_api_responses/{inspect.currentframe().f_back.f_code.co_name}.json"
        ),
        "w"
    ) as f:
        json.dump(document.response, f)