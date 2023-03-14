"""
Consumes Textract JSON response and converts them to a Document object format.
This class contains all the necessary utilities to create entity objects from JSON blocks within the response.
Use ResponseParser's parse function to handle API response and convert them to Document objects.
"""

import logging
import uuid
from typing import Any, List, Dict, Tuple
from collections import defaultdict
from textractor.entities.identity_document import IdentityDocument
from textractor.entities.expense_document import ExpenseDocument
from textractor.entities.expense_field import Expense, ExpenseField, ExpenseType, \
    ExpenseGroupProperty, LineItemGroup, LineItemRow

from textractor.entities.page import Page
from textractor.entities.query_result import QueryResult
from textractor.entities.signature import Signature
from textractor.entities.word import Word
from textractor.entities.line import Line
from textractor.entities.value import Value
from textractor.entities.table import Table
from textractor.entities.bbox import BoundingBox
from textractor.entities.document import Document
from textractor.entities.key_value import KeyValue
from textractor.entities.table_cell import TableCell
from textractor.entities.query import Query
from textractor.validate.validation import validate_entity_schema
from textractor.entities.document_entity import DocumentEntity
from textractor.entities.selection_element import SelectionElement
from textractor.data.constants import (
    SelectionStatus,
    TextTypes,
    HANDWRITING,
    PRINTED,
)
from textractor.data.constants import (
    WORD,
    LINE,
    KEY_VALUE_SET,
    CELL,
    TABLE,
    SELECTION_ELEMENT,
    PAGE,
    MERGED_CELL,
    QUERY,
    SIGNATURE,
)


def _create_document_object(response: dict) -> Document:
    """
    Consumes API Response in JSON format and creates a Document object.

    :param response: json response from Textract API
    :type response: dict

    :return: Returns a Document object populated with metadata on number of pages.
    :rtype: Document
    """
    doc = Document(num_pages=response["DocumentMetadata"]["Pages"])
    return doc


def _filter_block_type(response: dict, entity: str) -> List[Dict[str, Any]]:
    """
    Consumes entire JSON response, filters and returns list of blocks corresponding to the entity
    parameter from API response JSON.

    :param response: JSON response from Textract API
    :type response: dict
    :param entity: Entity to be extracted from the JSON response
    :type entity: str

    :return: Returns a list of JSON blocks that match entity parameter.
    :rtype: List
    """
    return [block for block in response["Blocks"] if block["BlockType"] == entity]


def _filter_by_entity(
    block_json: List[Dict[str, Any]], entity_type: str
) -> Dict[str, Any]:
    """
    Filters and returns dictionary of blocks corresponding to the entity_type from API response JSON.

    :param block_json: list of blocks belonging to a specific entity
    :type block_json: List[Dict[str, Any]]
    :param entity_type: EntityType used to select/filter from list of blocks
    :type entity_type: str

    :return: Dictionary mapping of block ID with JSON block for entity type.
    :rtype: Dict[str, Any]
    """
    return {
        block["Id"]: block
        for block in block_json
        if block["EntityTypes"][0] == entity_type
    }


def _get_relationship_ids(block_json: Dict[str, Any], relationship: str) -> List[str]:
    """
    Takes the JSON block corresponding to an entity and returns the Ids of the chosen Relationship if the Relationship exists.

    :param block_json: JSON block corresponding to an entity
    :type block_json: List[Dict[str, Any]]
    :relationship: CHILD or VALUE as input
    :type relationship: str

    :return: List of IDs with type Relationship to entity
    :rtype: List
    """
    ids = []
    try:
        ids = [
            rel["Ids"]
            for rel in block_json["Relationships"]
            if rel["Type"] == relationship
        ][0]
    except:
        logging.info(
            f"{block_json['BlockType']} - {block_json['Id']} does not have ids with {relationship} relationship."
        )
    return ids


