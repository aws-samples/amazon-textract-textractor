"""
Represents a :class:`Table` entity within the document.
Tables are hierarchical objects composed of :class:`TableCell` objects, which *implicitly* form columns and rows.

:class:`Table` object contains associated metadata within it. They include :class:`TableCell` information, headers, page number and 
page ID of the page within which it exists in the document. 
"""

import itertools
import logging
import os
import uuid
import xlsxwriter
from copy import deepcopy


from typing import List, Dict

from textractor.exceptions import InputError, MissingDependencyException
from textractor.entities.bbox import BoundingBox
from textractor.entities.table_cell import TableCell
from textractor.visualizers.entitylist import EntityList
from textractor.entities.document_entity import DocumentEntity
from textractor.entities.selection_element import SelectionElement
from textractor.entities.table_title import TableTitle
from textractor.entities.table_footer import TableFooter
from textractor.entities.word import Word
from textractor.utils.geometry_util import get_indices
from textractor.data.constants import SimilarityMetric, TextTypes, CellTypes, TableTypes
from textractor.data.constants import IS_COLUMN_HEAD, IS_MERGED_CELL
from textractor.utils.search_utils import SearchUtils, get_metadata_attr_name
from textractor.utils.text_utils import group_elements_horizontally, linearize_children
from textractor.data.text_linearization_config import TextLinearizationConfig
from textractor.data.html_linearization_config import HTMLLinearizationConfig


