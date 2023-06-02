import trp
from trp.trp2 import TBlock, TBoundingBox, TDocument, TGeometry, TPoint
from trp.trp2_analyzeid import TIdentityDocument
from trp.trp2_expense import TExpense
import trp.trp2_lending as tl
from typing import List, Optional
from tabulate import tabulate
from enum import Enum
from io import StringIO
import csv
import logging
import statistics

logger = logging.getLogger(__name__)


class Textract_Pretty_Print(Enum):
    WORDS = 1
    LINES = 2
    FORMS = 3
    TABLES = 4


class Pretty_Print_Table_Format(Enum):
    csv = 1
    plain = 2
    simple = 3
    github = 4
    grid = 5
    fancy_grid = 6
    pipe = 7
    orgtbl = 8
    jira = 9
    presto = 10
    pretty = 11
    psql = 12
    rst = 13
    mediawiki = 14
    moinmoin = 15
    youtrack = 16
    html = 17
    unsafehtml = 18
    latex = 19
    latex_raw = 20
    latex_booktabs = 21
    latex_longtable = 22
    textile = 23
    tsv = 24


def get_string(textract_json: dict,
               output_type: Optional[List[Textract_Pretty_Print]] = [Textract_Pretty_Print.WORDS],
               table_format: Pretty_Print_Table_Format = Pretty_Print_Table_Format.github,
               with_confidence: bool = False,
               with_geo: bool = False,
               with_page_number: bool = False,
               trim: bool = False):
    """Main function to call depending on output_type the parameters for with_confidence, with_geo, with_page_number are considered."""
    result_value = ""
    if output_type:
        for t in output_type:
            if t == Textract_Pretty_Print.WORDS:
                result_value += get_words_string(textract_json=textract_json,
                                                 with_page_number=with_page_number,
                                                 with_confidence=with_confidence,
                                                 trim=trim)
            if t == Textract_Pretty_Print.LINES:
                result_value += get_lines_string(textract_json=textract_json,
                                                 with_page_number=with_page_number,
                                                 with_confidence=with_confidence,
                                                 trim=trim)
            if t == Textract_Pretty_Print.FORMS:
                result_value += get_forms_string(textract_json=textract_json,
                                                 table_format=table_format,
                                                 with_confidence=with_confidence,
                                                 with_geo=with_geo,
                                                 trim=trim)
            if t == Textract_Pretty_Print.TABLES:
                result_value += get_tables_string(textract_json=textract_json,
                                                  table_format=table_format,
                                                  with_confidence=with_confidence,
                                                  with_geo=with_geo,
                                                  trim=trim)
    else:
        logger.error("output_type should be set otherwise not output")
    return result_value


def convert_table_to_list(trp_table: trp.Table,
                          with_confidence: bool = False,
                          with_geo: bool = False,
                          trim: bool = False) -> List:
    rows_list = list()
    for _, row in enumerate(trp_table.rows):
        one_row = list()
        for _, cell in enumerate(row.cells):
            add_text = ""
            if with_confidence:
                add_text = f"({cell.confidence:.1f})"
            if with_geo:
                add_text = f"({cell.geometry.boundingBox})"
            if trim:
                print_text = [cell.text.strip() + add_text]
            else:
                print_text = [cell.text + add_text]
            one_row = one_row + print_text
        rows_list.append(one_row)
    return rows_list


