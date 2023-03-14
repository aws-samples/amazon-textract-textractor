"""
The :class:`EntityList` is an extension of list type with custom functions to print document entities \
in a well formatted manner and visualize on top of the document page with their BoundingBox information. 

The two main functions within this class are :code:`pretty_print()` and :code:`visualize()`.
Use :code:`pretty_print()` to get a string formatted output of your custom list of entities.
Use :code:`visualize()` to get the bounding box visualization of the entities on the document page images.
"""

import os
import csv
import logging
from enum import Enum
from io import StringIO
from tabulate import tabulate
from typing import List, Optional, TypeVar, Generic, Any
from collections import defaultdict
from textractor.utils.geometry_util import get_indices
from PIL import Image, ImageDraw, ImageColor, ImageFont

from textractor.data.constants import TextractType, TableFormat, AnalyzeExpenseLineItemFields, AnalyzeExpenseFields
from textractor.exceptions import EntityListCreationError, NoImageException

logger = logging.getLogger(__name__)

present_path = os.path.abspath(os.path.dirname(__file__))

T = TypeVar("T")


class EntityList(list, Generic[T]):
    """
    Creates a list type object, initially empty but extended with the list passed in objs.

    :param objs: Custom list of objects that can be visualized with this class.
    :type objs: list
    """

    def __init__(self, objs=None):
        super().__init__()

        if objs is None:
            objs = []
        elif not isinstance(objs, list):
            objs = [objs]

        self.extend(objs)

    def visualize(
        self,
        with_text: bool = True,
        with_words: bool = True,
        with_confidence: bool = False,
        font_size_ratio: float = 0.5,
    ) -> List:
        """
        Returns list of PIL Images with bounding boxes drawn around the entities in the list.

        :param with_text: Flag to print the OCR output of Textract on top of the text bounding box.
        :type with_text: bool
        :param with_confidence: Flag to print the confidence of prediction on top of the entity bounding box.
        :type with_confidence: bool

        :return: Returns list of PIL Images with bounding boxes drawn around the entities in the list.
        :rtype: list
        """
        # FIXME: This is inelegant
        if len(self) > 0 and any([ent.__class__.__name__ == "Document" for ent in self]):
            return EntityList(self[0].pages).visualize(
                with_text=with_text,
                with_words=with_words,
                with_confidence=with_confidence,
                font_size_ratio=font_size_ratio,
            )
        elif len(self) > 0 and any([ent.__class__.__name__ == "Page" for ent in self]):
            new_entity_list = []
            for entity in self:
                if not with_words and (entity.__class__.__name__ == "Word" or entity.__class__.__name__ == "Line"):
                    continue
                if entity.__class__.__name__ == "Page":
                    if with_words:
                        new_entity_list.extend(entity.words)
                        new_entity_list.extend(entity.lines)
                    new_entity_list.extend(entity.tables)
                    new_entity_list.extend(entity.key_values)
                    for expense_document in entity.expense_documents:
                        new_entity_list = self._add_expense_document_to_list(new_entity_list, expense_document)
                elif entity.__class__.__name__ == "ExpenseDocument":
                    self._add_expense_document_to_list(new_entity_list, entity)
                else:
                    new_entity_list.append(entity)
            return EntityList(list(set(new_entity_list))).visualize(
                with_text=with_text,
                with_words=with_words,
                with_confidence=with_confidence,
                font_size_ratio=font_size_ratio,
            )
        elif len(self) > 0 and self[0].bbox.spatial_object.image is None:
            raise NoImageException(
                "Image was not saved during the Textract API call. Set save_image=True when calling the Textractor methods to use the visualize() method."
            )

        visualized_images = {}
        entities_pagewise = defaultdict(list)
        for obj in self:
            entities_pagewise[obj.page].append(obj)
            try:
                if with_words:
                    entities_pagewise[obj.page].extend(obj.words)
            # FIXME: There should be a way to recurse through all entities
            except AttributeError:
                pass
        for page in list(entities_pagewise.keys()):
            # Deduplication
            entities_pagewise[page] = list(set(entities_pagewise[page]))

        for page in entities_pagewise.keys():
            visualized_images[page] = _draw_bbox(
                entities_pagewise[page],
                with_text,
                with_confidence,
                font_size_ratio,
            )

        images = list(visualized_images.values())
        images = images if len(images) != 1 else images[0]
        return images

    def _add_expense_document_to_list(self, entity_list, expense_document):
        entity_list.append(expense_document)
        for field in expense_document.summary_fields_list:
            entity_list.append(field)
        for line_item_group in expense_document.line_items_groups:
            entity_list.append(line_item_group)
            for row in line_item_group.rows:
                entity_list.append(row)
                for expense in row.expenses:
                    if expense.type.text != AnalyzeExpenseLineItemFields.EXPENSE_ROW.name:
                        entity_list.append(expense)
        return entity_list

    def pretty_print(
        self,
        table_format: TableFormat = TableFormat.GITHUB,
        with_confidence: bool = False,
        with_geo: bool = False,
        with_page_number: bool = False,
        trim: bool = False,
    ) -> str:
        """
        Returns a formatted string output for each of the entities in the list according to its entity type.

        :param table_format: Choose one of the defined TableFormat types to decorate the table output string. This is a predefined set of choices by the PyPI tabulate package. It is used only if there are KeyValues or Tables in the list of textractor.entities.
        :type table_format: TableFormat
        :param with_confidence: Flag to add the confidence of prediction to the entity string. default= False.
        :type with_confidence: bool
        :param with_geo: Flag to add the bounding box information to the entity string. default= False.
        :type with_geo: bool
        :param with_page_number: Flag to add the page number to the entity string. default= False.
        :type with_page_number: bool
        :param trim: Flag to trim text in the entity string. default= False.
        :type trim: bool

        :return: Returns a formatted string output for each of the entities in the list according to its entity type.
        :rtype: str
        """

        result_value = ""
        result_value += self._get_text_string(
            with_page_number=with_page_number,
            with_confidence=with_confidence,
            trim=trim,
            textract_type=TextractType.WORDS,
        )
        result_value += self._get_text_string(
            with_page_number=with_page_number,
            with_confidence=with_confidence,
            trim=trim,
            textract_type=TextractType.LINES,
        )
        result_value += self._get_forms_string(
            table_format=table_format,
            with_confidence=with_confidence,
            with_geo=with_geo,
            trim=trim,
            textract_type=TextractType.KEY_VALUE_SET,
        )
        result_value += self._get_forms_string(
            table_format=table_format,
            with_confidence=with_confidence,
            with_geo=with_geo,
            trim=trim,
            textract_type=TextractType.SELECTION_ELEMENT,
        )
        result_value += self._get_tables_string(
            table_format=table_format,
            with_confidence=with_confidence,
            with_geo=with_geo,
            trim=trim,
        )
        result_value += self._get_queries_string()
        result_value += self._get_expense_documents_string()
        result_value += self._get_id_documents_string()
        return result_value

    def _get_text_string(
        self,
        with_page_number=False,
        with_confidence=False,
        trim=False,
        textract_type=TextractType.WORDS,
    ):
        """
        Returns a formatted string output for the entity type stated in the textract_type param. This function is
        specific to TextractType.WORDS and TextractType.LINES.

        :param with_page_number: Flag to add the page number to the entity string. default= False.
        :type with_page_number: bool
        :param with_confidence: Flag to add the confidence of prediction to the entity string. default= False.
        :type with_confidence: bool
        :param trim: Flag to trim text in the entity string. default= False.
        :type trim: bool
        :param textract_type: TextractType.WORDS / TextractType.LINES
        :type textract_type: TextractType

        :return: Returns a formatted string output for the entity type stated in the textract_type param.
        :rtype: str
        """

        result_value = ""

        if textract_type == TextractType.WORDS:
            objects = sorted(
                [obj for obj in self if obj.__class__.__name__ == "Word"],
                key=lambda x: x.page,
            )
        else:
            objects = sorted(
                [obj for obj in self if obj.__class__.__name__ == "Line"],
                key=lambda x: x.page,
            )

        current_page = -1

        for word in objects:
            if with_page_number and word.page != current_page:
                result_value += f"--------- page number: {word.page} - page ID: {word.page_id} --------------{os.linesep}"
                current_page = word.page
            if trim:
                result_value += f"{word.text.strip()}"
            else:
                result_value += f"{word.text}"

            if with_confidence:
                result_value += f", {word.confidence}"
            result_value += os.linesep

        return result_value

    def _get_forms_string(
        self,
        table_format: TableFormat = TableFormat.GITHUB,
        with_confidence: bool = False,
        with_geo: bool = False,
        trim: bool = False,
        textract_type=TextractType.KEY_VALUE_SET,
    ) -> str:
        """
        Returns a formatted string output for the entity type stated in the textract_type param. This function is
        specific to TextractType.KEY_VALUE_SET and TextractType.SELECTION_ELEMENT.

        :param table_format: Choose one of the defined TableFormat types to decorate the table output string.
                             This is a predefined set of choices by the PyPI tabulate package.
        :type table_format: TableFormat
        :param with_confidence: Flag to add the confidence of prediction to the entity string. default= False.
        :type with_confidence: bool
        :param with_geo: Flag to add the bounding box information to the entity string. default= False.
        :type with_geo: bool
        :param trim: Flag to trim text in the entity string. default= False.
        :type trim: bool
        :param textract_type: TextractType.KEY_VALUE_SET / TextractType.SELECTION_ELEMENT
        :type textract_type: TextractType

        :return: Returns a formatted string output for the entity type stated in the textract_type param.
        :rtype: str
        """

        logger.debug(f"table_format: {table_format}")
        result_value = ""

        if textract_type == TextractType.KEY_VALUE_SET:
            key_value_objects = [
                obj
                for obj in self
                if obj.__class__.__name__ == "KeyValue" and not obj.contains_checkbox
            ]
        else:
            key_value_objects = [
                obj
                for obj in self
                if obj.__class__.__name__ == "KeyValue" and obj.contains_checkbox
            ]

        kv_dict = {obj.page: [] for obj in key_value_objects}

        for obj in key_value_objects:
            kv_dict[obj.page].append(obj)

        if not table_format == TableFormat.CSV:
            for page in kv_dict.keys():
                forms_list = _convert_form_to_list(
                    kv_dict[page],
                    with_confidence=with_confidence,
                    with_geo=with_geo,
                    trim=trim,
                    textract_type=textract_type,
                )
                result_value += (
                    tabulate(forms_list, tablefmt=table_format.name.lower())
                    + os.linesep
                    + os.linesep
                )

        if table_format == TableFormat.CSV:
            logger.debug(f"pretty print - csv")
            csv_output = StringIO()
            csv_writer = csv.writer(
                csv_output, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            for page in kv_dict.keys():
                forms_list = _convert_form_to_list(
                    kv_dict[page],
                    with_confidence=with_confidence,
                    with_geo=with_geo,
                    trim=trim,
                    textract_type=textract_type,
                )
                csv_writer.writerows(forms_list)
            csv_writer.writerow([])
            result_value = csv_output.getvalue()
        return result_value

    def _get_tables_string(
        self,
        table_format: TableFormat = TableFormat.GITHUB,
        with_confidence: bool = False,
        with_geo: bool = False,
        trim: bool = False,
    ) -> str:
        """
        Returns a formatted string output for the Table entity type.

        :param table_format: Choose one of the defined TableFormat types to decorate the table output string.
                             This is a predefined set of choices by the PyPI tabulate package.
        :type table_format: TableFormat
        :param with_confidence: Flag to add the confidence of prediction to the entity string. default= False.
        :type with_confidence: bool
        :param with_geo: Flag to add the bounding box information to the entity string. default= False.
        :type with_geo: bool
        :param trim: Flag to trim text in the entity string. default= False.
        :type trim: bool

        :return: Returns a formatted string output for the Table entity type.
        :rtype: str
        """

        logger.debug(f"table_format: {table_format}")

        tables = {}
        for obj in self:
            if obj.__class__.__name__ == "Table":
                tables[obj.id] = obj
            elif obj.__class__.__name__ == "TableCell":
                if obj.table_id in tables.keys():
                    tables[obj.table_id].append(obj)
                else:
                    tables[obj.table_id] = [obj]

        result_value = ""
        if not table_format == TableFormat.CSV:
            for table_id in tables.keys():
                table_type = (
                    TextractType.TABLES
                    if tables[table_id].__class__.__name__ == "Table"
                    else TextractType.TABLE_CELL
                )

                table_list = _convert_table_to_list(
                    tables[table_id],
                    with_confidence=with_confidence,
                    with_geo=with_geo,
                    trim=trim,
                    textract_type=table_type,
                )
                result_value += (
                    tabulate(table_list, tablefmt=table_format.name.lower())
                    + os.linesep
                    + os.linesep
                )

        if table_format == TableFormat.CSV:
            logger.debug(f"pretty print - csv")
            for table_id in tables.keys():
                table_type = (
                    TextractType.TABLES
                    if tables[table_id].__class__.__name__ == "Table"
                    else TextractType.TABLE_CELL
                )
                csv_output = StringIO()
                csv_writer = csv.writer(
                    csv_output, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
                )

                table_list = _convert_table_to_list(
                    tables[table_id],
                    with_confidence=with_confidence,
                    with_geo=with_geo,
                    trim=trim,
                    textract_type=table_type,
                )
                csv_writer.writerows(table_list)
                csv_writer.writerow([])
                result_value += csv_output.getvalue()
        return result_value

    def _get_queries_string(self):
        result_value = ""
        queries = [obj for obj in self if obj.__class__.__name__ == "Query"]

        for query in queries:
            if query.result is not None:
                result_value += f"{query.query} => {query.result.answer}{os.linesep}"
            else:
                result_value += f"{query.query} => {os.linesep}"

        return result_value

    def _get_expense_documents_string(self):
        result_value = ""
        expense_documents = [
            obj for obj in self if obj.__class__.__name__ == "ExpenseDocument"
        ]

        for i, expense_document in enumerate(expense_documents):
            result_value += f"Expense Document {i+1}:{os.linesep}"
            result_value += f"### Summary Fields:{os.linesep}"
            result_value += f"{expense_document.summary_fields}{os.linesep}"
            result_value += f"### Line Item Groups: {os.linesep}"
            for line_item_group in expense_document.line_items_groups:
                result_value += f"{line_item_group}{os.linesep}"

        return result_value

    def _get_id_documents_string(self):
        result_value = ""
        id_documents = [
            obj for obj in self if obj.__class__.__name__ == "IdentityDocument"
        ]

        for id_document in id_documents:
            result_value += f"{id_document}{os.linesep}"

        return result_value

    def __add__(self, list2):
        return EntityList([*self, *list2])


def _convert_form_to_list(
    form_objects,
    with_confidence: bool = False,
    with_geo: bool = False,
    trim: bool = False,
    textract_type=TextractType.KEY_VALUE_SET,
) -> List:
    """
    Converts KeyValue objects (KEY_VALUE_SET in JSON) to row-wise list format to pretty_print using the
    PyPI tabulate package.

    :param form_objects: KeyValue instances to be formatted into strings
    :type form_objects: KeyValue
    :param with_confidence: Flag to add the confidence of prediction to the entity string. default= False.
    :type with_confidence: bool
    :param with_geo: Flag to add the bounding box information to the entity string. default= False.
    :type with_geo: bool
    :param trim: Flag to trim text in the entity string. default= False.
    :type trim: bool
    :param textract_type: TextractType.KEY_VALUE_SET / TextractType.SELECTION_ELEMENT
    :type textract_type: TextractType

    :return: Returns a list of lists, each inner list containing a key-value pair.
    :rtype: List[List[str]]
    """

    rows_list = list()
    rows_list.append(["Key", "Value"])
    for field in form_objects:
        t_key = ""
        t_value = ""
        if field.key:
            text = " ".join([word.text for word in field.key.words])
            if trim:
                t_key = text.strip()
            else:
                t_key = text
            if with_geo:
                t_key += " {" + field.bbox.__repr__() + "} "
            if with_confidence:
                t_key += f" ({field.key.confidence:.1f})"
        if field.value:
            text = (
                field.value.words
                if textract_type == TextractType.SELECTION_ELEMENT
                else " ".join([word.text for word in field.value.words])
            )
            if trim:
                t_value = text.strip()
            else:
                t_value = text
            if with_geo:
                t_value += " {" + field.value.bbox.__repr__() + "} "
            if with_confidence:
                t_value += f" ({field.value.confidence:.1f})"
        rows_list.append([t_key, t_value])
    return rows_list


def _convert_table_to_list(
    table_object,
    with_confidence: bool = False,
    with_geo: bool = False,
    trim: bool = False,
    textract_type=TextractType.TABLES,
) -> List:
    """
    Converts Table objects (TABLE in JSON) to row-wise list format to pretty_print using the
    PyPI tabulate package.

    :param table_object: Table instance to be formatted into strings
    :type table_object: Table
    :param with_confidence: Flag to add the confidence of prediction to the entity string. default= False.
    :type with_confidence: bool
    :param with_geo: Flag to add the bounding box information to the entity string. default= False.
    :type with_geo: bool
    :param trim: Flag to trim text in the entity string. default= False.
    :type trim: bool
    :param textract_type: TextractType.TABLES / TextractType.TABLE_CELL
    :type textract_type: TextractType

    :return: Returns a list of lists, each inner list containing a row of table data.
    :rtype: List[List]
    """
    if textract_type == TextractType.TABLES:
        rowwise_table = table_object._get_table_cells()
    else:
        rowwise_table = {cell.row_index: [] for cell in table_object}
        for cell in table_object:
            rowwise_table[cell.row_index].append(cell)
    table_rows = []
    for row in rowwise_table.keys():
        row_data = []
        for cell in rowwise_table[row]:
            text = cell.__repr__().split(">")[-1][1:]
            if trim:
                t_key = text.strip()
            else:
                t_key = text
            if with_geo:
                t_key += " {" + cell.bbox.__repr__() + "} "
            if with_confidence:
                t_key += f" ({cell.confidence:.1f})"
            row_data.append(t_key)
        table_rows.append(row_data)
    return table_rows


def _draw_bbox(
    entities: List[Any],
    with_text: bool = False,
    with_confidence: bool = False,
    font_size_ratio: float = 0.5,
):
    """
    Function to draw bounding boxes on all objects in entities present in a particular page.

    :param entities: List of entities to be visualized on top of the document page
    :type entities: list, required
    :param with_text: Flag to indicate if text is to be printed on top of the bounding box
    :type with_text: bool, optional
    :param with_word_text_only: Flag to print only the word-level OCR output of Textract on top of the text bounding box.
    :type with_word_text_only: bool
    :param with_confidence: Flag to print the confidence of prediction on top of the entity bounding box.
    :type with_confidence: bool
    :param with_word_confidence_only: Flag to print only the word-level confidence of Textract OCR.
    :type with_word_confidence_only: bool

    :return: Returns PIL.Image with bounding boxes drawn for the entities passed to the function
    :rtype: PIL.Image
    """
    image = entities[0].bbox.spatial_object.image
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    drw = ImageDraw.Draw(overlay, "RGBA")

    text_locations = {}

    # First drawing, bounding boxes
    for entity in entities:
        width, height = image.size
        if entity.__class__.__name__ == "Table":
            overlayer_data = _get_overlayer_data(entity, width, height)
            drw.rectangle(
                xy=overlayer_data["coords"], outline=overlayer_data["color"], width=2
            )
            processed_cells = set()
            for cell in entity.table_cells:
                if cell.id in processed_cells:
                    continue
                if cell.siblings:
                    for c in cell.siblings:
                        processed_cells.add(c.id)
                    min_x, min_y, max_x, max_y = list(
                        zip(
                            *[
                                (
                                    c.bbox.x,
                                    c.bbox.y,
                                    c.bbox.x + c.bbox.width,
                                    c.bbox.y + c.bbox.height,
                                )
                                for c in cell.siblings + [cell]
                            ]
                        )
                    )
                    min_x, min_y, max_x, max_y = (
                        min(min_x),
                        min(min_y),
                        max(max_x),
                        max(max_y),
                    )
                else:
                    processed_cells.add(cell.id)
                    min_x, min_y, max_x, max_y = (
                        cell.bbox.x,
                        cell.bbox.y,
                        cell.bbox.x + cell.bbox.width,
                        cell.bbox.y + cell.bbox.height,
                    )

                fill_color=None
                if cell.is_column_header:
                    fill_color = ImageColor.getrgb("blue") + (120,)

                drw.rectangle(
                    (
                        int(min_x * width),
                        int(min_y * height),
                        int(max_x * width),
                        int(max_y * height),
                    ),
                    outline=overlayer_data["color"],
                    fill=fill_color,
                    width=2,
                )
                for checkbox in cell.checkboxes:
                    drw.rectangle(
                        (int(checkbox.bbox.x * width),
                        int(checkbox.bbox.y * height),
                        int((checkbox.bbox.x + checkbox.bbox.width) * width),
                        int((checkbox.bbox.y + checkbox.bbox.height) * height)),
                        outline=ImageColor.getrgb("lightgreen") if checkbox.is_selected() else ImageColor.getrgb("indianred")
                    )
        elif entity.__class__.__name__ == "Query":
            overlayer_data = _get_overlayer_data(entity.result, width, height)
            drw.rectangle(
                xy=overlayer_data["coords"], outline=overlayer_data["color"], width=2
            )
        elif entity.__class__.__name__ == "ExpenseField":
            overlayer_data = _get_overlayer_data(entity, width, height)
            drw.rectangle(
                xy=overlayer_data["coords_value"], outline=overlayer_data["color_value"], width=2
            )
            if entity.key is not None:
                b1 = entity.key.bbox
                b2 = entity.value.bbox
                drw.rectangle(
                    xy=overlayer_data["coords_key"], outline=overlayer_data["color_key"], width=2
                )
                drw.line([((b1.x + b1.width / 2) * width, (b1.y + b1.height / 2) * height),
                          ((b2.x + b2.width / 2) * width, (b2.y + b2.height / 2) * height)], fill=overlayer_data["color_key"], width=2)
        elif entity.__class__.__name__ == "ExpenseDocument":
            overlayer_data = _get_overlayer_data(entity, width, height)
            drw.rectangle(
                xy=overlayer_data["coords"], outline=overlayer_data["color"], width=2
            )
            for coord, text in zip(overlayer_data["coords_list"], overlayer_data["coords_list"]):
                drw.rectangle(
                    xy=coord, outline=overlayer_data["color_expense_group"], width=2
                )
        else:
            overlayer_data = _get_overlayer_data(entity, width, height)
            drw.rectangle(
                xy=overlayer_data["coords"], outline=overlayer_data["color"], width=2
            )
            if entity.__class__.__name__ == "KeyValue":
                drw.rectangle(
                    xy=overlayer_data["value_bbox"],
                    outline=overlayer_data["color_value"],
                    width=2,
                )
                b1 = overlayer_data["value_bbox"]
                b2 = overlayer_data["coords"]
                drw.line([((b1[0] + b1[2]) / 2, (b1[1] + b1[3]) / 2),
                          ((b2[0] + b2[2]) / 2, (b2[1] + b2[3]) / 2)], fill=overlayer_data["color_value"], width=1)
    
    # Second drawing, text
    if with_text:
        for entity in entities:
            if entity.__class__.__name__ == "Word":
                width, height = image.size
                overlayer_data = _get_overlayer_data(entity, width, height)

                final_txt = ""
                bbox_height = overlayer_data["coords"][3] - overlayer_data["coords"][1]
                text_height = int(bbox_height * font_size_ratio)
                fnt = ImageFont.truetype(
                    os.path.join(present_path, "arial.ttf"), text_height
                )

                final_txt += overlayer_data["text"]

                if with_confidence:
                    final_txt += " (" + str(overlayer_data["confidence"])[:4] + ")"
            
                drw.text(
                    (
                        overlayer_data["coords"][0],
                        overlayer_data["coords"][1] - text_height,
                    ),
                    final_txt,
                    font=fnt,
                    fill=overlayer_data["text_color"],
                )

            elif entity.__class__.__name__ == "KeyValue":
                width, height = image.size
                overlayer_data = _get_overlayer_data(entity, width, height)

                # Key Text
                final_txt = ""
                bbox_height = overlayer_data["coords"][3] - overlayer_data["coords"][1]
                text_height = min(int(0.03 * height), int(bbox_height * font_size_ratio))
                fnt = ImageFont.truetype(
                    os.path.join(present_path, "arial.ttf"), text_height
                )

                final_txt += overlayer_data["text"]
                if with_confidence:
                    final_txt += " (" + str(overlayer_data["confidence"])[:4] + ")"

                drw.text(
                    (
                        overlayer_data["coords"][0],
                        overlayer_data["coords"][3] + 1,
                    ),
                    final_txt,
                    font=fnt,
                    fill=overlayer_data["color"],
                )

                # Value Text
                final_txt = overlayer_data["value_text"]

                bbox_height = overlayer_data["value_bbox"][3] - overlayer_data["value_bbox"][1]
                text_height = min(int(0.01 * height), int(bbox_height * font_size_ratio))
                fnt = ImageFont.truetype(
                    os.path.join(present_path, "arial.ttf"), text_height
                )

                if with_confidence:
                    final_txt += " (" + str(overlayer_data["value_conf"])[:4] + ")"

                drw.text(
                    (
                        overlayer_data["value_bbox"][0],
                        overlayer_data["value_bbox"][3] + 1,
                    ),
                    final_txt,
                    font=fnt,
                    fill=overlayer_data["color_value"],
                )
            elif entity.__class__.__name__ == "ExpenseField":
                width, height = image.size
                overlayer_data = _get_overlayer_data(entity, width, height)

                final_txt = overlayer_data["text"]
                text_height = int(0.018 * height * font_size_ratio)
                fnt = ImageFont.truetype(
                    os.path.join(present_path, "arial.ttf"), text_height
                )
                if entity.key is not None:
                    x = overlayer_data["coords_key"][0] + 0.3*(overlayer_data["coords_key"][2] - overlayer_data["coords_key"][0])
                    y =  overlayer_data["coords_key"][1] - text_height - 1
                else:
                    x = int(overlayer_data["coords"][0] + 0.3*(overlayer_data["coords"][2] - overlayer_data["coords"][0]))
                    y = overlayer_data["coords"][1] - text_height - 1
                while (x, y) in text_locations and text_locations[(x, y)] != final_txt:
                    y = y - text_height - 1
                text_locations[(x, y)] = final_txt
                drw.text(
                    (x, y),
                    final_txt,
                    font=fnt,
                    fill=overlayer_data["text_color"],

                )
            elif entity.__class__.__name__ == "ExpenseDocument":
                width, height = image.size
                text_height = int(0.018 * height * font_size_ratio)
                fnt = ImageFont.truetype(
                    os.path.join(present_path, "arial.ttf"), text_height
                )
                overlayer_data = _get_overlayer_data(entity, width, height)
                for coord, text in zip(overlayer_data["coords_list"], overlayer_data["text_list"]):
                    drw.text(
                        (coord[0], coord[3]),
                        text,
                        font=fnt,
                        fill=overlayer_data["color_expense_group"],
                    )

            elif entity.__class__.__name__ == "Query":
                if entity.result is None:
                    continue
                
                width, height = image.size
                overlayer_data = _get_overlayer_data(entity.result, width, height)

                final_txt = entity.query + " " + overlayer_data["text"]

                bbox_height = overlayer_data["coords"][3] - overlayer_data["coords"][1]
                text_height = int(bbox_height * font_size_ratio)
                fnt = ImageFont.truetype(
                    os.path.join(present_path, "arial.ttf"), text_height
                )

                if with_confidence:
                    final_txt += " (" + str(entity.result.confidence)[:4] + ")"

                drw.text(
                    (
                        overlayer_data["coords"][0],
                        overlayer_data["coords"][1] - text_height,
                    ),
                    final_txt,
                    font=fnt,
                    fill=overlayer_data["text_color"],
                )

    del drw
    image = Image.alpha_composite(image, overlay)
    return image


def _get_overlayer_data(entity: Any, width: float, height: float) -> dict:
    """
    Returns a dictionary with all the necessary details to draw a bounding box for an entity depending on the information
    present in it. This includes the bounding box coordinates, color of bounding box, confidence of detection and OCR text.

    :param entity: DocumentEntity object for which the data needs to be created
    :type entity: DocumentEntity
    :param width: width of the Page object the entity belongs to
    :type width: float, required
    :param height: height of the Page object the entity belongs to
    :type height: float, required

    :return: Dictionary containing all the information to draw the bounding box for a DocumentEntity.
    :rtype: dict
    """
    data = {}
    bbox = entity.bbox
    x, y, w, h = (
        bbox.x * width,
        bbox.y * height,
        bbox.width * width,
        bbox.height * height,
    )
    data["coords"] = [x, y, x + w, y + h]
    data["confidence"] = (
        entity.confidence if entity.__class__.__name__ not in ["Table", "ExpenseField", "ExpenseDocument", "LineItemRow", "LineItemGroup"] else ""
    )
    data["text_color"] = (0, 0, 0)

    if entity.__class__.__name__ == "Word":
        data["text"] = entity.text
        data["color"] = ImageColor.getrgb("blue")

    elif entity.__class__.__name__ == "Line":
        data["text"] = entity.text
        data["color"] = ImageColor.getrgb("lightgrey")
        data["coords"] = [x - 1, y - 1, x + w + 1, y + h + 1]
    elif entity.__class__.__name__ == "KeyValue":
        data["text"] = entity.key.__repr__()
        data["color"] = ImageColor.getrgb("brown")
        data["value_text"] = entity.value.__repr__()
        data["coords"] = [x - 2, y - 2, x + w + 2, y + h + 2]

        if entity.contains_checkbox:
            value_bbox = entity.children[0].bbox
            data["value_conf"] = entity.children[0].confidence

        else:
            value_bbox = entity.value.bbox
            data["value_conf"] = entity.value.confidence

        data["color_value"] = ImageColor.getrgb("orange")
        x, y, w, h = (
            value_bbox.x * width - 2,
            value_bbox.y * height - 2,
            value_bbox.width * width + 2,
            value_bbox.height * height + 2,
        )
        data["value_bbox"] = [x, y, x + w, y + h]

    elif entity.__class__.__name__ == "Table":
        data["color"] = ImageColor.getrgb("green")
        data["text"] = ""

    elif entity.__class__.__name__ == "TableCell":
        data["color"] = ImageColor.getrgb("skyblue")
        data["text"] = entity.__repr__().split(">")[-1][1:]

    elif entity.__class__.__name__ == "QueryResult":
        data["color"] = ImageColor.getrgb("mediumturquoise")
        data["text"] = entity.answer
    elif entity.__class__.__name__ == "Signature":
        data["color"] = ImageColor.getrgb("coral")
    elif entity.__class__.__name__ == "ExpenseField":
        data["text"] = entity.type.text
        data["text_color"] = ImageColor.getrgb("brown")
        data["coords"] = [x - 5, y - 5, x + w + 5, y + h + 5]

        if entity.key:
            data["color_key"] = ImageColor.getrgb("brown")
            data["coords_key"] = (
                entity.key.bbox.x * width-3,
                entity.key.bbox.y * height-3,
                (entity.key.bbox.x + entity.key.bbox.width) * width+3,
                ((entity.key.bbox.y + entity.key.bbox.height)) * height+3,
            )
        data["color_value"] = ImageColor.getrgb("orange")
        data["coords_value"] = (
            entity.value.bbox.x * width-3,
            entity.value.bbox.y * height-3,
            (entity.value.bbox.x + entity.value.bbox.width) * width+3,
            ((entity.value.bbox.y + entity.value.bbox.height)) * height+3,
        )
    elif entity.__class__.__name__ == "Expense":
        data["text"] = entity.text
        data["coords"] = [x-3, y-3, x + w + 3, y + h + 3]
    elif entity.__class__.__name__ == "ExpenseDocument":
        data["color"] = ImageColor.getrgb("beige")
        data["coords_list"] = []
        data["text_list"] = []
        for group in entity.summary_groups:
            bboxes = entity.summary_groups.get_group_bboxes(group)
            for bbox in bboxes:
                data["coords_list"].append(
                    (
                        bbox.x * width - 5,
                        bbox.y * height- 5,
                        (bbox.x + bbox.width) * width + 3,
                        (bbox.y + bbox.height) * height + 3,
                    )
                )
                data["text_list"].append(
                    group
                )
        data["color_expense_group"] = ImageColor.getrgb("coral")


    elif entity.__class__.__name__ == "LineItemGroup":
        data["color"] = ImageColor.getrgb("lightblue")
        data["coords"] = [x-10, y-10, x + w + 10, y + h + 10]

    elif entity.__class__.__name__ == "LineItemRow":
        data["color"] = ImageColor.getrgb("lightyellow")
        data["coords"] = [x-7, y-7, x + w + 7, y + h + 7]
    else:
        pass
    return data