class Table(DocumentEntity):
    """
    To create a new :class:`Table` object we need the following:

    :param entity_id:           Unique identifier of the table.
    :param bbox:                Bounding box of the table.
    """

    def __init__(self, entity_id, bbox: BoundingBox):
        super().__init__(entity_id, bbox)
        self.table_cells: List[TableCell] = []
        self._column_headers: Dict[str, List[TableCell]] = {}
        self._title: TableTitle = None
        self._footers: TableFooter = []
        self._table_type: TableTypes = TableTypes.UNKNOWN
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
    def table_type(self):
        """
        :return: Returns the table type.
        :rtype: TableTypes
        """

        return self._table_type

    @table_type.setter
    def table_type(self, table_type: TableTypes):
        """
        Sets the table type attribute of the Table entity.

        :param title: Type of the Table entity.
        :type title: TableTypes
        """

        self._table_type = table_type

    @property
    def title(self):
        """
        :return: Returns the table title.
        :rtype: TableTitle
        """

        return self._title

    @title.setter
    def title(self, title: TableTitle):
        """
        Sets the table title attribute of the Table entity.

        :param title: Title of the Table entity.
        :type title: TableTitle
        """

        self._title = title

    @property
    def footers(self):
        """
        :return: Returns the table footers.
        :rtype: List[TableFooter]
        """

        return self._footers

    @footers.setter
    def footers(self, footers: List[TableFooter]):
        """
        Sets the footers attribute of the Table entity.

        :param footers: Footers of the Table entity.
        :type footers: List[TableFooter]
        """

        self._footers = footers

    @property
    def column_headers(self) -> Dict[str, List[TableCell]]:
        """
        :return: Returns the column headers of the Table entity.
        :rtype: Dict[str, List[TableCell]]
        """

        return self._column_headers

    @column_headers.setter
    def column_headers(self, column_headers: Dict[str, List[TableCell]]):
        """
        Sets the column headers of the Table entity

        :param column_headers: Column headers
        :type column_headers: Dict[str, List[TableCell]]
        """

        self._column_headers = column_headers

    @property
    def page_id(self) -> str:
        """
        :return: Returns the Page ID attribute of the page which the entity belongs to.
        :rtype: str
        """

        return self._page_id

    @property
    def checkboxes(self) -> List[SelectionElement]:
        checkboxes = []
        for cell in self.table_cells:
            checkboxes.extend(cell.checkboxes)
        return checkboxes

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

    def strip_headers(
        self,
        column_headers: bool = True,
        in_table_title: bool = False,
        section_titles=False,
    ):
        """
        Returns a new :class:`Table` object after removing all cells that are marked as column headers in the table from the API response.

        :param column_headers: Remove the column headers
        :type column_headers: bool
        :param in_table_title: Remove the in-table titles
        :type in_table_title: bool
        :param section_titles: Remove the in-table section titles
        :type section_titles: bool

        :return: Table object after removing the headers.
        :rtype: Table
        """

        table_cells = deepcopy(self.table_cells)
        table_cells = [
            cell
            for cell in table_cells
            if not (
                (cell.is_column_header and column_headers)
                or (cell.is_title and in_table_title)
                or (cell.is_section_title and section_titles)
            )
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

        if cell_type == CellTypes.COLUMN_HEADER and not self._column_headers:
            self._column_headers = filtered_cells

            if not self._column_headers:
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
            self._column_headers.keys()
            if self._column_headers
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
            for cell in self._column_headers[col]:
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

        :param key: Tuple[rows, columns] with numpy indexing
                    Eg: table[0:3, :] returns all columns of the first 3 rows of the Table.

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

        filtered_rows = {}
        for row_number in rows:
            if row_number + 1 in table_rows.keys():
                row_data = table_rows[row_number + 1]
                col_cells = []
                for col_number in cols:
                    col_cells.append(row_data[col_number])
                filtered_rows[row_number] = col_cells

        new_table_cells = _get_new_table_cells(rows, filtered_rows)

        new_table = deepcopy(self)
        new_table.add_cells(new_table_cells)

        return new_table

    def to_pandas(self, use_columns=False, config: TextLinearizationConfig = TextLinearizationConfig()):
        """
        Converts the table to a pandas DataFrame

        :param use_columns: If the first row of the table is made of column headers, use them for the pandas dataframe. Only supports single row header.
        :param config: Text linearization configuration object for the table content
        :return:
        """
        try:
            from pandas import DataFrame
        except ImportError:
            raise MissingDependencyException(
                "pandas library is required for exporting tables to DataFrame objects or markdown"
            )

        rows = sorted([(key, list(group)) for key, group in itertools.groupby(
            self.table_cells, key=lambda cell: cell.row_index
        )], key=lambda r: r[0])
        row_offset = 0

        columns = None
        processed_cells = set()
        if use_columns:
            # Try to automatically get the columns if they are in the first row
            columns = [[] for _ in range(self.column_count)]
            is_header_count = 0
            for _, row in rows:
                if not any([c.is_column_header for c in row]):
                    # There is not header in that row, we are done
                    break
                for i, cell in enumerate(row):
                    if (
                        cell not in processed_cells or
                        config.table_duplicate_text_in_merged_cells or
                        config.table_flatten_headers
                    ):
                        if cell.siblings:
                            # This handles the edge case where we are flattening the headers
                            # so we want to duplicate the cell text but only in its first row
                            first_row, _, _, _ = cell._get_merged_cell_range()
                            if cell in processed_cells and first_row != cell.row_index:
                                continue
                            children = []
                            for sib in cell.siblings:
                                if sib.is_column_header:
                                    is_header_count += 1
                                children.extend(sib.children)
                                processed_cells.add(sib)
                            text, _ = linearize_children(children, config=config, no_new_lines=True)
                            columns[i].append(text)
                        else:
                            if cell.is_column_header:
                                is_header_count += 1
                            text = cell.get_text(config)
                            columns[i].append(text)
                    elif config.table_cell_empty_cell_placeholder:
                        columns[i].append(config.table_cell_empty_cell_placeholder)
                    else:
                        columns[i].append("")
                row_offset += 1
            # If we have the correct number of column and at least half the row is tagged as a header
            if len(columns) == self.column_count and is_header_count / len(columns) >= config.table_column_header_threshold:
                use_columns = True
            else:
                use_columns = False
                logging.info(
                    f"The number of column header cell do not match the column count, ignoring them, {len(columns)} vs {self.column_count}"
                )

        if columns and any([c for c in columns]) and config.table_flatten_headers:
            columns = ["".join(c) for c in columns]
            table = [columns]
        elif columns and any([c for c in columns]):
            # We reset the row offset as only the first line will be taken as header
            columns = [c[0] for c in columns]
            table = [columns]
            row_offset = 1
        else:
            table = []

        for _, row in rows[row_offset:]:
            table.append([])
            for cell in row:
                table[-1].append("")
                if cell.siblings:
                    children = []
                    first_row, first_col, last_row, last_col = cell._get_merged_cell_range()
                    if (cell.col_index == first_col and cell.row_index == first_row) or config.table_duplicate_text_in_merged_cells:
                        for sib in cell.siblings:
                            children.extend(sib.children)
                            processed_cells.add(sib)
                        text, _ = linearize_children(children, config=config, no_new_lines=True)
                    elif cell.row_index == first_row and config.table_cell_left_merge_cell_placeholder:
                        text = config.table_cell_left_merge_cell_placeholder
                    elif cell.col_index == first_col and config.table_cell_top_merge_cell_placeholder:
                        text = config.table_cell_top_merge_cell_placeholder
                    elif cell.col_index != first_col and cell.row_index != first_row and config.table_cell_cross_merge_cell_placeholder:
                        text = config.table_cell_cross_merge_cell_placeholder
                    else:
                        text = config.table_cell_empty_cell_placeholder if config.table_cell_empty_cell_placeholder else ""
                else:
                    text = cell.get_text(config)
                table[-1][cell.col_index - 1] = text if text or not config.table_cell_empty_cell_placeholder else config.table_cell_empty_cell_placeholder

        return DataFrame(
            table[1:] if use_columns else table,
            columns=columns if use_columns else None,
        )

    def to_csv(self, use_columns = False, config: TextLinearizationConfig = TextLinearizationConfig()) -> str:
        """Returns the table in the Comma-Separated-Value (CSV) format

        :param use_columns: If the first row of the table is made of column headers, use them for the pandas dataframe. Only supports single row header.
        :param config: Text linearization configuration object for the table content
        :return: Table as a CSV string.
        :rtype: str
        """
        return self.to_pandas(use_columns=use_columns, config=config).to_csv()

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

        merged_cells = set()
        for cell in self.table_cells:
            cell_content = cell.__repr__().split(">")[1][1:]
            if cell.metadata[IS_MERGED_CELL]:
                first_row, first_col, last_row, last_col = cell._get_merged_cell_range()
                if (first_row, first_col, last_row, last_col) in merged_cells:
                    continue
                else:
                    merged_cells.add((first_row, first_col, last_row, last_col))
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

    def to_html(self) -> str:
        """Returns the table in the HTML format

        :return: Table as an HTML string.
        :rtype: str
        """
        
        return self.get_text(HTMLLinearizationConfig())

    def get_text_and_words(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ):
        local_config = deepcopy(config)
        words_ = self.words
        # If no text, return empty string
        if not words_ and local_config.table_remove_column_headers:
            return "", []

        # If not many words, only return text
        if len(words_) < local_config.table_min_table_words:
            return linearize_children(words_, config=config)

        words = [Word(str(uuid.uuid4()), self.bbox, local_config.table_prefix)] if local_config.table_prefix else []
        rows = sorted([(key, list(group)) for key, group in itertools.groupby(
            self.table_cells, key=lambda cell: cell.row_index
        )], key=lambda r: r[0])
        processed_cells = set()
        # Fill the table
        row_offset = 0
        if local_config.table_flatten_headers:
            columns = [[] for _ in range(len(rows[0][1]))]
            columns_bbox = [[] for _ in range(len(rows[0][1]))]
            for _, row in rows:
                if not any([c.is_column_header for c in row]):
                    # There is not header in that row, we are done
                    break
                for i, cell in enumerate(row):
                    if (
                        cell not in processed_cells or
                        local_config.table_duplicate_text_in_merged_cells or
                        local_config.table_flatten_headers
                    ):
                        if cell.siblings:
                            # This handles the edge case where we are flattening the headers
                            # so we want to duplicate the cell text but only in its first row
                            first_row, _, _, _ = cell._get_merged_cell_range()
                            if cell in processed_cells and first_row != cell.row_index:
                                continue
                            children = []
                            for sib in cell.siblings:
                                children.extend(sib.children)
                                processed_cells.add(sib)
                            _, words = linearize_children(children, config=config, no_new_lines=True)
                            columns[i].extend(words)
                            columns_bbox[i].append(cell.bbox)
                        else:
                            _, words = cell.get_text_and_words(config)
                            columns[i].extend(words)
                            columns_bbox[i].append(cell.bbox)
                    elif local_config.table_cell_empty_cell_placeholder:
                        columns[i].append(Word(str(uuid.uuid4()), cell.bbox, local_config.table_cell_empty_cell_placeholder))
                row_offset += 1
            if columns:
                columns_bbox = [BoundingBox.enclosing_bbox(cbb) for cbb in columns_bbox]
                if local_config.table_row_prefix and local_config.add_prefixes_and_suffixes_as_words:
                    words.append(Word(str(uuid.uuid4()), BoundingBox.enclosing_bbox(columns_bbox), local_config.table_row_prefix, is_structure=True))
                for i, column in enumerate(columns):
                    words.append(
                        Word(
                            str(uuid.uuid4()),
                            columns_bbox[i],
                            local_config.table_cell_header_prefix
                            if local_config.table_cell_header_prefix
                            else local_config.table_cell_prefix,
                            is_structure=True
                        )
                    )
                    words.extend(column)
                    words.append(
                        Word(
                            str(uuid.uuid4()),
                            columns_bbox[i],
                            local_config.table_cell_header_suffix
                            if local_config.table_cell_header_suffix
                            else local_config.table_cell_suffix,
                            is_structure=True
                        )
                    )
                if local_config.table_row_suffix and local_config.add_prefixes_and_suffixes_as_words:
                    words.append(Word(str(uuid.uuid4()), columns_bbox, local_config.table_row_suffix, is_structure=True))
        for _, cells in rows[row_offset:]:
            if local_config.table_row_prefix and local_config.add_prefixes_and_suffixes_as_words:
                words.append(Word(str(uuid.uuid4()), BoundingBox.enclosing_bbox(cells), local_config.table_row_prefix, is_structure=True))
            for cell in sorted(cells, key=lambda c: c.col_index):
                # Siblings includes the current cell
                if cell.siblings:
                    first_row, first_col, last_row, last_col = cell._get_merged_cell_range()
                    cell_id = cell.id
                    cell_bbox = BoundingBox.enclosing_bbox(cell.siblings)
                    col_index = first_col
                    col_span = last_col - first_col + 1
                    row_index = first_row
                    row_span = last_row - first_row + 1
                    children = []
                    if (cell.col_index == first_col and cell.row_index == first_row) or local_config.table_duplicate_text_in_merged_cells:
                        for sib in cell.siblings:
                            children.extend(sib.children)
                            processed_cells.add(sib)
                        _, cell_words = linearize_children(children, config=config, no_new_lines=True)
                    elif cell.row_index == first_row and local_config.table_cell_left_merge_cell_placeholder:
                        # Left-merge token
                        cell_words = [
                            Word(str(uuid.uuid4()),
                                cell_bbox,
                                local_config.table_cell_left_merge_cell_placeholder,
                                is_structure=True
                            )
                        ]
                    elif cell.col_index == first_col and local_config.table_cell_top_merge_cell_placeholder:
                        # Top-merge token
                        cell_words = [
                            Word(str(uuid.uuid4()),
                                cell_bbox,
                                local_config.table_cell_top_merge_cell_placeholder,
                                is_structure=True
                            )
                        ]
                    elif cell.col_index != first_col and cell.row_index != first_row and local_config.table_cell_cross_merge_cell_placeholder:
                        # Cross-merge token (left and top)
                        cell_words = [
                            Word(str(uuid.uuid4()),
                                cell_bbox,
                                local_config.table_cell_cross_merge_cell_placeholder,
                                is_structure=True
                            )
                        ]
                    else:
                        continue
                else:
                    cell_id = cell.id
                    cell_bbox = cell.bbox
                    col_index = cell.col_index
                    col_span = cell.col_span
                    row_index = cell.row_index
                    row_span = cell.row_span
                    _, cell_words = cell.get_text_and_words(config)
                if local_config.add_prefixes_and_suffixes_as_words:
                    if local_config.table_cell_prefix or (local_config.table_cell_header_prefix and cell.is_column_header):
                        words.append(
                            Word(
                                str(uuid.uuid4()),
                                cell_bbox,
                                local_config.table_cell_header_prefix
                                if cell.is_column_header and local_config.table_cell_header_prefix
                                else local_config.table_cell_prefix,
                                is_structure=True
                            )
                        )
                        words[-1].cell_id = cell_id
                        words[-1].cell_bbox = cell_bbox
                        words[-1].col_index = col_index
                        words[-1].col_span = col_span
                        words[-1].row_index = row_index
                        words[-1].row_span = row_span

                    words.extend(cell_words)
                    if not cell_words and local_config.table_cell_empty_cell_placeholder:
                        words.append(Word(str(uuid.uuid4()), cell_bbox, local_config.table_cell_empty_cell_placeholder))

                    if local_config.table_cell_suffix or (local_config.table_cell_header_suffix and cell.is_column_header):
                        words.append(
                            Word(
                                str(uuid.uuid4()),
                                cell_bbox,
                                local_config.table_cell_header_suffix if cell.is_column_header and local_config.table_cell_header_suffix else local_config.table_cell_suffix,
                                is_structure=True
                            )
                        )
                        words[-1].cell_id = cell_id
                        words[-1].cell_bbox = cell_bbox
                        words[-1].col_index = col_index
                        words[-1].col_span = col_span
                        words[-1].row_index = row_index
                        words[-1].row_span = row_span
                else:
                    words.extend(cell_words)
            if local_config.table_row_suffix and local_config.add_prefixes_and_suffixes_as_words:
                words.append(Word(str(uuid.uuid4()), BoundingBox.enclosing_bbox(cells), local_config.table_row_suffix, is_structure=True))

        if local_config.table_suffix:
            words.append(Word(str(uuid.uuid4()), self.bbox, local_config.table_suffix))

        for w in words:
            w.table_id = str(self.id)
            w.table_bbox = self.bbox

        text = (local_config.table_prefix if local_config.add_prefixes_and_suffixes_in_text else "")
        # Markdown
        if local_config.table_linearization_format == "markdown":
            df = self.to_pandas(
                use_columns=True,
                config=config
            )
            has_column = any([isinstance(c, str) for c in df.columns])
            if local_config.table_remove_column_headers:
                headers = df.columns if has_column else ["" for c in df.columns]
            else:
                headers = df.columns
            table = df.to_markdown(
                tablefmt=local_config.table_tabulate_format, headers=headers, index=False
            )
            if local_config.table_tabulate_remove_extra_hyphens:
                while "-" * 2 in table:
                    table = table.replace("--", "-")
            text += table
        # Plaintext or HTML
        else:
            # FIXME: The cyclomatic complexity of doing things like this will be unsustainable.
            if local_config.table_flatten_semi_structured_as_plaintext and self.table_type == TableTypes.SEMI_STRUCTURED:
                text = "<p>"
                if config.table_linearization_format == "html":
                    local_config.table_prefix = "<p>"
                    local_config.table_suffix = "</p>"
                else:
                    local_config.table_prefix = ""
                    local_config.table_suffix = ""
                local_config.table_linearization_format = "plaintext"
                local_config.table_row_prefix = ""
                local_config.table_row_suffix = ""
                local_config.table_cell_header_prefix = ""
                local_config.table_cell_header_suffix = ""
                local_config.table_cell_prefix = ""
                local_config.table_cell_suffix = " "
            elif local_config.table_linearization_format == "html":
                local_config.table_prefix = "<table>"
                local_config.table_suffix = "</table>"
                local_config.table_row_prefix = "<tr>"
                local_config.table_row_suffix = "</tr>"
                local_config.table_cell_header_prefix = "<th>"
                local_config.table_cell_header_suffix = "</th>"
                local_config.table_cell_prefix = "<td>"
                local_config.table_cell_suffix = "</td>"
                
            row_offset = 0
            processed_cells = set()
            if local_config.table_flatten_headers:
                columns = ["" for _ in range(len(rows[0][1]))]
                column_spans = [1 for _ in range(len(rows[0][1]))]
                for _, row in rows:
                    if not any([c.is_column_header for c in row]):
                        # There is not header in that row, we are done
                        break
                    for i, cell in enumerate(row):
                        if (
                            cell not in processed_cells or
                            local_config.table_duplicate_text_in_merged_cells or
                            local_config.table_flatten_headers
                        ):
                            if cell.siblings:
                                # This handles the edge case where we are flattening the headers
                                # so we want to duplicate the cell text but only in its first row
                                first_row, first_col, _, last_col = cell._get_merged_cell_range()
                                # We always compute the colspan, but we will discard them if config.table_duplicate_text_in_merged_cells is True
                                column_spans[i] = last_col - first_col + 1
                                if cell in processed_cells and first_row != cell.row_index:
                                    continue
                                children = []
                                for sib in cell.siblings:
                                    children.extend(sib.children)
                                    processed_cells.add(sib)
                                text, _ = linearize_children(children, config=local_config, no_new_lines=True)
                                columns[i] += text
                            else:
                                text = cell.get_text(local_config)
                                columns[i] += text
                        elif local_config.table_cell_empty_cell_placeholder and local_config.table_linearization_format != "html":
                            columns[i] += local_config.table_cell_empty_cell_placeholder
                        else:
                            columns[i] += ""
                            column_spans[i] = 0
                    row_offset += 1
                if any(columns):
                    text += local_config.table_row_prefix if local_config.add_prefixes_and_suffixes_in_text else ""
                    for column, column_span in zip(columns, column_spans):
                        if column_span == 0:
                            continue
                        
                        if local_config.table_linearization_format == "html":
                            prefix = f'<th colspan="{column_span}">'
                        else:
                            prefix = (local_config.table_cell_header_prefix if local_config.table_cell_header_prefix else local_config.table_cell_prefix)
                        # We don't have any rowspan logic here as the flattened header will have rowspan=1 always.
                        text += (
                            (
                                prefix + 
                                (column or local_config.table_cell_empty_cell_placeholder) +
                                (local_config.table_cell_header_suffix if local_config.table_cell_header_suffix else local_config.table_cell_suffix)
                            )
                            if local_config.add_prefixes_and_suffixes_in_text or local_config.table_linearization_format == "html" else
                            (column or local_config.table_cell_empty_cell_placeholder)
                        )
                        text += local_config.table_column_separator
                    text += (local_config.table_row_suffix if local_config.add_prefixes_and_suffixes_in_text else "")
                    text += local_config.table_row_separator
                    
            for _, row in rows[row_offset:]:
                text += (local_config.table_row_prefix if local_config.add_prefixes_and_suffixes_in_text else "")
                for cell in sorted(row, key=lambda c: c.col_index):
                    # This will return row_index, col_index, row_index, col_index for regular cells
                    first_row, first_col, last_row, last_col = cell._get_merged_cell_range()
                    if cell in processed_cells and local_config.table_linearization_format == "html":
                        continue
                    
                    # Siblings includes the current cell
                    if cell.siblings:
                        children = []
                        if (cell.col_index == first_col and cell.row_index == first_row) or local_config.table_duplicate_text_in_merged_cells:
                            for sib in cell.siblings:
                                children.extend(sib.children)
                                processed_cells.add(sib)
                            cell_text, _ = linearize_children(children, config=local_config, no_new_lines=True)
                        elif cell.row_index == first_row and local_config.table_cell_left_merge_cell_placeholder:
                            cell_text = local_config.table_cell_left_merge_cell_placeholder
                        elif cell.col_index == first_col and local_config.table_cell_top_merge_cell_placeholder:
                            cell_text = local_config.table_cell_top_merge_cell_placeholder
                        elif cell.col_index != first_col and cell.row_index != first_row and local_config.table_cell_cross_merge_cell_placeholder:
                            cell_text = local_config.table_cell_cross_merge_cell_placeholder
                        else:
                            cell_text = ""
                            
                    # This is a regular cell
                    else:
                        cell_text, _ = cell.get_text_and_words(local_config)
                    
                    if local_config.table_linearization_format == "html":
                        if cell.is_column_header:
                            prefix = (
                                '<th' +
                                (f' colspan="{last_col - first_col + 1}" ' if last_col - first_col > 0 else '') +
                                (f' rowspan="{last_row - first_row + 1}"' if last_row - first_row > 0 else '') +
                                '>'
                            )
                        else:
                            prefix = (
                                '<td' +
                                (f' colspan="{last_col - first_col + 1}" ' if last_col - first_col > 0 else '') +
                                (f' rowspan="{last_row - first_row + 1}"' if last_row - first_row > 0 else '') +
                                '>'
                            )
                    else:
                        prefix = local_config.table_cell_header_prefix if local_config.table_cell_header_prefix and cell.is_column_header else local_config.table_cell_prefix
                        
                    text += (
                        (
                            prefix +
                            # Removes trailing whitespace in cell_text
                            (cell_text.strip() or local_config.table_cell_empty_cell_placeholder) +
                            (local_config.table_cell_header_suffix if local_config.table_cell_header_suffix and cell.is_column_header else local_config.table_cell_suffix)
                        )
                        if local_config.add_prefixes_and_suffixes_in_text else
                        (cell_text or local_config.table_cell_empty_cell_placeholder)
                    ) 
                    text += local_config.table_column_separator
                if text and text[-1] == local_config.table_column_separator:
                    text = text[:-1]
                text += (local_config.table_row_suffix if local_config.add_prefixes_and_suffixes_in_text else "")
                text += local_config.table_row_separator
                
        if local_config.table_add_title_as_caption and self.title and local_config.table_linearization_format == "html":
            text += "<caption>" + self.title.get_text() + "</caption>"
            
        text += (local_config.table_suffix if local_config.add_prefixes_and_suffixes_in_text else "")
        
        return text, words

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

    rows = sorted([r + 1 for r in rows])
    cols = sorted(list(set([cell.col_index for cell in filtered_rows[rows[0] - 1]])))

    new_row_range = list(range(1, len(rows) + 1))
    new_col_range = list(range(1, len(filtered_rows[rows[0] - 1]) + 1))

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
                new_cells_dict[(cell_row, cell_col)].add_children(cell_children)

                for sibling in new_cells_dict[(cell_row, cell_col)].siblings:
                    sibling.siblings = new_cell_siblings
            else:
                continue

    return list(new_cells_dict.values())