def _create_page_objects(
    response: dict,
) -> Tuple[Dict[str, Page], List[Dict[str, Any]]]:
    """
    Consumes API Response in JSON format and returns Page objects for the Document.

    :param response: JSON response from Textract API
    :type response: dict

    :return: Returns dictionary with page ID - Page object mapping,  list of JSON blocks belonging to PAGE blocks.
    :rtype: Dict[str, Page], List[str]
    """
    pages = []
    page_elements = _filter_block_type(response, entity=PAGE)

    for page_json in page_elements:
        asset_id = page_json["Id"]
        width = page_json["Geometry"]["BoundingBox"]["Width"]
        height = page_json["Geometry"]["BoundingBox"]["Height"]
        page_num = page_json["Page"] if len(page_elements) > 1 else 1
        page_children = _get_relationship_ids(page_json, relationship="CHILD")
        page = Page(
            id=asset_id,
            width=width,
            height=height,
            page_num=page_num,
            child_ids=page_children,
        )
        pages.append(page)
    pages = {page.id: page for page in pages}
    return pages, page_elements


def _create_word_objects(
    word_ids: List[str], id_json_map: Dict[str, str], page: Page
) -> List[Word]:
    """
    Creates list of Word objects for all word_ids passed to the function.

    :param word_ids: List of ids corresponding to the words present within Page.
    :type word_ids: list
    :param id_json_map: Dictionary containing entity_id: JSON block mapping.
    :type id_json_map: dict
    :param page: Instance of parent Page object.
    :type page: Page

    :return: Returns a list of Word objects for the IDs passed in word_ids.
    :rtype: list
    """
    word_elements = []

    for word_id in word_ids:
        validate_entity_schema(id_json_map[word_id], entity=WORD)
        word_elements.append(id_json_map[word_id])

    text_type = {PRINTED: TextTypes.PRINTED, HANDWRITING: TextTypes.HANDWRITING}

    words = []
    for elem in word_elements:
        word = Word(
            entity_id=elem["Id"],
            bbox=BoundingBox.from_normalized_dict(
                elem["Geometry"]["BoundingBox"], spatial_object=page
            ),
            text=elem.get("Text"),
            text_type=text_type[elem.get("TextType")],
            confidence=elem["Confidence"],
        )
        word.raw_object = elem
        words.append(word)

    for word in words:
        word.page = page.page_num
        word.page_id = page.id

    return words


def _create_line_objects(
    line_ids: List[str], id_json_map: Dict[str, str], page: Page
) -> Tuple[List[Line], List[Word]]:
    """
    Creates list of Line objects for all lines in the Page derived from the API JSON response.

    :param line_ids: List of IDs corresponding to the lines present within Page.
    :type line_ids: list
    :param id_json_map: Dictionary containing entity_id: JSON block mapping.
    :type id_json_map: dict
    :param page: Instance of parent Page object.
    :type page: Page

    :return: Returns a list of Line objects for the IDs passed in line_ids and list of Word objects
             belonging to the corresponding Line objects.
    :rtype: List[Line], List[Word]
    """
    page_lines = []

    for line_id in line_ids:
        if line_id in page.child_ids:
            validate_entity_schema(id_json_map[line_id], entity=LINE)
            page_lines.append(id_json_map[line_id])

    lines = []
    page_words = []
    for line in page_lines:
        if _get_relationship_ids(line, relationship="CHILD"):
            line_words = _create_word_objects(
                _get_relationship_ids(line, relationship="CHILD"),
                id_json_map,
                page,
            )
            page_words.extend(line_words)
            lines.append(
                Line(
                    entity_id=line["Id"],
                    bbox=BoundingBox.from_normalized_dict(
                        line["Geometry"]["BoundingBox"], spatial_object=page
                    ),
                    words=line_words,
                    confidence=line["Confidence"],
                )
            )
            lines[-1].raw_object = line

    for line in lines:
        line.page = page.page_num
        line.page_id = page.id

    return lines, page_words


def _create_selection_objects(
    selection_ids: List[str], id_json_map: Dict[str, Any], page: Page
) -> Dict[str, SelectionElement]:
    """
    Creates dictionary mapping of SelectionElement ID with SelectionElement objects for all ids passed in selection_ids.

    :param selection_ids: List of ids corresponding to the SelectionElements.
    :type selection_ids: list
    :param id_json_map: Dictionary containing entity_id: JSON block mapping.
    :type id_json_map: dict
    :param page: Instance of parent Page object.
    :type page: Page

    :return: Returns a dictionary mapping of SelectionElement IDs with SelectionElement objects for the IDs present in
             selection_ids.
    :rtype: Dict[str, SelectionElement]
    """
    checkbox_elements = [id_json_map[selection_id] for selection_id in selection_ids]
    for checkbox_info in checkbox_elements:
        validate_entity_schema(checkbox_info, entity=SELECTION_ELEMENT)

    status = {
        "SELECTED": SelectionStatus.SELECTED,
        "NOT_SELECTED": SelectionStatus.NOT_SELECTED,
    }

    checkboxes = {}
    for block in checkbox_elements:
        checkboxes[block["Id"]] = SelectionElement(
            entity_id=block["Id"],
            bbox=BoundingBox.from_normalized_dict(
                block["Geometry"]["BoundingBox"], spatial_object=page
            ),
            status=status[block["SelectionStatus"]],
            confidence=block["Confidence"],
        )
        checkboxes[block["Id"]].raw_object = block

    for c in checkboxes.values():
        c.page = page.page_num
        c.page_id = page.id

    return checkboxes


