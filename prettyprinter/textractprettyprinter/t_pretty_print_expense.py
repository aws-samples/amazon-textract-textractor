"""
Author: dhawalkp@amazon.com
Pretty printer for Amazon Textract AnalyzeExpense Response

Call the method as shown in below example to pretty print the AnalyzeExpense Response -

print(get_string(textract_json=data,output_type=[Textract_Expense_Pretty_Print.SUMMARY,Textract_Expense_Pretty_Print.LINEITEMGROUPS],
table_format=Pretty_Print_Table_Format.fancy_grid))

Arguments:
    textract_json: Python Dictionary Object containing the AnalyzeExpense Response
    output_type: Select the specific components for output for pretty printing. Valid values are SUMMARY and LINEITEMGROUPS.
        SUMMARY: To get the Summary Fields (key value pairs) in the Expense document
        LINEITEMGROUPS: To get the LineItemGroups in the Expense document.
    table_format: Type of Formating for pretty printing. Valid values are below
        "csv", "plain" ,"simple" ,"github" ,"grid" ,"fancy_grid" ,"pipe" ,"orgtbl" ,"jira" ,"presto" ,"pretty" ,"psql" ,
        "rst" ,"mediawiki" ,"moinmoin" ,"youtrack" ,"html" ,"unsafehtml" ,"latex" ,"latex_raw" ,"latex_booktabs" ,
        "latex_longtable" ,"textile" ,"tsv"
"""
from typing import List, Optional
from enum import Enum
from io import StringIO
import csv
import logging
from trp import trp2_expense
from tabulate import tabulate





logger = logging.getLogger(__name__)

Textract_Expense_Pretty_Print = Enum('Textract_Expense_Pretty_Print',
                             ["SUMMARY", "LINEITEMGROUPS"],
                             start=0)
Pretty_Print_Table_Format = Enum('Pretty_Print_Table_Format', ["csv", "plain" ,"simple" ,"github" ,"grid" ,"fancy_grid" ,"pipe" ,"orgtbl" ,"jira" ,"presto" ,"pretty" ,"psql" ,"rst" ,"mediawiki" ,"moinmoin" ,"youtrack" ,"html" ,"unsafehtml" ,"latex" ,"latex_raw" ,"latex_booktabs" ,"latex_longtable" ,"textile" ,"tsv"])


def get_string(textract_json:dict,
               output_type: Optional[List[Textract_Expense_Pretty_Print]] = None,
               table_format: Pretty_Print_Table_Format=Pretty_Print_Table_Format.github):
    """
    Main method for the clients to call for pretty printing the AnalyzeExpense Response
    """
    result_value = ""

    for otype in output_type:
        if otype == Textract_Expense_Pretty_Print.SUMMARY:
            result_value += get_expensesummary_string(
                textract_json=textract_json, table_format=table_format)
        if otype == Textract_Expense_Pretty_Print.LINEITEMGROUPS:
            result_value += get_expenselineitemgroups_string(
                textract_json=textract_json, table_format=table_format)

    return result_value


def convert_expenselineitemgroup_to_list(trp_table: trp2_expense.TLineItemGroup,
                          skip_expense_row = True,
                          with_type: bool = False,
                          with_confidence: bool = False,
                          with_geo: bool = False) -> List:
    """
    convert_expenselineitemgroup_to_list method for converting the Expense LineItemGroups to List for Pretty Printing.
        Parameters:
            trp_table: The AnalyzeExpense Document LineItemGroup
            skip_expense_row: Boolean with Default value as True. AnalyzeExpense will also have additional Field Type
                in LineItemField with EXPENSE_ROW. Customer can use this field in case the Normalized Keys are not detected.
            with_type: Boolean with Default value as False. Set this to True if you want the Normalized Field Type to be
                included in the pretty print output.
            with_confidence: Boolean with Default value as False. Set this to True if you want the Confidence score to be
                included in the pretty print output.
            with_geo: Boolean with default value as False. Set this to True if you want the geometry info to be included
                in the pretty print output.
        Returns:
            List of all the Expense LineItems
    """
    rows_list = list()
    for _, row in enumerate(trp_table.lineitems):
        one_row = list()
        for _, cell in enumerate(row.lineitem_expensefields):
            if skip_expense_row and cell.ftype and cell.ftype.text == 'EXPENSE_ROW':
                continue
            add_text = ""
            if with_confidence:
                add_text = f"({cell.confidence:.1f})"
            if with_geo:
                add_text = f"({cell.geometry.boundingBox})"
            if with_type:
                add_text = f"({cell.ftype.text})"
            print_text = [cell.valuedetection.text + add_text]
            one_row = one_row + print_text
        rows_list.append(one_row)
    return rows_list