def convert_form_to_list_trp2(trp2_doc: TDocument, ) -> List[List[List[str]]]:
    '''return List[List[List[str]]]
    With the first List being the Page and the second the list of form fields
    page_number, key_name, key_confidence, value_name, value_confidence, key-bounding-box.top, key-bounding-box.height, k-bb.width, k-bb.left, value-bounding-box.top, v-bb.height, v-bb.width, v-bb.left
    '''
    page_list: List[List[List[str]]] = list()
    for idx, page_block in enumerate(trp2_doc.pages):
        page_keys: List[List[str]] = list()
        for key_block in trp2_doc.keys(page=page_block):
            key_child_relationships = key_block.get_relationships_for_type()
            if key_child_relationships:
                key_blocks = trp2_doc.get_blocks_for_relationships(relationship=key_child_relationships)
                key_name = trp2_doc.get_text_for_tblocks(key_blocks)
                key_geometry = TDocument.create_geometry_from_blocks(key_blocks)
                value_blocks = trp2_doc.value_for_key(key=key_block)
                key_confidence = statistics.mean([x.confidence for x in key_blocks if x.confidence])
                if value_blocks:
                    key_value = trp2_doc.get_text_for_tblocks(value_blocks)
                    value_geometry = TDocument.create_geometry_from_blocks(value_blocks)
                    value_confidence = statistics.mean([x.confidence for x in value_blocks if x.confidence])
                else:
                    # no value for key
                    key_value = ""
                    value_geometry = TGeometry(TBoundingBox(width=0, height=0, top=0, left=0), polygon=[TPoint(0, 0)])
                    value_confidence = 1
                page_keys.append([
                    str(idx + 1), key_name,
                    str(key_confidence), key_value,
                    str(value_confidence),
                    str(key_geometry.bounding_box.top) if key_geometry and key_geometry.bounding_box else "0",
                    str(key_geometry.bounding_box.height) if key_geometry and key_geometry.bounding_box else "0",
                    str(key_geometry.bounding_box.width) if key_geometry and key_geometry.bounding_box else "0",
                    str(key_geometry.bounding_box.left) if key_geometry and key_geometry.bounding_box else "0",
                    str(value_geometry.bounding_box.top) if value_geometry and value_geometry.bounding_box else "0",
                    str(value_geometry.bounding_box.height) if value_geometry and value_geometry.bounding_box else "0",
                    str(value_geometry.bounding_box.width) if value_geometry and value_geometry.bounding_box else "0",
                    str(value_geometry.bounding_box.left) if value_geometry and value_geometry.bounding_box else "0"
                ])
        page_list.append(page_keys)
    return page_list


def convert_queries_to_list_trp2(trp2_doc: TDocument) -> List[List[List[str]]]:
    '''return List[List[List[str]]]
    With the first List being the Page and the second the list of [page_number, alias (if exists, otherwise query), value]
    page_number, key_name, value_name, key-bounding-box.top, key-bounding-box.height, k-bb.width, k-bb.left, value-bounding-box.top, v-bb.height, v-bb.width, v-bb.left
    '''
    page_list: List[List[List[str]]] = list()
    for idx, page_block in enumerate(trp2_doc.pages):
        page_keys: List[List[str]] = list()
        for query in trp2_doc.queries(page=page_block):
            if query.query.alias:
                key = query.query.alias
            else:
                key = query.query.text
            answer_blocks: List[TBlock] = [x for x in trp2_doc.get_answers_for_query(block=query)]
            if answer_blocks:
                for answer in answer_blocks:
                    value_geometry = TDocument.create_geometry_from_blocks([answer])
                    page_keys.append([
                        str(idx + 1), key, "1", answer.text,
                        str(answer.confidence), "0", "0", "0", "0",
                        str(value_geometry.bounding_box.top) if value_geometry and value_geometry.bounding_box else "0",
                        str(value_geometry.bounding_box.height)
                        if value_geometry and value_geometry.bounding_box else "0",
                        str(value_geometry.bounding_box.width)
                        if value_geometry and value_geometry.bounding_box else "0",
                        str(value_geometry.bounding_box.left) if value_geometry and value_geometry.bounding_box else "0"
                    ])
            else:
                # no answer found
                page_keys.append([str(idx + 1), key, "1", "", "1", "0", "0", "0", "0", "0", "0", "0", "0 "])
        page_list.append(page_keys)
    return page_list


def convert_signatures_to_list_trp2(trp2_doc: TDocument) -> List[List[List[str]]]:
    '''return List[List[List[str]]]
    With the first List being the Page and the second the list of [page_number, alias (if exists, otherwise query), key_confidence, value, key-bounding-box.top, key-bounding-box.height, k-bb.width, k-bb.left, value-bounding-box.top, v-bb.height, v-bb.width, v-bb.left
    '''
    page_list: List[List[List[str]]] = list()
    for idx, page_block in enumerate(trp2_doc.pages):
        page_signatures: List[List[str]] = list()
        for signature in trp2_doc.signatures(page=page_block):
            value_geometry = TDocument.create_geometry_from_blocks([signature])
            page_signatures.append([
                str(idx + 1), "SIGNATURE", "1", "exists",
                str(signature.confidence), "0", "0", "0", "0",
                str(value_geometry.bounding_box.top) if value_geometry and value_geometry.bounding_box else "0",
                str(value_geometry.bounding_box.height) if value_geometry and value_geometry.bounding_box else "0",
                str(value_geometry.bounding_box.width) if value_geometry and value_geometry.bounding_box else "0",
                str(value_geometry.bounding_box.left) if value_geometry and value_geometry.bounding_box else "0"
            ])
        page_list.append(page_signatures)
    return page_list