def _create_value_objects(
    value_ids: List[str],
    id_json_map: Dict[str, Any],
    entity_id_map: Dict[str, list],
    page: Page,
) -> Dict[str, Value]:
    """
    Creates dictionary containing Value objects for all value_ids in the Page derived from the API response JSON.

    :param value_ids: List of ids corresponding to the Values in the page.
    :type value_ids: list
    :param id_json_map: Dictionary containing entity_id:JSON block mapping.
    :type id_json_map: dict
    :param entity_id_map: Dictionary containing entity_type:List[entity_id] mapping.
    :type entity_id_map: dict
    :param page: Instance of parent Page object.
    :type page: Page

    :return: Dictionary mapping value_ids to Value objects.
    :rtype: Dict[str, Value]
    """
    values_info = {value_id: id_json_map[value_id] for value_id in value_ids}

    values = {}
    for block_id, block in values_info.items():
        values[block_id] = Value(
            entity_id=block_id,
            bbox=BoundingBox.from_normalized_dict(
                block["Geometry"]["BoundingBox"], spatial_object=page
            ),
            confidence=block["Confidence"],
        )
        values[block_id].raw_object = block

    checkboxes = _create_selection_objects(
        entity_id_map[SELECTION_ELEMENT], id_json_map, page
    )

    # Add children to Value object
    for val_id in values.keys():
        val_child_ids = _get_relationship_ids(values_info[val_id], relationship="CHILD")
        for child_id in val_child_ids:
            if id_json_map[child_id]["BlockType"] == WORD:
                values[val_id].words += _create_word_objects(
                    [child_id], id_json_map, page
                )
            elif id_json_map[child_id]["BlockType"] == SIGNATURE:
                continue
            else:
                checkbox = checkboxes[child_id]
                checkbox.value_id = val_id
                values[val_id].add_children([checkbox])
                values[val_id].contains_checkbox = True

            values[val_id].page = page.page_num
            values[val_id].page_id = page.id

    return values


def _create_query_objects(
    query_ids: List[str],
    id_json_map: Dict[str, str],
    entity_id_map: Dict[str, list],
    page: Page,
) -> List[Query]:
    page_queries = []
    for query_id in query_ids:
        if query_id in page.child_ids:
            validate_entity_schema(id_json_map[query_id], entity=QUERY)
            page_queries.append(id_json_map[query_id])

    query_result_id_map = {}
    for block in page_queries:
        answer = _get_relationship_ids(block, relationship="ANSWER")
        query_result_id_map[block["Id"]] = answer[0] if answer else None

    query_results = _create_query_result_objects(
        list(query_result_id_map.values()), id_json_map, entity_id_map, page
    )

    queries = []
    for query in page_queries:
        query_result = query_results.get(query_result_id_map[query["Id"]])
        query_obj = Query(
            query["Id"],
            query["Query"]["Text"],
            query["Query"].get("Alias"),
            query_result,
            query_result.bbox if query_result is not None else None,
        )
        query_obj.raw_object = query
        queries.append(query_obj)

    return queries


def _create_query_result_objects(
    query_result_ids: List[str],
    id_json_map: Dict[str, str],
    entity_id_map: Dict[str, list],
    page: Page,
) -> Dict[str, QueryResult]:
    page_query_results = []
    for query_result_id in query_result_ids:
        if query_result_id in page.child_ids:
            validate_entity_schema(id_json_map[query_result_id], entity=QueryResult)
            page_query_results.append(id_json_map[query_result_id])

    query_results = {}
    for block in page_query_results:
        query_results[block["Id"]] = QueryResult(
            entity_id=block["Id"],
            confidence=block["Confidence"],
            result_bbox=BoundingBox.from_normalized_dict(
                block["Geometry"]["BoundingBox"], spatial_object=page
            ),
            answer=block["Text"],
        )
        query_results[block["Id"]].raw_object = block

    for query_result_id, query_result in query_results.items():
        query_result.page = page.page_num
        query_result.page_id = page.id

    return query_results

