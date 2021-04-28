import trp
from typing import List, Optional
from tabulate import tabulate
from enum import Enum
from io import StringIO
import csv
import logging

logger = logging.getLogger(__name__)

Textract_Pretty_Print = Enum('Textract_Pretty_Print',
                             ["WORDS", "LINES", "FORMS", "TABLES"],
                             start=0)
Pretty_Print_Table_Format = Enum('Pretty_Print_Table_Format', ["csv", "plain" ,"simple" ,"github" ,"grid" ,"fancy_grid" ,"pipe" ,"orgtbl" ,"jira" ,"presto" ,"pretty" ,"psql" ,"rst" ,"mediawiki" ,"moinmoin" ,"youtrack" ,"html" ,"unsafehtml" ,"latex" ,"latex_raw" ,"latex_booktabs" ,"latex_longtable" ,"textile" ,"tsv"])

def get_string(textract_json:dict,
               output_type: Optional[List[Textract_Pretty_Print]] = None,
               table_format: Pretty_Print_Table_Format=Pretty_Print_Table_Format.github):
    result_value = ""
    for t in output_type:
        if t == Textract_Pretty_Print.WORDS:
            result_value += get_words_string(
                textract_json=textract_json)
        if t == Textract_Pretty_Print.LINES:
            result_value += get_lines_string(
                textract_json=textract_json)
        if t == Textract_Pretty_Print.FORMS:
            result_value += get_forms_string(
                textract_json=textract_json, table_format=table_format)
        if t == Textract_Pretty_Print.TABLES:
            result_value += get_tables_string(
                textract_json=textract_json, table_format=table_format)
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

def convert_form_to_list(trp_form: trp.Form,
                          with_confidence: bool = False,
                          with_geo: bool = False) -> List:
    rows_list = list()
    rows_list.append(["Key", "Value"])
    for field in trp_form.fields:
        t_key = ""
        t_value = ""
        if (field.key):
            t_key = field.key.text
            if with_geo:
                t_key += f" ({field.key.geometry.boundingBox}) "
            if with_confidence:
                t_key += f" ({field.key.confidence:.1f}) "
        if (field.value):
            t_value = field.value.text
            if with_geo:
                t_value += f" ({field.value.geometry.boundingBox}) "
            if with_confidence:
                t_value += f" ({field.value.confidence:.1f}) "
        rows_list.append([t_key, t_value])
    return rows_list

def get_tables_string(textract_json: dict,
                      table_format: Pretty_Print_Table_Format = Pretty_Print_Table_Format.github,
                      with_confidence: bool = False,
                      with_geo: bool = False) -> str:
    """
    doc: Textract response in form of trp.Document (https://github.com/aws-samples/amazon-textract-response-parser/tree/master/src-python)
    table_format: uses tabulate to pretty print the tabels to ascii. See https://pypi.org/project/tabulate/ for a lsit of table format values
    with_confidence: output confidence scores as well
    with_geo: output geo information as well
    """
    logger.debug(f"table_format: {table_format}")
    doc = trp.Document(textract_json)
    result_value = ""
    if not table_format==Pretty_Print_Table_Format.csv:
        for page in doc.pages:
            for table in page.tables:
                table_list = convert_table_to_list(
                    table, with_confidence=with_confidence, with_geo=with_geo)
                result_value += tabulate(table_list, tablefmt=table_format.name) + "\n\n"
    if table_format==Pretty_Print_Table_Format.csv:
        logger.debug(f"pretty print - csv")
        csv_output = StringIO()
        csv_writer = csv.writer(csv_output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for page in doc.pages:
            for table in page.tables:
                table_list = convert_table_to_list(
                    table, with_confidence=with_confidence, with_geo=with_geo)
                csv_writer.writerows(table_list)
                csv_writer.writerow([])
        result_value = csv_output.getvalue()
    return result_value


def get_forms_string(textract_json: dict,
                    table_format: Pretty_Print_Table_Format = Pretty_Print_Table_Format.github,
                    with_confidence: bool = False,
                    with_geo: bool = False) -> str:
    """
    returns string with key-values printed out in format: key: value
    """
    logger.debug(f"table_format: {table_format}")
    doc = trp.Document(textract_json)
    result_value = ""
    if not table_format==Pretty_Print_Table_Format.csv:
        for page in doc.pages:
            forms_list = convert_form_to_list(
                page.form, with_confidence=with_confidence, with_geo=with_geo)
            result_value += tabulate(forms_list, tablefmt=table_format.name) + "\n\n"
    if table_format==Pretty_Print_Table_Format.csv:
        logger.debug(f"pretty print - csv")
        csv_output = StringIO()
        csv_writer = csv.writer(csv_output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for page in doc.pages:
            forms_list = convert_form_to_list(
                page.form, with_confidence=with_confidence, with_geo=with_geo)
            csv_writer.writerows(forms_list)
        csv_writer.writerow([])
        result_value = csv_output.getvalue()
    return result_value


def get_lines_string(textract_json: dict,
                     with_page_number: bool = False) -> str:
    """
    returns string with lines seperated by \n
    """
    doc = trp.Document(textract_json)
    i = 0
    result_value = ""
    for page in doc.pages:
        if with_page_number:
            result_value += f"--------- page number: {i} - page ID: {page.id} --------------"
        for line in page.lines:
            result_value += f"{line.text}\n"
        i += 1
    return result_value


def get_words_string(textract_json:dict,
                     with_page_number: bool = False) -> str:
    """
    returns string with words seperated by \n
    """
    doc = trp.Document(textract_json)
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