def convert_form_to_list(trp_form: trp.Form,
                         with_confidence: bool = False,
                         with_geo: bool = False,
                         trim: bool = False) -> List:
    rows_list = list()
    rows_list.append(["Key", "Value"])
    for field in trp_form.fields:
        t_key = ""
        t_value = ""
        if field.key:
            if trim:
                t_key = field.key.text.strip()
            else:
                t_key = field.key.text
            if with_geo:
                t_key += f" ({field.key.geometry.boundingBox}) "
            if with_confidence:
                t_key += f" ({field.key.confidence:.1f}) "
        if field.value:
            if trim:
                t_value = field.value.text.strip()
            else:
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
                      with_geo: bool = False,
                      trim: bool = False) -> str:
    """
    doc: Textract response in form of trp.Document (https://github.com/aws-samples/amazon-textract-response-parser/tree/master/src-python)
    table_format: uses tabulate to pretty print the tables to ascii. See https://pypi.org/project/tabulate/ for a list of table format values
    with_confidence: output confidence scores as well
    with_geo: output geo information as well
    trim: removes whitespace from text
    """
    logger.debug(f"table_format: {table_format}")
    doc = trp.Document(textract_json)
    result_value = ""
    if not table_format == Pretty_Print_Table_Format.csv:
        for page in doc.pages:
            for table in page.tables:
                table_list = convert_table_to_list(table, with_confidence=with_confidence, with_geo=with_geo, trim=trim)
                result_value += (tabulate(table_list, tablefmt=table_format.name) + "\n\n")
    if table_format == Pretty_Print_Table_Format.csv:
        logger.debug(f"pretty print - csv")
        csv_output = StringIO()
        csv_writer = csv.writer(csv_output, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for page in doc.pages:
            for table in page.tables:
                table_list = convert_table_to_list(table, with_confidence=with_confidence, with_geo=with_geo, trim=trim)
                csv_writer.writerows(table_list)
                csv_writer.writerow([])
        result_value = csv_output.getvalue()
    return result_value


def get_forms_string(textract_json: dict,
                     table_format: Pretty_Print_Table_Format = Pretty_Print_Table_Format.github,
                     with_confidence: bool = False,
                     with_geo: bool = False,
                     trim: bool = False) -> str:
    """
    returns string with key-values printed out in format: key: value
    """
    logger.debug(f"table_format: {table_format}")
    doc = trp.Document(textract_json)
    result_value = ""
    if not table_format == Pretty_Print_Table_Format.csv:
        for page in doc.pages:
            forms_list = convert_form_to_list(page.form, with_confidence=with_confidence, with_geo=with_geo, trim=trim)
            result_value += tabulate(forms_list, tablefmt=table_format.name) + "\n\n"
    if table_format == Pretty_Print_Table_Format.csv:
        logger.debug(f"pretty print - csv")
        csv_output = StringIO()
        csv_writer = csv.writer(csv_output, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for page in doc.pages:
            forms_list = convert_form_to_list(page.form, with_confidence=with_confidence, with_geo=with_geo, trim=trim)
            csv_writer.writerows(forms_list)
        csv_writer.writerow([])
        result_value = csv_output.getvalue()
    return result_value


def get_lines_string(textract_json: dict,
                     with_page_number: bool = False,
                     with_confidence=False,
                     trim: bool = False) -> str:
    """
    returns string with lines separated by \n
    """
    doc = trp.Document(textract_json)
    i = 0
    result_value = ""
    for page in doc.pages:
        if with_page_number:
            result_value += (f"--------- page number: {i} - page ID: {page.id} --------------")
        for line in page.lines:
            if trim:
                result_value += f"{line.text.strip()}\n"
            else:
                result_value += f"{line.text}\n"

            if with_confidence:
                result_value += f", {line.confidence}"
        i += 1
    return result_value


def get_words_string(textract_json: dict,
                     with_page_number: bool = False,
                     with_confidence=False,
                     trim: bool = False) -> str:
    """
    returns string with words separated by \n
    """
    doc = trp.Document(textract_json)
    i = 0
    result_value = ""
    for page in doc.pages:
        if with_page_number:
            result_value += (f"--------- page number: {i} - page ID: {page.id} --------------")
        for line in page.lines:
            for word in line.words:
                if trim:
                    result_value += f"{word.text.strip()}\n"
                else:
                    result_value += f"{word.text}\n"

                if with_confidence:
                    result_value += f", {word.confidence}"
                result_value += "\n"
        i += 1
    return result_value


def convert_geometry_from_trp2(geometry: TGeometry) -> List[str]:
    """Converts a TGeometry object to strings [top, height, width, left]
    if any value is None or empty, will be set to 0
    """
    return [
        str(geometry.bounding_box.top if geometry and geometry.bounding_box else str(0)),
        str(geometry.bounding_box.height if geometry and geometry.bounding_box else str(0)),
        str(geometry.bounding_box.width if geometry and geometry.bounding_box else str(0)),
        str(geometry.bounding_box.left if geometry and geometry.bounding_box else str(0)),
    ]


def convert_lending_document_from_trp2(trp2_lending: tl.TLendingDocument) -> List[List[str]]:
    """
    returns: a list of ['key-name', 'confidence-score-for-key-name', 'value', 'confidence-score-for-value', key-bounding-box.top, key-bounding-box.height, k-bb.width, k-bb.left, value-bounding-box.top, v-bb.height, v-bb.width, v-bb.left]
    """
    lending_document_value_list: List[List[str]] = list()
    if not trp2_lending:
        return lending_document_value_list

    if trp2_lending:
        # Iterate through all lending fields
        for lending_field in trp2_lending.lending_fields:
            # type OTHER means we could not map to a normalized key and used the key from FORMS
            if lending_field.field_type != 'OTHER':
                if lending_field.value_detections:
                    for value_detection in lending_field.value_detections:
                        value_text = value_detection.selection_status if value_detection.selection_status else value_detection.text
                        lending_document_value_list.append([
                            lending_field.field_type, "1", value_text,
                            str(value_detection.confidence), "0", "0", "0", "0"
                        ] + convert_geometry_from_trp2(value_detection.geometry))
                else:
                    # no values detected, set all float to 0 and confidence to 1
                    lending_document_value_list.append(
                        [lending_field.field_type, "1", "", "1", "0", "0", "0", "0", "0", "0", "0", "0"])
            else:
                # OTHER has key detections, so need those
                if lending_field.value_detections:
                    for value_detection in lending_field.value_detections:
                        value_text = value_detection.selection_status if value_detection.selection_status else value_detection.text

                        lending_document_value_list.append([
                            lending_field.key_detection.text,
                            str(lending_field.key_detection.confidence), value_text,
                            str(value_detection.confidence)
                        ] + convert_geometry_from_trp2(lending_field.key_detection.geometry) +
                                                           convert_geometry_from_trp2(value_detection.geometry))
                else:
                    # no value detections, so just add the key
                    lending_document_value_list.append([
                        lending_field.key_detection.text,
                        str(lending_field.key_detection.confidence), "", "1",
                        str(lending_field.key_detection.geometry.bounding_box.top),
                        str(lending_field.key_detection.geometry.bounding_box.height),
                        str(lending_field.key_detection.geometry.bounding_box.width),
                        str(lending_field.key_detection.geometry.bounding_box.left), "0", "0", "0", "0"
                    ])

        for signature in trp2_lending.signature_detections:
            lending_document_value_list.append([
                "SIGNATURE",
                "1",
                "SIGNATURE_PRESENT",
                str(signature.confidence),
                "0",
                "0",
                "0",
                "0",
                str(signature.geometry.bounding_box.
                    top if signature and signature.geometry and signature.geometry.bounding_box else str(0)),
                str(signature.geometry.bounding_box.
                    height if signature and signature.geometry and signature.geometry.bounding_box else str(0)),
                str(signature.geometry.bounding_box.
                    width if signature and signature.geometry and signature.geometry.bounding_box else str(0)),
                str(signature.geometry.bounding_box.
                    left if signature and signature.geometry and signature.geometry.bounding_box else str(0)),
            ])
    return lending_document_value_list


def convert_expense_from_trp2(trp2_expense: TExpense) -> List[List[str]]:
    """
    returns: a list of ['key-name', 'confidence-score-for-key-name', 'value', 'confidence-score-for-value', key-bounding-box.top, key-bounding-box.height, k-bb.width, k-bb.left, value-bounding-box.top, v-bb.height, v-bb.width, v-bb.left]
    If there is a Type, use that text as the first part of the key
    If there is a LabelDetection, append that text to the key
    If there is a GroupProperty with a GroupType, prepend that to the key
    If there is a currency, add it to the value?
    """
    if not trp2_expense:
        return list()
    expense_value_list: List[List[str]] = list()
    for summary_field in trp2_expense.summaryfields:
        key_text: str = ""
        key_confidence_list: List[float] = list()
        key_geometry: TGeometry = None    #type: ignore
        value_text: str = ""
        value_confidence_list: List[float] = list()
        value_geometry: TGeometry = None    #type: ignore
        if summary_field.ftype:
            if summary_field.ftype.text:
                key_text = summary_field.ftype.text
            if summary_field.ftype.confidence:
                key_confidence_list.append(summary_field.ftype.confidence)
        if summary_field.group_properties and summary_field.group_properties[0].types:
            #just take the first one if there is a group_property
            key_text = summary_field.group_properties[0].types[0] + "_" + key_text

        if summary_field.labeldetection:
            if summary_field.labeldetection.text:
                key_text = summary_field.labeldetection.text + "_" + key_text
            if summary_field.labeldetection.confidence:
                key_confidence_list.append(summary_field.ftype.confidence)
            if summary_field.labeldetection.geometry:
                key_geometry = summary_field.labeldetection.geometry

        if summary_field.valuedetection:
            if summary_field.valuedetection.geometry:
                value_geometry = summary_field.valuedetection.geometry
            if summary_field.valuedetection.text:
                value_text = summary_field.valuedetection.text
            if summary_field.valuedetection.confidence:
                value_confidence_list.append(summary_field.valuedetection.confidence)

        expense_value_list.append(
            [key_text,
             statistics.mean(key_confidence_list), value_text,
             statistics.mean(value_confidence_list)] + convert_geometry_from_trp2(key_geometry) +
            convert_geometry_from_trp2(value_geometry))
    return expense_value_list


def convert_identity_from_trp2(trp2_identity: TIdentityDocument) -> List[List[str]]:
    """
    returns: a list of ['key-name', 'confidence-score-for-key-name', 'value', 'confidence-score-for-value', key-bounding-box.top, key-bounding-box.height, k-bb.width, k-bb.left, value-bounding-box.top, v-bb.height, v-bb.width, v-bb.left]
    Will not have entries for normalized values
    """
    if not trp2_identity:
        return list()
    identity_value_list: List[List[str]] = list()
    for field in trp2_identity.identity_document_fields:
        identity_value_list.append([
            field.type.text if field.type else "",
            str(1), field.value_detection.text if field.value_detection else "",
            str(field.value_detection.confidence) if field.value_detection.confidence else "", "0", "0", "0", "0", "0",
            "0", "0", "0"
        ])
    return identity_value_list


def convert_lending_from_trp2(trp2_doc: tl.TFullLendingDocument) -> List[List[str]]:
    '''return List[List[str]]
    With the first List being the Page and the second the list of
    [{page_classification}_{page_number_within_document_type}, page_number_in_document, key, key_confidence, value, value_confidence, key-bounding-box.top, key-bounding-box.height, key-bb.width, key-bb.left, value-bounding-box.top, value-bb.height, value-bb.width, value-bb.left]
    '''
    page_list: List[List[str]] = list()
    for idx, page_result in enumerate(trp2_doc.lending_results):
        page_classification_max: tl.TPrediction = max(page_result.page_classification.page_type,
                                                      key=lambda x: x.confidence)
        page_number_max: tl.TPrediction = max(page_result.page_classification.page_number, key=lambda x: x.confidence)

        for extraction in page_result.extractions:
            for lending_detection in convert_lending_document_from_trp2(extraction.lending_document):
                logger.debug(f"lending: {lending_detection}")
                page_list.append([f"{page_classification_max.value}_{page_number_max.value}",
                                  str(idx + 1)] + lending_detection)

            for expense_detection in convert_expense_from_trp2(extraction.expense_document):
                page_list.append([f"{page_classification_max.value}_{page_number_max.value}",
                                  str(idx + 1)] + expense_detection)
            for identity_detection in convert_identity_from_trp2(extraction.identity_document):
                page_list.append([f"{page_classification_max.value}_{page_number_max.value}",
                                  str(idx + 1)] + identity_detection)
    return page_list