def _create_signature_objects(
    signature_ids: List[str],
    id_json_map: Dict[str, str],
    entity_id_map: Dict[str, list],
    page: Page,
) -> Dict[str, Signature]:
    page_signatures = []
    for signature_id in signature_ids:
        if signature_id in page.child_ids:
            validate_entity_schema(id_json_map[signature_id], entity=Signature)
            page_signatures.append(id_json_map[signature_id])

    signatures = {}
    for block in page_signatures:
        signatures[block["Id"]] = Signature(
            entity_id=block["Id"],
            confidence=block["Confidence"],
            bbox=BoundingBox.from_normalized_dict(
                block["Geometry"]["BoundingBox"], spatial_object=page
            ),
        )
        signatures[block["Id"]].raw_object = block

    for signature_id, signature in signatures.items():
        signature.page = page.page_num
        signature.page_id = page.id

    return list(signatures.values())

def _create_keyvalue_objects(
    key_value_ids: List[str],
    id_json_map: Dict[str, Any],
    id_entity_map: Dict[str, str],
    entity_id_map: Dict[str, list],
    page: Page,
) -> Tuple[List[KeyValue], List[Word]]:
    """
    Creates list of KeyValue objects for all key-value pairs in the Page derived from the API response JSON.

    :param key_value_ids: List of ids corresponding to the KeyValues in the page.
    :type key_value_ids: list
    :param id_json_map: Dictionary containing entity_id:JSON block mapping.
    :type id_json_map: dict
    :param entity_id_map: Dictionary containing entity_type:List[entity_id] mapping.
    :type entity_id_map: dict
    :param id_entity_map: Dictionary containing entity_id:entity_type mapping.
    :type id_entity_map: dict
    :param page: Instance of parent Page object.
    :type page: Page

    :return: Returns a list of KeyValue objects and list of Word objects with CHILD relationship
             to the KeyValue objects.
    :rtype: List[KeyValue], List[Word]
    """
    page_kv = []
    for kv_id in key_value_ids:
        if kv_id in page.child_ids:
            validate_entity_schema(id_json_map[kv_id], entity=KEY_VALUE_SET)
            page_kv.append(id_json_map[kv_id])

    keys_info = _filter_by_entity(page_kv, entity_type="KEY")

    key_value_id_map = {
        block["Id"]: _get_relationship_ids(block, relationship="VALUE")[0]
        for block in keys_info.values()
    }

    values = _create_value_objects(
        list(key_value_id_map.values()), id_json_map, entity_id_map, page
    )

    keys = {}
    for block in keys_info.values():
        keys[block["Id"]] = KeyValue(
            entity_id=block["Id"],
            bbox=BoundingBox.from_normalized_dict(
                block["Geometry"]["BoundingBox"], spatial_object=page
            ),
            contains_checkbox=values[key_value_id_map[block["Id"]]].contains_checkbox,
            value=values[key_value_id_map[block["Id"]]],
            confidence=block["Confidence"],
        )
        keys[block["Id"]].raw_object = block

    # Add words and children (Value Object) to KeyValue object
    kv_words = []
    for key_id in keys.keys():
        keys[key_id].value.key_id = key_id
        if keys[key_id].contains_checkbox:
            keys[key_id].value.children[0].key_id = key_id
            keys[key_id].selection_status = keys[key_id].value.children[0].status
        else:
            kv_words.extend(values[key_value_id_map[key_id]].words)

        key_child_ids = _get_relationship_ids(keys_info[key_id], relationship="CHILD")
        key_word_ids = [
            child_id
            for child_id in key_child_ids
            if id_json_map[child_id]["BlockType"] == WORD
        ]
        key_words = _create_word_objects(key_word_ids, id_json_map, page)

        key_child_ids = [
            child_id for child_id in key_child_ids if child_id not in key_word_ids
        ]
        key_selection_elements = _create_selection_objects(
            key_child_ids, id_json_map, page
        )
        # find a place to add selection elements for keys

        keys[key_id].key = key_words
        keys[key_id].add_children([values[key_value_id_map[key_id]]])
        kv_words.extend(key_words)

    key_values = list(keys.values())
    for kv in key_values:
        kv.page = page.page_num
        kv.page_id = page.id
    return key_values, kv_words


