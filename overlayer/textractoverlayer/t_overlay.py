from dataclasses import dataclass
from textractcaller.t_call import Textract_Types
from typing import List
import trp
import json


@dataclass
class DocumentDimensions():
    def __init__(self, doc_width: int, doc_height: int):
        self.__doc_width = doc_width
        self.__doc_height = doc_height

    @property
    def doc_width(self):
        return self.__doc_width

    @property
    def doc_height(self):
        return self.__doc_height


@dataclass
class BoundingBox():
    def __init__(self, geometry: trp.Geometry, document_dimensions: DocumentDimensions, box_type: Textract_Types,
                 page_number: int):
        if not geometry or not document_dimensions:
            raise ValueError("need geometry and document_dimensions to create BoundingBox object")
        self.__box_type = box_type
        self.__page_number = page_number
        bbox_width = geometry.boundingBox.width
        bbox_height = geometry.boundingBox.height
        bbox_left = geometry.boundingBox.left
        bbox_top = geometry.boundingBox.top
        self.__xmin: int = round(bbox_left * document_dimensions.doc_width)
        self.__ymin: int = round(bbox_top * document_dimensions.doc_height)
        self.__xmax: int = round(self.__xmin + (bbox_width * document_dimensions.doc_width))
        self.__ymax: int = round(self.__ymin + (bbox_height * document_dimensions.doc_height))

    def __str__(self):
        return f"BoundingBox(box_type='{self.__box_type}', page_number={self.page_number}, xmin={self.__xmin}, ymin={self.__ymin}, xmax={self.__xmax}, ymax={self.__ymax})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, obj):
        return isinstance(
            obj, BoundingBox
        ) and obj.box_type == self.__box_type and obj.xmin == self.xmin and obj.ymin == self.ymin and obj.xmax == self.xmax and obj.ymax == self.ymax and self.page_number == obj.page_number

    @property
    def xmin(self) -> int:
        return self.__xmin

    @property
    def ymin(self) -> int:
        return self.__ymin

    @property
    def xmax(self) -> int:
        return self.__xmax

    @property
    def ymax(self) -> int:
        return self.__ymax

    @property
    def box_type(self) -> Textract_Types:
        return self.__box_type

    @property
    def page_number(self) -> int:
        return self.__page_number


def get_bounding_boxes(textract_json_string: str, overlay_features: List[Textract_Types],
                       document_dimensions: DocumentDimensions) -> "list[BoundingBox]":
    doc = trp.Document(json.loads(textract_json_string))
    bounding_box_list: List[BoundingBox] = list()
    page_number: int = 0
    for page in doc.pages:
        page_number += 1
        if Textract_Types.WORD in overlay_features or Textract_Types.LINE in overlay_features:
            for line in page.lines:
                if Textract_Types.LINE in overlay_features:
                    if line:
                        bounding_box_list.append(
                            BoundingBox(geometry=line.geometry,
                                        document_dimensions=document_dimensions,
                                        box_type=Textract_Types.LINE,
                                        page_number=page_number))
                if Textract_Types.WORD in overlay_features:
                    for word in line.words:
                        if word:
                            bounding_box_list.append(
                                BoundingBox(geometry=word.geometry,
                                            document_dimensions=document_dimensions,
                                            box_type=Textract_Types.WORD,
                                            page_number=page_number))

        if any([x for x in overlay_features if x in [Textract_Types.FORM, Textract_Types.KEY, Textract_Types.VALUE]]):
            for field in page.form.fields:
                if any([x for x in overlay_features if x in [Textract_Types.FORM, Textract_Types.KEY]]):
                    if field and field.key:
                        bounding_box_list.append(
                            BoundingBox(geometry=field.key.geometry,
                                        document_dimensions=document_dimensions,
                                        box_type=Textract_Types.KEY,
                                        page_number=page_number))
                if any([x for x in overlay_features if x in [Textract_Types.FORM, Textract_Types.VALUE]]):
                    if field and field.value:
                        bounding_box_list.append(
                            BoundingBox(geometry=field.value.geometry,
                                        document_dimensions=document_dimensions,
                                        box_type=Textract_Types.VALUE,
                                        page_number=page_number))

        if any([x for x in overlay_features if x in [Textract_Types.TABLE, Textract_Types.CELL]]):
            for table in page.tables:
                if Textract_Types.TABLE in overlay_features:
                    bounding_box_list.append(
                        BoundingBox(geometry=table.geometry,
                                    document_dimensions=document_dimensions,
                                    box_type=Textract_Types.TABLE,
                                    page_number=page_number))

                if Textract_Types.CELL in overlay_features:
                    for _, row in enumerate(table.rows):
                        for _, cell in enumerate(row.cells):
                            if cell:
                                bounding_box_list.append(
                                    BoundingBox(geometry=cell.geometry,
                                                document_dimensions=document_dimensions,
                                                box_type=Textract_Types.CELL,
                                                page_number=page_number))

    return bounding_box_list
