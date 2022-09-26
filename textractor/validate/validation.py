"""Validate the input json block for every document entity"""

import jsonschema
from jsonschema import validate

from textractor.data.constants import (
    WORD,
    LINE,
    KEY_VALUE_SET,
    CELL,
    TABLE,
    SELECTION_ELEMENT,
)


def validate_entity_schema(json_block, entity):
    """
    Returns True if the json_block adheres to the format the parser can handle for entity creation. Returns False otherwise.
    Exceptions and Errors are raised internally within functions depending on severity of the difference in format.
    :param json_block: Block of json as returned by the Textract API response for each Document entity
    :param entity: Respective entity for which information is contained in json_block
    :return: True/False
    """
    if entity == WORD:
        return validate_word(json_block)
    elif entity == LINE:
        return validate_line(json_block)
    elif entity == KEY_VALUE_SET:
        return validate_kv(json_block)
    elif entity == CELL:
        return validate_table_cell(json_block)
    elif entity == TABLE:
        return validate_table(json_block)
    elif entity == SELECTION_ELEMENT:
        return validate_checkbox(json_block)


def validate_word(json_block):
    word_schema = {
        "type": "object",
        "properties": {
            "BlockType": {"type": "string"},
            "Confidence": {"type": "number"},
            "Text": {"type": "string"},
            "TextType": {"type": "string"},
            "Geometry": {
                "type": "object",
                "properties": {
                    "BoundingBox": {
                        "type": "object",
                        "properties": {
                            "Width": {"type": "number"},
                            "Height": {"type": "number"},
                            "Left": {"type": "number"},
                            "Top": {"type": "number"},
                        },
                    },
                    "Polygon": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "X": {"type": "number"},
                                "Y": {"type": "number"},
                            },
                        },
                    },
                },
            },
            "Id": {"type": "string"},
        },
        "required": ["BlockType", "Confidence", "Text", "TextType", "Geometry", "Id"],
    }
    validate(instance=json_block, schema=word_schema)


def validate_line(json_block):
    line_schema = {
        "type": "object",
        "required": ["BlockType", "Confidence", "Text", "Geometry", "Id"],
        "properties": {
            "BlockType": {"type": "string"},
            "Confidence": {"type": "number"},
            "Text": {"type": "string"},
            "Geometry": {
                "type": "object",
                "properties": {
                    "BoundingBox": {
                        "type": "object",
                        "properties": {
                            "Width": {"type": "number"},
                            "Height": {"type": "number"},
                            "Left": {"type": "number"},
                            "Top": {"type": "number"},
                        },
                    },
                    "Polygon": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "X": {"type": "number"},
                                "Y": {"type": "number"},
                            },
                        },
                    },
                },
            },
            "Id": {"type": "string"},
            "Relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Type": {"type": "string"},
                        "Ids": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        },
    }
    validate(instance=json_block, schema=line_schema)


def validate_kv(json_block):
    kv_schema = {
        "type": "object",
        "required": ["BlockType", "Confidence", "Geometry", "Id", "EntityTypes"],
        "properties": {
            "BlockType": {"type": "string"},
            "Confidence": {"type": "number"},
            "Geometry": {
                "type": "object",
                "properties": {
                    "BoundingBox": {
                        "type": "object",
                        "properties": {
                            "Width": {"type": "number"},
                            "Height": {"type": "number"},
                            "Left": {"type": "number"},
                            "Top": {"type": "number"},
                        },
                    },
                    "Polygon": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "X": {"type": "number"},
                                "Y": {"type": "number"},
                            },
                        },
                    },
                },
            },
            "Id": {"type": "string"},
            "Relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Type": {"type": "string"},
                        "Ids": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "EntityTypes": {"type": "array", "items": {"type": "string"}},
        },
    }
    return validate(instance=json_block, schema=kv_schema)


def validate_checkbox(json_block):
    checkbox_schema = {
        "type": "object",
        "required": ["BlockType", "Confidence", "Geometry", "Id", "SelectionStatus"],
        "properties": {
            "BlockType": {"type": "string"},
            "Confidence": {"type": "number"},
            "Geometry": {
                "type": "object",
                "properties": {
                    "BoundingBox": {
                        "type": "object",
                        "properties": {
                            "Width": {"type": "number"},
                            "Height": {"type": "number"},
                            "Left": {"type": "number"},
                            "Top": {"type": "number"},
                        },
                    },
                    "Polygon": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "X": {"type": "number"},
                                "Y": {"type": "number"},
                            },
                        },
                    },
                },
            },
            "Id": {"type": "string"},
            "SelectionStatus": {"type": "string"},
        },
    }
    return validate(instance=json_block, schema=checkbox_schema)


def validate_table_cell(json_block):
    cell_schema = {
        "type": "object",
        "required": [
            "BlockType",
            "Confidence",
            "RowIndex",
            "ColumnIndex",
            "RowSpan",
            "ColumnSpan",
            "Geometry",
            "Id",
        ],
        "properties": {
            "BlockType": {"type": "string"},
            "Confidence": {"type": "number"},
            "RowIndex": {"type": "number"},
            "ColumnIndex": {"type": "number"},
            "RowSpan": {"type": "number"},
            "ColumnSpan": {"type": "number"},
            "Geometry": {
                "type": "object",
                "properties": {
                    "BoundingBox": {
                        "type": "object",
                        "properties": {
                            "Width": {"type": "number"},
                            "Height": {"type": "number"},
                            "Left": {"type": "number"},
                            "Top": {"type": "number"},
                        },
                    },
                    "Polygon": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "X": {"type": "number"},
                                "Y": {"type": "number"},
                            },
                        },
                    },
                },
            },
            "Id": {"type": "string"},
            "Relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Type": {"type": "string"},
                        "Ids": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "EntityTypes": {"type": "array", "items": {"type": "string"}},
        },
    }
    validate(instance=json_block, schema=cell_schema)


def validate_table(json_block):
    table_schema = {
        "type": "object",
        "required": ["BlockType", "Confidence", "Geometry", "Id"],
        "properties": {
            "BlockType": {"type": "string"},
            "Confidence": {"type": "number"},
            "Geometry": {
                "type": "object",
                "properties": {
                    "BoundingBox": {
                        "type": "object",
                        "properties": {
                            "Width": {"type": "number"},
                            "Height": {"type": "number"},
                            "Left": {"type": "number"},
                            "Top": {"type": "number"},
                        },
                    },
                    "Polygon": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "X": {"type": "number"},
                                "Y": {"type": "number"},
                            },
                        },
                    },
                },
            },
            "Id": {"type": "string"},
        },
        "Relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Type": {"type": "string"},
                    "Ids": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    }
    validate(instance=json_block, schema=table_schema)