def _create_table_cell_objects(
    page_tables: List[Any],
    id_entity_map: Dict[str, List[str]],
    id_json_map: Dict[str, str],
    page: Page,
) -> Tuple[Dict[str, TableCell], Dict[str, Any]]:
    """
    Creates TableCell objects for all page_tables passed as input present on a single Page of the Document.

    :param page_tables: List containing JSON structure of tables within the page.
    :type page_tables: list
    :param id_entity_map: Dictionary containing entity_id:entity_type mapping.
    :type id_entity_map: dict
    :param id_json_map: Dictionary containing entity_id:JSON block mapping.
    :type id_json_map: dict
    :param page: Instance of parent Page object.
    :type page: Page

    :return: Returns a dictionary containing TableCells mapped with their IDs and dictionary containing ID: CELL JSON mapping.
    :rtype: Dict[str, TableCell], Dict[str, Any]
    """
    all_table_cells_info = {}
    for table in page_tables:
        for cell_id in _get_relationship_ids(table, relationship="CHILD"):
            if id_entity_map[cell_id] == CELL:
                validate_entity_schema(id_json_map[cell_id], entity=CELL)
                all_table_cells_info[cell_id] = id_json_map[cell_id]

    table_cells = {}
    for elem_id, elem in all_table_cells_info.items():
        table_cells[elem_id] = TableCell(
            entity_id=elem_id,
            bbox=BoundingBox.from_normalized_dict(
                elem["Geometry"]["BoundingBox"], spatial_object=page
            ),
            row_index=elem["RowIndex"],
            col_index=elem["ColumnIndex"],
            row_span=elem["RowSpan"],
            col_span=elem["ColumnSpan"],
            confidence=elem["Confidence"],
            is_column_header="COLUMN_HEADER" in elem.get("EntityTypes", [])
        )
        table_cells[elem_id].raw_object = elem

    for cell in table_cells.values():
        cell.page = page.page_num
        cell.page_id = page.id
    return table_cells, all_table_cells_info


def _create_table_objects(
    table_ids: List[str],
    id_json_map: Dict[str, Any],
    id_entity_map: Dict[str, List[str]],
    entity_id_map: Dict[str, List[str]],
    page: Page,
) -> Tuple[List[Table], List[Word]]:
    """
    Creates list of Table objects for all tables in the Page derived from the API response JSON.
    This includes creating TableCell objects and updating metadata for each cell. The TableCell objects are assigned as children
    of the table.

    :param table_ids: List of ids corresponding to the Tables in the page.
    :type table_ids: list
    :param id_json_map: Dictionary containing entity_id:JSON block mapping.
    :type id_json_map: dict
    :param id_entity_map: Dictionary containing entity_id:entity_type mapping.
    :type id_entity_map: dict
    :param entity_id_map: Dictionary containing entity_type:List[entity_id] mapping.
    :type entity_id_map: dict
    :param page: Instance of parent Page object.
    :type page: Page

    :return: Returns a list of table objects and list of words present in tables.
    :rtype: List[Table], List[Word]
    """
    # Create Tables
    page_tables = []
    for table_id in table_ids:
        if table_id in page.child_ids:
            validate_entity_schema(id_json_map[table_id], entity=TABLE)
            page_tables.append(id_json_map[table_id])

    tables = {}
    for val in page_tables:
        tables[val["Id"]] = Table(
            entity_id=val["Id"],
            bbox=BoundingBox.from_normalized_dict(
                val["Geometry"]["BoundingBox"], spatial_object=page
            ),
        )
        tables[val["Id"]].raw_object = val

    # Create Table Cells
    table_cells, all_table_cells_info = _create_table_cell_objects(
        page_tables, id_entity_map, id_json_map, page
    )

    merged_table_cells = [
        id_json_map[merge_id] for merge_id in entity_id_map[MERGED_CELL]
    ]

    checkboxes = _create_selection_objects(
        entity_id_map[SELECTION_ELEMENT], id_json_map, page
    )

    # Add children to cells
    merged_child_map = {
        merged_cell["Id"]: _get_relationship_ids(merged_cell, relationship="CHILD")
        for merged_cell in merged_table_cells
    }
    merged_child_ids = sum([ids for ids in merged_child_map.values()], [])

    table_words = []
    for cell_id, cell in all_table_cells_info.items():
        children = _get_relationship_ids(cell, relationship="CHILD")
        cell_word_ids = [
            child_id for child_id in children if id_entity_map[child_id] == WORD
        ]
        selection_ids = [
            child_id
            for child_id in children
            if id_entity_map[child_id] == SELECTION_ELEMENT
        ]

        cell_words = _create_word_objects(cell_word_ids, id_json_map, page)
        table_words.extend(cell_words)
        selection_child = [checkboxes[child_id] for child_id in selection_ids]

        table_cells[cell_id].words = cell_words
        if selection_child:
            table_cells[cell_id].add_children(selection_child)

        # update metadata
        meta_info = cell.get("EntityTypes", [])
        merged_info = [MERGED_CELL] if cell_id in merged_child_ids else []
        table_cells[cell_id]._update_response_metadata(meta_info + merged_info)

    # optimize code
    for merge_id, child_cells in merged_child_map.items():
        for child_id in child_cells:
            if child_id in table_cells.keys():
                table_cells[child_id].parent_cell_id = merge_id
                table_cells[child_id].siblings = [
                    table_cells[cid] for cid in child_cells
                ]  # CHECK IF IDS ARE BETTER THAN INSTANCES

    # Associate Children with Tables
    for table in page_tables:
        children = _get_relationship_ids(table, relationship="CHILD")
        children_cells = []
        for child_id in children:
            children_cells.append(table_cells[child_id])

        tables[table["Id"]].add_cells(children_cells)

    tables = list(tables.values())
    for table in tables:
        table.page = page.page_num
        table.page_id = page.id
    return tables, table_words


