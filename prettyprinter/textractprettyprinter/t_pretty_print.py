import trp
from typing import List, Optional
from tabulate import tabulate
from enum import Enum
import json

Textract_Pretty_Print = Enum('Textract_Pretty_Print',
                             ["WORDS", "LINES", "FORMS", "TABLES"],
                             start=0)


def get_string(textract_json_string: str,
               output_type: Optional[List[Textract_Pretty_Print]] = None):
    result_value = ""
    for t in output_type:
        if t == Textract_Pretty_Print.WORDS:
            result_value += get_words_string(
                textract_json_string=textract_json_string)
        if t == Textract_Pretty_Print.LINES:
            result_value += get_lines_string(
                textract_json_string=textract_json_string)
        if t == Textract_Pretty_Print.FORMS:
            result_value += get_forms_string(
                textract_json_string=textract_json_string)
        if t == Textract_Pretty_Print.TABLES:
            result_value += get_tables_string(
                textract_json_string=textract_json_string)
    return result_value


def convert_table_to_list(trp_table: trp.Table,
                          with_confidence: bool = False,
                          with_geo: bool = False) -> List:
    rows_list = list()
    for _, row in enumerate(trp_table.rows):
        one_row = list()
        for _, cell in enumerate(row.cells):
            add_text = ""
            if with_confidence:
                add_text = f"({cell.confidence:.1f})"
            if with_geo:
                add_text = f"({cell.geometry.boundingBox})"
            print_text = [cell.text + add_text]
            one_row = one_row + print_text
        rows_list.append(one_row)
    return rows_list


def get_tables_string(textract_json_string: str,
                      table_format: str = 'github',
                      with_confidence: bool = False,
                      with_geo: bool = False) -> str:
    """
    doc: Textract response in form of trp.Document (https://github.com/aws-samples/amazon-textract-response-parser/tree/master/src-python)
    table_format: uses tabulate to pretty print the tabels to ascii. See https://pypi.org/project/tabulate/ for a lsit of table format values
    with_confidence: output confidence scores as well
    with_geo: output geo information as well
    """
    doc = trp.Document(json.loads(textract_json_string))
    result_value = ""
    for page in doc.pages:
        for table in page.tables:
            result_value += tabulate(convert_table_to_list(
                table, with_confidence=with_confidence, with_geo=with_geo),
                                     tablefmt=table_format) + "\n\n"

    return result_value


def get_forms_string(textract_json_string: str,
                     with_confidence: bool = False,
                     with_geo: bool = False) -> str:
    """
    returns string with key-values printed out in format: key: value
    """
    doc = trp.Document(json.loads(textract_json_string))
    result_value = ""
    for page in doc.pages:
        for field in page.form.fields:
            t = ""
            if (field.key):
                t = field.key.text
                if with_geo:
                    t += f" ({field.key.geometry.boundingBox}) "
                if with_confidence:
                    t += f" ({field.key.confidence:.1f}) "
            if (field.value):
                t += ": " + field.value.text
                if with_geo:
                    t += f" ({field.value.geometry.boundingBox}) "
                if with_confidence:
                    t += f" ({field.value.confidence:.1f}) "
            result_value += t + "\n"
    return result_value


def get_lines_string(textract_json_string: str,
                     with_page_number: bool = False) -> str:
    """
    returns string with lines seperated by \n
    """
    doc = trp.Document(json.loads(textract_json_string))
    i = 0
    result_value = ""
    for page in doc.pages:
        if with_page_number:
            result_value += f"--------- page number: {i} - page ID: {page.id} --------------"
        for line in page.lines:
            result_value += f"{line.text}\n"
        i += 1
    return result_value


def get_words_string(textract_json_string: str,
                     with_page_number: bool = False) -> str:
    """
    returns string with words seperated by \n
    """
    doc = trp.Document(json.loads(textract_json_string))
    i = 0
    result_value = ""
    for page in doc.pages:
        if with_page_number:
            result_value += f"--------- page number: {i} - page ID: {page.id} --------------"
        for line in page.lines:
            for word in line.words:
                result_value += f"{word.text}\n"
        i += 1
    return result_value