def convert_expensesummary_to_list(expensedocument: trp2_expense.TExpense,
                          with_confidence: bool = False,
                          with_geo: bool = False,
                          with_type: bool = True) -> List:
    """
    convert_expensesummary_to_list method for converting the Expense Summary to List for Pretty Printing.
    Arguments:
        expensedocument: The AnalyzeExpense Expense Document
        with_type: Boolean with Default value as False. Set this to True if you want the Normalized Field Type
            to be included in the pretty print output.
        with_confidence: Boolean with Default value as False. Set this to True if you want the Confidence score
            to be included in the pretty print output.
        with_geo: Boolean with default value as False. Set this to True if you want the geometry info to be included
            in the pretty print output.
    Returns:
        List of all the Expense Summary
    """
    rows_list = list()
    rows_list.append(["Key", "Value"])
    for field in expensedocument.summaryfields:
        t_key = ""
        t_value = ""
        if field.labeldetection:
            t_key = field.labeldetection.text
            if with_geo:
                t_key += f" ({field.labeldetection.geometry.boundingBox}) "
            if with_confidence:
                t_key += f" ({field.labeldetection.confidence:.1f}) "
            if with_type:
                t_key += f"({field.ftype.text})"
        else:
            if with_type:
                t_key += f"({field.ftype.text})"
        if field.valuedetection:
            t_value = field.valuedetection.text
            if with_geo:
                t_value += f" ({field.valuedetection.geometry.boundingBox}) "
            if with_confidence:
                t_value += f" ({field.valuedetection.confidence:.1f}) "
        rows_list.append([t_key, t_value])
    return rows_list

def get_expenselineitemgroups_string(textract_json: dict,
                      table_format: Pretty_Print_Table_Format = Pretty_Print_Table_Format.github,
                      with_confidence: bool = False,
                      skip_expense_row: bool = True,
                      with_type: bool = True,
                      with_geo: bool = False) -> str:
    """
    doc: Textract response in form of trp.Document (https://github.com/aws-samples/amazon-textract-response-parser/tree/master/src-python)
    table_format: uses tabulate to pretty print the tabels to ascii. See https://pypi.org/project/tabulate/ for a lsit of table format values
    with_confidence: output confidence scores as well
    with_geo: output geo information as well
    """
    logger.debug(f"table_format: {table_format}")
    doc = trp2_expense.TAnalyzeExpenseDocumentSchema().load(textract_json)
    result_value = ""
    if not table_format==Pretty_Print_Table_Format.csv:
        for document in doc.expenses_documents:
            for table in document.lineitemgroups:
                table_list = convert_expenselineitemgroup_to_list(
                    table,skip_expense_row=skip_expense_row, with_type=with_type,with_confidence=with_confidence, with_geo=with_geo)
                result_value += tabulate(table_list, tablefmt=table_format.name) + "\n\n"
    if table_format==Pretty_Print_Table_Format.csv:
        logger.debug(f"pretty print - csv")
        csv_output = StringIO()
        csv_writer = csv.writer(csv_output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for document in doc.expenses_documents:
            for table in document.lineitemgroups:
                table_list = convert_expenselineitemgroup_to_list(
                    table, skip_expense_row=skip_expense_row, with_type=with_type, with_confidence=with_confidence, with_geo=with_geo)
                csv_writer.writerows(table_list)
                csv_writer.writerow([])
        result_value = csv_output.getvalue()
    return result_value


def get_expensesummary_string(textract_json: dict,
                    table_format: Pretty_Print_Table_Format = Pretty_Print_Table_Format.github,
                    with_confidence: bool = False,
                    with_geo: bool = False,
                    with_type: bool = True) -> str:
    """
    returns string with key-values printed out in format: key: value
    """
    logger.debug(f"table_format: {table_format}")
    doc = trp2_expense.TAnalyzeExpenseDocumentSchema().load(textract_json)
    result_value = ""
    if not table_format==Pretty_Print_Table_Format.csv:
        for document in doc.expenses_documents:
            summaryfields_list = convert_expensesummary_to_list(
                document, with_confidence=with_confidence, with_geo=with_geo,with_type=with_type)
            result_value += tabulate(summaryfields_list, tablefmt=table_format.name) + "\n\n"
    if table_format==Pretty_Print_Table_Format.csv:
        logger.debug(f"pretty print - csv")
        csv_output = StringIO()
        csv_writer = csv.writer(csv_output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for document in doc.expenses_documents:
            summaryfields_list = convert_expensesummary_to_list(
                document, with_confidence=with_confidence, with_geo=with_geo,with_type=with_type)
            csv_writer.writerows(summaryfields_list)
        csv_writer.writerow([])
        result_value = csv_output.getvalue()
    return result_value