def parse_document_api_response(response: dict) -> Document:
    """
    Parses Textract JSON response and converts them into Document object containing Page objects.
    A valid Page object must contain at least a unique name and physical dimensions.

    :param response: JSON response data in a format readable by the ResponseParser
    :type response: dict

    :return: Document object containing the hierarchy of DocumentEntity descendants.
    :rtype: Document
    """
    document = _create_document_object(response)

    id_entity_map, id_json_map, entity_id_map = {}, {}, defaultdict(list)
    for block in response["Blocks"]:
        id_entity_map[block["Id"]] = block["BlockType"]
        id_json_map[block["Id"]] = block
        entity_id_map[block["BlockType"]].append(block["Id"])

    pages, page_elements = _create_page_objects(response)
    assert len(pages) == response["DocumentMetadata"]["Pages"]

    for page_json in page_elements:
        entities = {}
        page = pages[page_json["Id"]]

        lines, line_words = _create_line_objects(entity_id_map[LINE], id_json_map, page)
        page.lines = lines

        key_values, kv_words = _create_keyvalue_objects(
            entity_id_map[KEY_VALUE_SET],
            id_json_map,
            id_entity_map,
            entity_id_map,
            page,
        )
        kvs = [kv for kv in key_values if not kv.contains_checkbox]
        checkboxes = [kv for kv in key_values if kv.contains_checkbox]

        page.key_values = kvs
        page.checkboxes = checkboxes

        for checkbox in checkboxes:
            id_entity_map[checkbox.id] = SELECTION_ELEMENT

        tables, table_words = _create_table_objects(
            entity_id_map[TABLE], id_json_map, id_entity_map, entity_id_map, page
        )
        page.tables = tables

        all_words = table_words + kv_words + line_words
        all_words = {word.id: word for word in all_words}

        page.words = list(all_words.values())

        queries = _create_query_objects(
            entity_id_map[QUERY], id_json_map, entity_id_map, page
        )
        page.queries = queries

        signatures = _create_signature_objects(
            entity_id_map[SIGNATURE], id_json_map, entity_id_map, page
        )
        page.signatures = signatures

    document.pages = sorted(list(pages.values()), key=lambda x: x.page_num)
    return document


