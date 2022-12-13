"""
Represents a :class:`Table` entity within the document.
Tables are hierarchical objects composed of :class:`TableCell` objects, which *implicitly* form columns and rows.

:class:`Table` object contains associated metadata within it. They include :class:`TableCell` information, headers, page number and 
page ID of the page within which it exists in the document. 
"""

import logging
import os
import xlsxwriter
from copy import deepcopy

try:
    from pandas import DataFrame
except ImportError:
    logging.info("pandas library is required for exporting tables to DataFrame objects")

from typing import List, Dict

from textractor.exceptions import InputError
from textractor.entities.bbox import BoundingBox
from textractor.entities.table_cell import TableCell
from textractor.visualizers.entitylist import EntityList
from textractor.entities.document_entity import DocumentEntity
from textractor.utils.geometry_util import get_indices
from textractor.data.constants import SimilarityMetric, TextTypes, CellTypes
from textractor.data.constants import (
    IS_COLUMN_HEAD,
    IS_MERGED_CELL,
)
from textractor.utils.search_utils import SearchUtils, get_metadata_attr_name


class Table(DocumentEntity):
    """
    To create a new :class:`Table` object we need the following:

    :param entity_id:           Unique identifier of the table.
    :param bbox:                Bounding box of the table.
    """

    def __init__(self, entity_id, bbox: BoundingBox):
        super().__init__(entity_id, bbox)
        self.table_cells: List[TableCell] = []
        self.column_headers: Dict[str, List[TableCell]] = {}
        self._page = None
        self._page_id = None

    @property
    def words(self):
        """
        Returns all the :class:`Word` objects present in the :class:`Table`.

        :return words: List of Word objects, each representing a word within the Table.
        :rtype: EntityList[Word]
        """

        all_words = sum([cell.words for cell in self.table_cells], [])

        if not all_words:
            logging.info("Table contains no word entities.")

        return EntityList(all_words)

    @property
    def page(self):
        """
        :return: Returns the page number of the page the Table entity is present in.
        :rtype: int
        """

        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the Table entity.

        :param page_num: Page number where the Table entity exists.
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
        Sets the Page ID of the Table entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """

        self._page_id = page_id

    @property
    def column_count(self):
        return max(list(self._get_table_cells(row_wise=False, column_wise=True).keys()))

    @property
    def row_count(self):
        return max(list(self._get_table_cells().keys()))

    def get_words_by_type(self, text_type=TextTypes.PRINTED):
        """
        Returns list of :class:`Word` entities that match the input text type.

        :param text_type: TextTypes.PRINTED or TextTypes.HANDWRITING
        :type text_type: TextTypes

        :return: Returns list of Word entities that match the input text type.
        :rtype: EntityList[Word]
        """
        if not isinstance(text_type, TextTypes):
            raise InputError(
                "text_type parameter should be of TextTypes type. Find input choices from textractor.data.constants"
            )

        if not self.words:
            return []

        return EntityList([word for word in self.words if word.text_type == text_type])

    def get_table_range(self):
        """
        :return: Returns the number of rows and columns in the table.
        :rtype: Tuple(int)
        """

        return self.row_count, self.column_count

    def strip_headers(self):
        """
        Returns a new :class:`Table` object after removing all cells that are marked as column headers in the table from the API response.

        :return: Table object after removing the headers.
        :rtype: Table
        """

        table_cells = deepcopy(self.table_cells)
        table_cells = [
            cell for cell in table_cells if not cell.metadata[IS_COLUMN_HEAD]
        ]

        old_rows = set([cell.row_index for cell in table_cells])
        new_rows = set(range(1, len(old_rows) + 1))

        new_row_mapping = dict(zip(old_rows, new_rows))

        new_table_cells = []
        for cell in table_cells:
            cell.row_index = new_row_mapping[cell.row_index]
            new_table_cells.append(cell)

        new_table = deepcopy(self)
        new_table.add_cells(new_table_cells)

        return new_table

    def add_cells(self, cells: List[TableCell]):
        """
        Add :class:`TableCell` objects to the :class:`Table`.
        This function does not check the integrity of the table after the cells are added.

        :param cells: List of TableCell objects, each representing a single cell within the table.
                      No specific ordering is assumed since it is implicitly ordered by row and column index.
        :type cells: list
        """

        for cell in cells:
            cell.table_id = self.id
        self.table_cells = cells
        self.table_cells = sorted(
            self.table_cells, key=lambda x: (x.row_index, x.col_index)
        )

    def _get_table_cells(
        self, row_wise: bool = True, column_wise: bool = False
    ) -> Dict[int, List[TableCell]]:
        """
        Return a dictionary of row_number/column_number : List[TableCell] (in order) for the table entity. Only one of the 2 params should be set to True. default: row_wise=True, column_wise=False.

        :param row_wise: True if format of dict `{row_number : List[TableCell]}`. Else False.
        :type row_wise: bool
        :param column_wise: True if format of dict `{row_number : List[TableCell]}`. Else False.
        :type column_wise: bool

        :return: Returns a dictionary of format `{row_number/column_number : List[TableCell]}`
        :rtype: Dict[int, List[TableCell]]
        """

        if (row_wise and column_wise) or (not row_wise and not column_wise):
            logging.warning(
                "Both parameters cannot be equal. Choose one (row_wise=True or column_wise=True)"
            )
            return {}

        attribute = "row_index" if row_wise else "col_index"
        alt_attribute = "col_index" if row_wise else "row_index"
        sorted_cells = {}
        for cell in self.table_cells:
            index = getattr(cell, attribute)
            if index in sorted_cells.keys():
                sorted_cells[index].append(cell)
            else:
                sorted_cells[index] = [cell]

        for key in sorted_cells.keys():
            sorted_cells[key] = sorted(
                sorted_cells[key], key=lambda x: getattr(x, alt_attribute)
            )

        return sorted_cells

    def get_cells_by_type(self, cell_type: CellTypes = CellTypes.COLUMN_HEADER):
        """
        Returns a dictionary of column_header (str) : List[TableCell] (in order).

        :param cell_type: supports CellTypes.COLUMN_HEADER as of now, will support SECTION_TITLE, FLOATING_TITLE,
                            FLOATING_FOOTER, SUMMARY_CELL in the future.
        :type cell_type: CellTypes

        :return: {column_header (str) : List[TableCell]}
        :rtype: Dict[str, List[TableCell]]
        """
        if not isinstance(cell_type, CellTypes):
            raise InputError(
                "cell_type parameter should be of CellTypes type. Find input choices from textractor.data.constants"
            )

        cell_property = get_metadata_attr_name(cell_type)
        if cell_property == "":
            logging.info("No cells of this type exist.")
            return []
        table_cells_by_id = {cell.id: cell for cell in self.table_cells}
        filtered_cells = {}

        for cell in self.table_cells:
            if cell.metadata[cell_property]:
                if not cell.metadata[IS_MERGED_CELL]:
                    header = " ".join([word.text for word in cell.words])
                    filtered_cells[header] = [cell]
                else:
                    all_merge_cells = sorted(
                        cell.siblings, key=lambda x: x.bbox.x + x.bbox.y
                    )
                    all_words = sum([cell.words for cell in all_merge_cells], [])
                    header = " ".join([word.text for word in all_words])
                    filtered_cells[header] = all_merge_cells

        if cell_type == CellTypes.COLUMN_HEADER and not self.column_headers:
            self.column_headers = filtered_cells

            if not self.column_headers:
                logging.info("Column headers have not been identified in this table.")

        return filtered_cells

    def get_columns_by_name(
        self,
        column_names,
        similarity_metric=SimilarityMetric.COSINE,
        similarity_threshold=0.6,
    ):
        """
        Returns a dictionary of format {column_name : List[TableCell]} for the column names listed in param column_names.

        :param column_names: List of column names of columns to be extracted from table.
        :type column_names: list
        :param similarity_metric: 'cosine', 'euclidean' or 'levenshtein'. 'cosine' is chosen as default.
        :type similarity_metric: str
        :param similarity_threshold: Measure of how similar document key is to queried key. default=0.6
        :type similarity_threshold: float

        :return: Returns a new Table consisting of columns passed in column_names.
        :rtype: Table
        """
        if not isinstance(similarity_metric, SimilarityMetric):
            raise InputError(
                "similarity_metric parameter should be of SimilarityMetric type. Find input choices from textractor.data.constants"
            )

        table_columns = (
            self.column_headers.keys()
            if self.column_headers
            else self.get_cells_by_type().keys()
        )
        column_indices = set()
        chosen_columns = []
        similarity_threshold = (
            similarity_threshold
            if similarity_metric == SimilarityMetric.COSINE
            else -(similarity_threshold)
        )
        for column in column_names:
            for table_column in table_columns:
                similarity = SearchUtils.get_word_similarity(
                    column, table_column, similarity_metric
                )
                similarity = (
                    similarity
                    if similarity_metric == SimilarityMetric.COSINE
                    else -(similarity)
                )

                if similarity > similarity_threshold:
                    chosen_columns.append(table_column)

        for col in chosen_columns:
            for cell in self.column_headers[col]:
                column_indices.add(cell.col_index)

        table_cells = deepcopy(self.table_cells)
        table_cells = [cell for cell in table_cells if cell.col_index in column_indices]
        new_cols = set(range(1, len(column_indices) + 1))
        new_col_mapping = dict(zip(column_indices, new_cols))

        new_table_cells = []
        for cell in table_cells:
            cell.col_index = new_col_mapping[cell.col_index]
            new_table_cells.append(cell)

        new_table = deepcopy(self)
        new_table.add_cells(new_table_cells)

        return new_table

    def __getitem__(self, key):
        """
        Returns a new :class:`Table` with selected rows and columns. The table can be filtered using numpy indexing.
        One-indexing followed. index 0 => automatically converted to 1.

        :param key: Tuple[rows, columns] with numpy indexing
                    Eg: table[1:4, :] returns all columns of the first 3 rows of the Table.

        :return: Returns a new Table with selected rows and columns.
        :rtype: Table
        """

        np_rows, np_cols = key

        if np_rows == np_cols and np_rows == slice(None, None, None):
            return self

        max_rows, max_cols = self.get_table_range()

        row_index = (
            str(np_rows)
            if isinstance(np_rows, int)
            else ":".join([str(np_rows.start), str(np_rows.stop), str(np_rows.step)])
        )
        col_index = (
            str(np_cols)
            if isinstance(np_cols, int)
            else ":".join([str(np_cols.start), str(np_cols.stop), str(np_cols.step)])
        )

        rows = get_indices(row_index, max_rows)
        cols = get_indices(col_index, max_cols)

        table_rows = self._get_table_cells(row_wise=True, column_wise=False)

        table_by_rows = {key - 1: table_rows[key] for key in table_rows.keys()}

        filtered_rows = {}
        for row_number in rows:
            if row_number in table_by_rows.keys():
                row_data = table_by_rows[row_number]
                col_cells = []
                for col_number in cols:
                    col_cells.append(row_data[col_number])
                filtered_rows[row_number] = col_cells

        new_table_cells = _get_new_table_cells(rows, filtered_rows)

        new_table = deepcopy(self)
        new_table.add_cells(new_table_cells)

        return new_table


    def to_pandas(self):
        """Converts the table to a pandas DataFrame

        :return: DataFrame for the table
        :rtype: DataFrame
        """

        table = [["" for _ in range(self.column_count)] for _ in range(self.row_count)]
        for cell in self.table_cells:
            table[cell.row_index - 1][cell.col_index - 1] = cell.text

        return DataFrame(table)

    def to_csv(self) -> str:
        """Returns the table in the Comma-Separated-Value (CSV) format

        :return: Table as a CSV string.
        :rtype: str
        """
        return self.to_pandas().to_csv()

    def to_excel(self, filepath=None, workbook=None, save_workbook=True):
        """
        Export the Table Entity as an excel document. Advantage of excel over csv is that it can accommodate merged cells that we see so often with Textract documents.

        :param filepath: Path to store the exported Excel file
        :type filepath: str
        :param workbook: if xlsxwriter workbook is passed to the function, the table is appended to the last sheet of that workbook.
        :type workbook: xlsxwriter.Workbook
        :param save_workbook: Flag to save_notebook. If False, it is returned by the function.
        :type save_workbook: bool

        :return: Returns a workbook if save_workbook is False. Else, saves the .xlsx file in the filepath if was initialized with.
        :rtype: xlsxwriter.Workbook
        """
        if workbook is None:
            if filepath is not None:
                workbook = xlsxwriter.Workbook(filepath)
            else:
                logging.error("You need to provide a filepath or a workbook")

        worksheet = workbook.add_worksheet()

        for cell in self.table_cells:
            cell_content = cell.__repr__().split(">")[1][1:]
            if cell.metadata[IS_MERGED_CELL]:
                first_row, first_col, last_row, last_col = cell._get_merged_cell_range()
                worksheet.merge_range(
                    first_row - 1,
                    first_col - 1,
                    last_row - 1,
                    last_col - 1,
                    cell_content,
                )
            else:
                worksheet.write_string(
                    cell.row_index - 1, cell.col_index - 1, cell_content
                )

        if save_workbook:
            workbook.close()

        else:
            return workbook

    def to_txt(self):
        table = [["" for _ in range(self.column_count)] for _ in range(self.row_count)]
        for cell in self.table_cells:
            table[cell.row_index - 1][cell.col_index - 1] = cell.text

        return os.linesep.join(["\t".join(r) for r in table])

    def __repr__(self):
        return os.linesep.join(
            [
                "Table",
                f"Rows - {self.row_count}",
                f"Columns - {self.column_count}",
                f"Cells - {len(self.table_cells)}",
                f"Merged Cells - {len([c for c in self.table_cells if c.metadata[IS_MERGED_CELL]])}",
            ]
        )

def _get_new_table_cells(rows, filtered_rows):
    """
    Modifies indexing of :class:`TableCell` entities according to the new filtered table format.

    :param rows: List containing the filtered row indices from original table.
    :type rows: list
    :param filtered_rows: Dictionary containing filtered rows and respective cells. Format row : List[TableCell]
    :type filtered_rows: dict

    :return: List of modified TableCell objects with new indexing.
    :rtype: List
    """

    rows = sorted([row + 1 for row in rows])
    cols = sorted(list(set([cell.col_index for cell in filtered_rows[rows[0]]])))

    new_row_range = list(range(1, len(rows) + 1))
    new_col_range = list(range(1, len(filtered_rows[rows[0]]) + 1))

    row_index_map = dict(zip(rows, new_row_range))
    col_index_map = dict(zip(cols, new_col_range))

    all_cells = sum(list(filtered_rows.values()), [])
    old_cells_dict = {(cell.row_index, cell.col_index): cell for cell in all_cells}

    new_cells_dict = {
        (row_index_map[cell.row_index], col_index_map[cell.col_index]): TableCell(
            entity_id=cell.id,
            bbox=cell.bbox,
            row_index=row_index_map[cell.row_index],
            col_index=col_index_map[cell.col_index],
            row_span=1,
            col_span=1,
            confidence=cell.confidence,
        )
        for cell in old_cells_dict.values()
    }

    for cell in old_cells_dict.values():
        new_cell_siblings = []
        cell_words = []
        cell_children = []

        cell_row, cell_col = row_index_map.get(cell.row_index), col_index_map.get(
            cell.col_index
        )
        new_cells_dict[(cell_row, cell_col)].metadata = cell.metadata

        if (cell_row, cell_col) in new_cells_dict.keys() and not cell.metadata[
            IS_MERGED_CELL
        ]:
            new_cells_dict[(cell_row, cell_col)].words = list(cell.words)
            new_cells_dict[(cell_row, cell_col)].add_children(list(cell.children))

        else:
            if (cell_row, cell_col) in new_cells_dict.keys() and not new_cells_dict[
                (cell_row, cell_col)
            ].siblings:
                for subcell in cell.siblings:
                    cell_words.extend(list(subcell.words))
                    cell_children.extend(list(subcell.children))

                    new_row, new_col = row_index_map.get(
                        subcell.row_index
                    ), col_index_map.get(subcell.col_index)

                    if (new_row, new_col) in new_cells_dict.keys():
                        new_cells_dict[(new_row, new_col)].metadata = subcell.metadata
                        new_cell_siblings.append(new_cells_dict[(new_row, new_col)])

                new_cells_dict[(cell_row, cell_col)].siblings = new_cell_siblings
                new_cells_dict[(cell_row, cell_col)].words = cell_words
                new_cells_dict[(cell_row, cell_col)].add_children(cell_children)

                for sibling in new_cells_dict[(cell_row, cell_col)].siblings:
                    sibling.siblings = new_cell_siblings
            else:
                continue

    return list(new_cells_dict.values())
