"""
Represents a single :class:`TableCell:class:` object. The :class:`TableCell` objects contains information such as:

* The position info of the cell within the encompassing Table
* Properties such as merged-cells span
* A hierarchy of words contained within the TableCell (optional)
* Page information
* Confidence of entity detection.
"""

import os
from typing import List

from textractor.entities.word import Word
from textractor.exceptions import InputError
from textractor.entities.bbox import BoundingBox
from textractor.visualizers.entitylist import EntityList
from textractor.entities.document_entity import DocumentEntity
from textractor.entities.selection_element import SelectionElement

from textractor.data.constants import (
    IS_COLUMN_HEAD,
    IS_MERGED_CELL,
    IS_SECTION_TITLE_CELL,
    IS_SUMMARY_CELL,
    IS_TITLE_CELL,
    IS_FOOTER_CELL,
)
from textractor.data.constants import TextTypes


class TableCell(DocumentEntity):
    """
    To create a new TableCell object we need the following:

    :param entity_id: Unique id of the TableCell object
    :param bbox: Bounding box of the entity
    :param row_index: Row index of position of cell within the table
    :param col_index: Column index of position of cell within the table
    :param row_span: How many merged cells does the cell spans horizontally (1 means no merged cells)
    :param col_span: How mant merged cells does the cell spand vertically (1 means no merged cells)
    :param confidence: Confidence out of 100 with which the Cell was detected.
    """

    def __init__(
        self,
        entity_id: str,
        bbox: BoundingBox,
        row_index: int,
        col_index: int,
        row_span: int,
        col_span: int,
        confidence: float = 0,
        is_column_header: bool = False
    ):

        super().__init__(entity_id, bbox)
        self._row_index: int = int(row_index)
        self._col_index: int = int(col_index)
        self._row_span: int = int(row_span)
        self._col_span: int = int(col_span)
        self._words: List[Word] = []
        self.confidence = confidence / 100
        self._page = None
        self._page_id = None
        self._is_column_header = is_column_header
        # this gets populated when cells are added to a table using the `add_cells` method
        # or when cells are attributed to a table with table.cells = [TableCell]
        self._parent_table_id = None
        self.parent_cell_id = None
        self.siblings: List[TableCell] = []

    @property
    def is_column_header(self):
        return self._is_column_header

    @property
    def page(self):
        """
        :return: Returns the page number of the page the :class:`TableCell` entity is present in.
        :rtype: int
        """
        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the :class:`TableCell` entity.

        :param page_num: Page number where the TableCell entity exists.
        :type page_num: int
        """
        self._page = page_num

    @property
    def page_id(self) -> str:
        """
        :return: Returns the Page ID attribute of the page which the entity belongs to.
        :rtype: str
        """
        return self._page_id

    @page_id.setter
    def page_id(self, page_id: str):
        """
        Sets the Page ID of the TableCell entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """
        self._page_id = page_id

    @property
    def row_index(self):
        """
        :return: Returns the row index of the cell in the :class:`Table`.
        :rtype: int
        """
        return self._row_index

    @row_index.setter
    def row_index(self, index: int):
        """
        Sets the row index of the cell in the Table.

        :param index: Row value of the cell in the Table.
        :type index: int
        """
        self._row_index = index

    @property
    def col_index(self):
        """
        :return: Returns the column index of the cell in the Table.
        :rtype: int
        """
        return self._col_index

    @col_index.setter
    def col_index(self, index: int):
        """
        Sets the column index of the cell in the :class:`Table`.

        :param index: Column value of the cell in the Table.
        :type index: int
        """
        self._col_index = index

    @property
    def row_span(self):
        """
        :return: Returns the row span of the cell in the :class:`Table`.
        :rtype: int
        """
        return self._row_span

    @property
    def col_span(self):
        """
        :return: Returns the column span of the cell in the :class:`Table`.
        :rtype: int
        """
        return self._col_span

    @property
    def words(self):
        """
        Returns all the Word objects present in the :class:`TableCell`.

        :return words: List of Word objects, each representing a word within the TableCell.
        :rtype: list
        """
        return EntityList(self._words)

    @words.setter
    def words(self, words: List[Word]):
        """
        Add Word objects to the :class:`TableCell`.

        :param words: List of Word objects, each representing a word within the TableCell. No specific ordering is assumed as it is ordered internally.
        :type words: list
        """
        self._words = words

    @property
    def checkboxes(self):
        output = []
        for child in self._children:
            if isinstance(child, SelectionElement):
                output.append(child)
        return output


    @property
    def text(self) -> str:
        """Returns the text in the cell as one space-separated string

        :return: Text in the cell
        :rtype: str
        """
        return " ".join([" ".join([str(c) for c in self.checkboxes]), " ".join([w.text for w in self.words])])

    @property
    def table_id(self):
        """
        :return: Returns the ID of the :class:`Table` the TableCell belongs to.
        :rtype: str
        """
        return self._parent_table_id

    @table_id.setter
    def table_id(self, id: str):
        """
        Sets the ID of the Table the TableCell belongs to.

        :param id: ID of the Table
        :type id: str
        """
        self._parent_table_id = id

    def _update_response_metadata(self, metadata: list):
        """
        Updates metadata of :class:`TableCell` to include information stating if cell is of a special type.

        :param metadata: List of string types that match different cell types
        :type metadata: List
        """
        self.metadata[IS_COLUMN_HEAD] = True if "COLUMN_HEADER" in metadata else False
        self.metadata[IS_MERGED_CELL] = True if "MERGED_CELL" in metadata else False
        self.metadata[IS_SECTION_TITLE_CELL] = (
            True if "SECTION_TITLE" in metadata else False
        )
        self.metadata[IS_SUMMARY_CELL] = True if "SUMMARY_CELL" in metadata else False
        self.metadata[IS_TITLE_CELL] = True if "FLOATING_TITLE" in metadata else False
        self.metadata[IS_FOOTER_CELL] = True if "FLOATING_FOOTER" in metadata else False

    def _get_merged_cell_range(self):
        """
        :return: Returns the first row, first column, last row and last column of the merged cell.
        :rtype: Tuple[float]
        """
        if self.metadata[IS_MERGED_CELL]:
            rows = set()
            cols = set()
            for cell in self.siblings:
                rows.add(cell.row_index)
                cols.add(cell.col_index)
            return min(rows), min(cols), max(rows), max(cols)
        else:
            return self.row_index, self.col_index, self.row_index, self.col_index

    def get_words_by_type(self, text_type: TextTypes = TextTypes.PRINTED) -> List[Word]:
        """
        Returns list of :class:`Word` entities that match the input text type.

        :param text_type: TextTypes.PRINTED or TextTypes.HANDWRITING
        :type text_type: TextTypes
        :return: Returns list of Word entities that match the input text type.
        :rtype: EntityList
        """
        if not isinstance(text_type, TextTypes):
            raise InputError(
                "text_type parameter should be of TextTypes type. Find input choices from textractor.data.constants"
            )

        return EntityList([word for word in self.words if word.text_type == text_type])

    def merge_direction(self):
        """
        :return:    Determines if the merged cell is a row or column merge.
                    Returns 0 if row merge, 1 if column merge and 2 if both and None if there is no merge.
        :rtype: int, str
        """
        if self.metadata[IS_MERGED_CELL]:
            rows = set()
            columns = set()
            for cell in self.siblings:
                rows.add(cell.row_index)
                columns.add(cell.col_index)
            if len(rows) > 1 and len(columns) > 1:
                return 2, "Row and Column"
            elif len(rows) > 1:
                return 1, "Column"
            elif len(columns) > 1:
                return 0, "Row"
            else:
                self.metadata[IS_MERGED_CELL] = False
        return None, "None"

    def __repr__(self):
        """
        :return: String representation of the TableCell entity.
        :rtype: str
        """
        if self.metadata.get(IS_MERGED_CELL, False):
            entities = {
                (cell.row_index, cell.col_index): sorted(
                    cell.words + cell.children, key=lambda x: (x.bbox.x, x.bbox.y)
                )
                for cell in sorted(
                    self.siblings, key=lambda x: (x.row_index, x.col_index)
                )
            }

            rows = set(sorted([cell_key[0] for cell_key in entities.keys()]))
            cols = set(sorted([cell_key[1] for cell_key in entities.keys()]))

            entity_repr = []
            for row in rows:
                for col in cols:
                    entity_repr.append(
                        " ".join([entity.__repr__() for entity in entities[(row, col)]])
                    )
                    entity_repr.append(" ")
                entity_repr.append(os.linesep)
            entity_repr = "".join(entity_repr)

        else:
            entities = self.words + self.children
            entity_repr = " ".join([entity.__repr__() for entity in entities])

        entity_string = f"<Cell: ({self.row_index},{self.col_index}), Span: ({self.row_span}, {self.col_span}), Column Header: { self.is_column_header}, "
        entity_string += (
            f"MergedCell: {self.metadata.get(IS_MERGED_CELL, False)}>  " + entity_repr
        )
        return entity_string