def parse_analyze_id_response(response):
    id_documents = []
    response["Blocks"] = []
    for doc in response["IdentityDocuments"]:
        fields = {}
        for field in doc["IdentityDocumentFields"]:
            fields[field["Type"]["Text"]] = {
                "key": field["Type"]["Text"],
                "value": field["ValueDetection"]["Text"],
                "confidence": field["ValueDetection"]["Confidence"],
            }
        id_documents.append(IdentityDocument(fields))
        id_documents[-1].raw_object = doc
        response["Blocks"].extend(doc.get("Blocks", []))
    # FIXME: Quick fix, we need something more robust
    document = parse_document_api_response(response)
    del response["Blocks"]
    document.identity_documents = id_documents
    document.response = response
    return document


def create_expense_from_field(field: Dict, page: Page) -> ExpenseField:
    if "Type" in field:
        type_expense = ExpenseType(
            field["Type"]["Text"], field["Type"]["Confidence"], field["Type"]
        )
    else:
        type_expense = None
    if "ValueDetection" in field:
        value_expense = Expense(
            bbox=BoundingBox.from_normalized_dict(
                field["ValueDetection"]["Geometry"]["BoundingBox"], spatial_object=page
            ),
            text=field["ValueDetection"]["Text"],
            confidence=field["ValueDetection"]["Confidence"],
            page = page.page_num
        )
        value_expense.raw_object = field["ValueDetection"]
    else:
        value_expense = None
    if "LabelDetection" in field:
        label_expense = Expense(
            bbox=BoundingBox.from_normalized_dict(
                field["LabelDetection"]["Geometry"]["BoundingBox"], spatial_object=page
            ),
            text=field["LabelDetection"]["Text"],
            confidence=field["LabelDetection"]["Confidence"],
            page=page.page_num
        )
        label_expense.raw_object = field["LabelDetection"]
    else:
        label_expense = None
    group_properties = []
    if "GroupProperties" in field:
        for group_property in field["GroupProperties"]:
            group_properties.append(
                ExpenseGroupProperty(id=group_property["Id"], types=group_property["Types"])
            )
    if "Currency" in field:
        currency = field["Currency"]["Code"]
    else:
        currency = None
    return ExpenseField(type_expense, value_expense, group_properties=group_properties, label=label_expense,
                        currency=currency, page=page.page_num)



def parser_analyze_expense_response(response):
    response["Blocks"] = [b for doc in response["ExpenseDocuments"] for b in doc.get("Blocks", [])]
    document = parse_document_api_response(response)
    for doc in response["ExpenseDocuments"]:
        # FIXME
        if len(doc["SummaryFields"]) == 0:
            continue
        page = document.pages[doc["SummaryFields"][0]["PageNumber"] - 1]
        summary_fields = []
        for summary_field in doc["SummaryFields"]:
            summary_fields.append(create_expense_from_field(summary_field, page))
            summary_fields[-1].raw_object = summary_field

        line_items_groups = []
        for line_items_group in doc["LineItemGroups"]:
            line_item_rows = []
            for i, line_item in enumerate(line_items_group["LineItems"]):
                row_expenses = []
                for line_item_field in line_item["LineItemExpenseFields"]:
                    row_expenses.append(create_expense_from_field(line_item_field, page))
                    row_expenses[-1].raw_object = line_item_field
                line_item_rows.append(LineItemRow(index=i, line_item_expense_fields=row_expenses, page=page.page_num))
            line_items_groups.append(LineItemGroup(index=line_items_group["LineItemGroupIndex"], line_item_rows=line_item_rows, page=page.page_num))

        bbox = BoundingBox.enclosing_bbox(bboxes=[s.bbox for s in summary_fields] + [g.bbox for g in line_items_groups], spatial_object=page)
        expense_document = ExpenseDocument(
            summary_fields=summary_fields, line_items_groups=line_items_groups, bounding_box=bbox, page=page.page_num
        )
        expense_document.raw_object = doc
        document.pages[summary_field["PageNumber"] - 1].expense_documents.append(
            expense_document
        )
    del response["Blocks"]
    document.response = response
    return document


def parse(response: dict) -> Document:
    """
    Ingests response data and API Call Mode and calls the appropriate function for it.
    Presently supports only SYNC and ASYNC API calls. Will be extended to Analyze ID and Expense in the future.

    :param response: JSON response data in a format readable by the ResponseParser.
    :type response: dict

    :return: Document object returned after making respective parse function calls.
    :rtype: Document
    """

    if "IdentityDocuments" in response:
        return parse_analyze_id_response(response)
    if "ExpenseDocuments" in response:
        return parser_analyze_expense_response(response)
    else:
        return parse_document_api_response(response)
