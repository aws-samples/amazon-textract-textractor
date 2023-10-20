"""
Represents a single :class:`Document` page, as it would appear in the Textract API output.
The :class:`Page` object also contains the metadata such as the physical dimensions of the page (width, height, in pixels), child_ids etc.
"""

import os
import string
import logging
import xlsxwriter
from typing import List, Tuple
from copy import deepcopy
from collections import defaultdict
from textractor.entities.expense_document import ExpenseDocument

from textractor.entities.word import Word
from textractor.entities.line import Line
from textractor.entities.table import Table
from textractor.entities.signature import Signature
from textractor.exceptions import InputError
from textractor.entities.key_value import KeyValue
from textractor.entities.query import Query
from textractor.entities.identity_document import IdentityDocument
from textractor.entities.bbox import SpatialObject
from textractor.data.constants import SelectionStatus, Direction, DirectionalFinderType
from textractor.data.constants import TextTypes, SimilarityMetric
from textractor.entities.selection_element import SelectionElement
from textractor.utils.geometry_util import sort_by_position
from textractor.utils.search_utils import SearchUtils, jaccard_similarity
from textractor.visualizers.entitylist import EntityList


class Page(SpatialObject):
    """
    Creates a new document, ideally representing a single item in the dataset.

    :param id: Unique id of the Page
    :type id: str
    :param width: Width of page, in pixels
    :type width: float
    :param height: Height of page, in pixels
    :type height: float
    :param page_num: Page number in the document linked to this Page object
    :type page_num: int
    :param child_ids: IDs of child entities in the Page as determined by Textract
    :type child_ids: List
    """

    def __init__(
        self, id: str, width: int, height: int, page_num: int = -1, child_ids=None
    ):
        super().__init__(width=width, height=height)
        self.id = id
        self._words: EntityList[Word] = EntityList([])
        self._lines: EntityList[Line] = EntityList([])
        self._key_values: EntityList[KeyValue] = EntityList([])
        self._checkboxes: EntityList[KeyValue] = EntityList([])
        self._tables: EntityList[Table] = EntityList([])
        self._queries: EntityList[Query] = EntityList([])
        self._expense_documents: EntityList[ExpenseDocument] = EntityList([])
        self.kv_cache = defaultdict(list)
        self.metadata = {}
        self.page_num = page_num
        self.child_ids: List[str] = child_ids
        self.image = None

    # functions to add entities to the Page object
    @property
    def words(self) -> EntityList[Word]:
        """
        Returns all the :class:`Word` objects present in the Page.

        :return: List of Word objects, each representing a word within the Page.
        :rtype: EntityList[Word]
        """
        return self._words

    @words.setter
    def words(self, words: List[Word]):
        """
        Add Word objects to the Page.

        :param words: List of Word objects, each representing a word within the page. No specific ordering is assumed.
        :type words: List[Word]
        """
        self._words = words
        self._words = EntityList(sort_by_position(list(set(self._words))))

    @property
    def lines(self) -> EntityList[Line]:
        """
        Returns all the :class:`Line` objects present in the Page.

        :return: List of Line objects, each representing a line within the Page.
        :rtype: EntityList[Line]
        """
        return self._lines

    @lines.setter
    def lines(self, lines: List[Line]):
        """
        Add Line objects to the Document.

        :param lines: List of Line objects, each representing a line within the Page.
        :type lines: List[Line]
        """
        self._lines = EntityList(sort_by_position(lines))

    @property
    def text(self) -> str:
        """Returns the page text as one string

        :return: Line text seperated by line return
        :rtype: str
        """
        return os.linesep.join([line.text for line in self.lines])

    @property
    def key_values(self) -> EntityList[KeyValue]:
        """
        Returns all the :class:`KeyValue` objects present in the Page.

        :return: List of KeyValue objects, each representing a key-value pair within the Page.
        :rtype: EntityList[KeyValue]
        """
        return self._key_values

    @key_values.setter
    def key_values(self, kv: List[KeyValue]):
        """
        Add KeyValue objects to the Page.

        :param kv: List of KeyValue objects, each representing a KV area within the document page.
        :type kv: List[KeyValue]
        """
        self._key_values = EntityList(sort_by_position(kv))

    @property
    def checkboxes(self) -> EntityList[KeyValue]:
        """
        Returns all the :class:`KeyValue` objects with :class:`SelectionElement` present in the Page.

        :return: List of KeyValue objects, each representing a checkbox within the Page.
        :rtype: EntityList[KeyValue]
        """
        return self._checkboxes

    @checkboxes.setter
    def checkboxes(self, checkbox: List[KeyValue]):
        """
        Add KeyValue objects containing SelectionElement children to the Page.

        :param checkbox: List of KeyValue objects, each representing a checkbox area within the document page.
        :type checkbox: List[KeyValue]
        """
        self._checkboxes = EntityList(sort_by_position(checkbox))

    @property
    def tables(self) -> EntityList[Table]:
        """
        Returns all the :class:`Table` objects present in the Page.

        :return: List of Table objects, each representing a table within the Page.
        :rtype: EntityList
        """
        return self._tables

    @tables.setter
    def tables(self, tables: List[Table]):
        """
        Add Table objects to the Page.

        :param tables: List of Table objects, each representing a Table area within the document page.
        :type tables: list
        """
        self._tables = EntityList(tables)

    @property
    def queries(self) -> EntityList[Query]:
        """
        Returns all the :class:`Query` objects present in the Page.

        :return: List of Query objects.
        :rtype: EntityList
        """
        return self._queries

    @queries.setter
    def queries(self, queries: List[Query]):
        """
        Add Signature objects to the Page.

        :param signatures: List of Signature objects.
        :type signatures: list
        """
        self._queries = EntityList(queries)

    @property
    def signatures(self) -> EntityList[Signature]:
        """
        Returns all the :class:`Signature` objects present in the Page.

        :return: List of Signature objects.
        :rtype: EntityList
        """
        return self._signatures

    @signatures.setter
    def signatures(self, signatures: List[Signature]):
        """
        Add Signature objects to the Page.

        :param signatures: List of Signature objects.
        :type signatures: list
        """
        self._signatures = EntityList(signatures)

    @property
    def expense_documents(self) -> EntityList[ExpenseDocument]:
        """
        Returns all the :class:`ExpenseDocument` objects present in the Page.

        :return: List of ExpenseDocument objects.
        :rtype: EntityList
        """
        return self._expense_documents

    @expense_documents.setter
    def expense_documents(self, expense_documents: List[ExpenseDocument]):
        """
        Add ExpenseDocument objects to the Page.

        :param tables: List of ExpenseDocument objects.
        :type expense_documents: list
        """
        self._expense_documents = EntityList(expense_documents)

    def __repr__(self):
        return os.linesep.join(
            [
                f"This Page ({self.page_num}) holds the following data:",
                f"Words - {len(self.words)}",
                f"Lines - {len(self.lines)}",
                f"Key-values - {len(self.key_values)}",
                f"Checkboxes - {len(self.checkboxes)}",
                f"Tables - {len(self.tables)}",
                f"Queries - {len(self.queries)}",
                f"Signatures - {len(self.signatures)}",
                f"Expense documents - {len(self.expense_documents)}",
            ]
        )

    def __getitem__(self, key):
        output = self.get(key)
        if output:
            return output
        raise KeyError(f"{key} was not found in Document")

    def keys(self, include_checkboxes: bool = True) -> List[str]:
        """
        Prints all keys for key-value pairs and checkboxes if the page contains them.

        :param include_checkboxes: True/False. Set False if checkboxes need to be excluded.
        :type include_checkboxes: bool

        :return: List of strings containing key names in the Page
        :rtype: List[str]
        """
        keys = []
        keys = [keyvalue.key for keyvalue in self.key_values]
        if include_checkboxes:
            keys += [keyvalue.key for keyvalue in self.checkboxes]
        return keys

    def filter_checkboxes(
        self, selected: bool = True, not_selected: bool = True
    ) -> EntityList[KeyValue]:
        """
        Return a list of :class:`KeyValue` objects containing checkboxes if the page contains them.

        :param selected: True/False Return SELECTED checkboxes
        :type selected: bool
        :param not_selected: True/False Return NOT_SELECTED checkboxes
        :type not_selected: bool

        :return: Returns checkboxes that match the conditions set by the flags.
        :rtype: EntityList[KeyValue]
        """
        if not self.checkboxes:
            logging.warning(f"This document does not contain checkboxes")
            return []
        else:
            if selected and not_selected:
                checkboxes = self.checkboxes
                return EntityList(checkboxes)

            checkboxes = []
            if selected:
                checkboxes = [
                    kv
                    for kv in self.checkboxes
                    if kv.selection_status == SelectionStatus.SELECTED
                ]
            if not_selected:
                checkboxes = [
                    kv
                    for kv in self.checkboxes
                    if kv.selection_status == SelectionStatus.NOT_SELECTED
                ]

            return EntityList(checkboxes)

    def get_words_by_type(
        self, text_type: TextTypes = TextTypes.PRINTED
    ) -> EntityList[Word]:
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
            logging.warn("Document contains no word entities.")
            return []

        filtered_words = [word for word in self.words if word.text_type == text_type]
        return EntityList(filtered_words)

    def _search_words_with_similarity(
        self,
        keyword: str,
        top_k: int = 1,
        similarity_metric: SimilarityMetric = SimilarityMetric.LEVENSHTEIN,
        similarity_threshold: float = 0.6,
    ) -> List[Tuple[Word, float]]:
        """
        Returns a list of top_k words with their similarity to the keyword.

        :param keyword: Keyword that is used to query the document.
        :type keyword: str, required
        :param top_k: Number of closest word objects to be returned. default=1
        :type top_k: int, optional
        :param similarity_metric: SimilarityMetric.COSINE, SimilarityMetric.EUCLIDEAN or SimilarityMetric.LEVENSHTEIN. SimilarityMetric.COSINE is chosen as default.
        :type similarity_metric: SimilarityMetric
        :param similarity_threshold: Measure of how similar document key is to queried key. default=0.6
        :type similarity_threshold: float

        :return: Returns a list of tuples containing similarity and Word.
        :rtype: List[Tuple(float, Word)]]
        """
        if not isinstance(similarity_metric, SimilarityMetric):
            raise InputError(
                "similarity_metric parameter should be of SimilarityMetric type. Find input choices from textractor.data.constants"
            )
        top_n_words = []
        similarity_threshold = (
            similarity_threshold
            if similarity_metric == SimilarityMetric.COSINE
            else -(similarity_threshold)
        )
        lowest_similarity = similarity_threshold

        for word in self.words:
            similarity = SearchUtils.get_word_similarity(
                keyword, word.text, similarity_metric
            )
            similarity = (
                similarity
                if similarity_metric == SimilarityMetric.COSINE
                else -(similarity)
            )

            if len(top_n_words) < top_k and similarity > similarity_threshold:
                top_n_words.append((similarity, word))
            elif similarity > lowest_similarity:
                top_n_words[-1] = (similarity, word)
            else:
                continue
            top_n_words = sorted(top_n_words, key=lambda x: x[0], reverse=True)
            lowest_similarity = top_n_words[-1][0]

        return top_n_words

    def search_words(
        self,
        keyword: str,
        top_k: int = 1,
        similarity_metric: SimilarityMetric = SimilarityMetric.LEVENSHTEIN,
        similarity_threshold: float = 0.6,
    ) -> EntityList[Word]:
        """
        Return a list of top_k words that match the keyword.

        :param keyword: Keyword that is used to query the document.
        :type keyword: str, required
        :param top_k: Number of closest word objects to be returned. default=1
        :type top_k: int, optional
        :param similarity_metric: SimilarityMetric.COSINE, SimilarityMetric.EUCLIDEAN or SimilarityMetric.LEVENSHTEIN. SimilarityMetric.COSINE is chosen as default.
        :type similarity_metric: SimilarityMetric
        :param similarity_threshold: Measure of how similar document key is to queried key. default=0.6
        :type similarity_threshold: float

        :return: Returns a list of words that match the queried key sorted from highest to lowest similarity.
        :rtype: EntityList[Word]
        """

        top_n_words = EntityList(
            [
                ent[1]
                for ent in self._search_words_with_similarity(
                    keyword=keyword,
                    top_k=top_k,
                    similarity_metric=similarity_metric,
                    similarity_threshold=similarity_threshold,
                )
            ]
        )

        return top_n_words

    def _search_lines_with_similarity(
        self,
        keyword: str,
        top_k: int = 1,
        similarity_metric: SimilarityMetric = SimilarityMetric.LEVENSHTEIN,
        similarity_threshold: int = 0.6,
    ) -> List[Tuple[Line, float]]:
        """
        Return a list of top_k lines that contain the queried keyword.

        :param keyword: Keyword that is used to query the page.
        :type keyword: str
        :param top_k: Number of closest line objects to be returned
        :type top_k: int
        :param similarity_metric: SimilarityMetric.COSINE, SimilarityMetric.EUCLIDEAN or SimilarityMetric.LEVENSHTEIN. SimilarityMetric.COSINE is chosen as default.
        :type similarity_metric: SimilarityMetric
        :param similarity_threshold: Measure of how similar page key is to queried key. default=0.6
        :type similarity_threshold: float

        :return: Returns a list of tuples of lines and their similarity to the keyword that contain the queried key sorted
                 from highest to lowest similarity.
        :rtype: List[Tuple[Line, float]]
        """
        if not isinstance(similarity_metric, SimilarityMetric):
            raise InputError(
                "similarity_metric parameter should be of SimilarityMetric type. Find input choices from textractor.data.constants"
            )

        top_n_lines = []
        similarity_threshold = (
            similarity_threshold
            if similarity_metric == SimilarityMetric.COSINE
            else -(similarity_threshold)
        )
        lowest_similarity = similarity_threshold

        for line in self.lines:
            similarity = [
                SearchUtils.get_word_similarity(keyword, word, similarity_metric)
                for word in line.__repr__().split(" ")
            ]
            similarity.append(
                SearchUtils.get_word_similarity(
                    keyword, line.__repr__(), similarity_metric
                )
            )
            similarity = (
                max(similarity)
                if similarity_metric == SimilarityMetric.COSINE
                else -min(similarity)
            )

            if len(top_n_lines) < top_k and similarity > similarity_threshold:
                top_n_lines.append((similarity, line))
            elif similarity > lowest_similarity:
                top_n_lines[-1] = (similarity, line)
            else:
                continue
            top_n_lines = sorted(top_n_lines, key=lambda x: x[0], reverse=True)
            lowest_similarity = top_n_lines[-1][0]

        return top_n_lines

    def search_lines(
        self,
        keyword: str,
        top_k: int = 1,
        similarity_metric: SimilarityMetric = SimilarityMetric.LEVENSHTEIN,
        similarity_threshold: int = 0.6,
    ) -> EntityList[Line]:
        """
        Return a list of top_k lines that contain the queried keyword.

        :param keyword: Keyword that is used to query the page.
        :type keyword: str
        :param top_k: Number of closest line objects to be returned
        :type top_k: int
        :param similarity_metric: SimilarityMetric.COSINE, SimilarityMetric.EUCLIDEAN or SimilarityMetric.LEVENSHTEIN. SimilarityMetric.COSINE is chosen as default.
        :type similarity_metric: SimilarityMetric
        :param similarity_threshold: Measure of how similar page key is to queried key. default=0.6
        :type similarity_threshold: float

        :return: Returns a list of lines that contain the queried key sorted
                 from highest to lowest similarity.
        :rtype: EntityList[Line]
        """

        top_n_lines = EntityList(
            [
                ent[1]
                for ent in self._search_lines_with_similarity(
                    keyword=keyword,
                    top_k=top_k,
                    similarity_metric=similarity_metric,
                    similarity_threshold=similarity_threshold,
                )
            ]
        )

        return top_n_lines

    # KeyValue entity related functions
    def get(
        self,
        key: str,
        top_k_matches: int = 1,
        similarity_metric: SimilarityMetric = SimilarityMetric.LEVENSHTEIN,
        similarity_threshold: float = 0.6,
    ) -> EntityList[KeyValue]:
        """
        Return upto top_k_matches of key-value pairs for the key that is queried from the page.

        :param key: Query key to match
        :type key: str
        :param top_k_matches: Maximum number of matches to return
        :type top_k_matches: int
        :param similarity_metric: SimilarityMetric.COSINE, SimilarityMetric.EUCLIDEAN or SimilarityMetric.LEVENSHTEIN. SimilarityMetric.COSINE is chosen as default.
        :type similarity_metric: SimilarityMetric
        :param similarity_threshold: Measure of how similar page key is to queried key. default=0.6
        :type similarity_threshold: float

        :return: Returns a list of key-value pairs that match the queried key sorted from highest
                 to lowest similarity.
        :rtype: EntityList[KeyValue]
        """
        if not isinstance(similarity_metric, SimilarityMetric):
            raise InputError(
                "similarity_metric parameter should be of SimilarityMetric type. Find input choices from textractor.data.constants"
            )

        top_n = []
        similarity_threshold = (
            similarity_threshold
            if similarity_metric == SimilarityMetric.COSINE
            else -(similarity_threshold)
        )
        lowest_similarity = similarity_threshold

        for kv in self.key_values + self.checkboxes:
            try:
                edited_document_key = "".join(
                    [
                        char
                        for char in kv.key.__repr__()
                        if char not in string.punctuation
                    ]
                )
            except:
                pass
            key = "".join([char for char in key if char not in string.punctuation])

            similarity = [
                SearchUtils.get_word_similarity(key, word, similarity_metric)
                for word in edited_document_key.split(" ")
            ]
            similarity.append(
                SearchUtils.get_word_similarity(
                    key, edited_document_key, similarity_metric
                )
            )

            similarity = (
                max(similarity)
                if similarity_metric == SimilarityMetric.COSINE
                else -min(similarity)
            )

            if similarity > similarity_threshold:
                if len(top_n) < top_k_matches:
                    top_n.append((kv, similarity))
                elif similarity > lowest_similarity:
                    top_n[-1] = (kv, similarity)
                top_n = sorted(top_n, key=lambda x: x[1], reverse=True)
                lowest_similarity = top_n[-1][1]

        if not top_n:
            logging.warning(
                f"Query key does not match any existing keys in the document.{os.linesep}{self.keys()}"
            )

        logging.info(f"Query key matched {len(top_n)} key-values in the document.")

        return EntityList([value[0] for value in top_n])

    # Export document entities into supported formats
    def export_kv_to_csv(
        self,
        include_kv: bool = True,
        include_checkboxes: bool = True,
        filepath: str = "Key-Values.csv",
    ):
        """
        Export key-value entities and checkboxes in csv format.

        :param include_kv: True if KVs are to be exported. Else False.
        :type include_kv: bool
        :param include_checkboxes: True if checkboxes are to be exported. Else False.
        :type include_checkboxes: bool
        :param filepath: Path to where file is to be stored.
        :type filepath: str
        """
        keys = []
        values = []
        if include_kv and not self.key_values:
            logging.warning("Document does not contain key-values.")
        elif include_kv:
            for kv in self.key_values:
                keys.append(kv.key.__repr__())
                values.append(kv.value.__repr__())

        if include_checkboxes and not self.checkboxes:
            logging.warning("Document does not contain checkbox elements.")
        elif include_checkboxes:
            for kv in self.checkboxes:
                keys.append(kv.key.__repr__())
                values.append(kv.value.children[0].status.name)

        with open(filepath, "w") as f:
            f.write(f"Key,Value{os.linesep}")
            for k, v in zip(keys, values):
                f.write(f"{k},{v}{os.linesep}")

        logging.info(
            f"csv file stored at location {os.path.join(os.getcwd(), filepath)}"
        )

    def export_kv_to_txt(
        self,
        include_kv: bool = True,
        include_checkboxes: bool = True,
        filepath: str = "Key-Values.txt",
    ):
        """
        Export key-value entities and checkboxes in txt format.

        :param include_kv: True if KVs are to be exported. Else False.
        :type include_kv: bool
        :param include_checkboxes: True if checkboxes are to be exported. Else False.
        :type include_checkboxes: bool
        :param filepath: Path to where file is to be stored.
        :type filepath: str
        """
        export_str = []
        index = 1
        if include_kv and not self.key_values:
            logging.warning("Document does not contain key-values.")
        elif include_kv:
            for kv in self.key_values:
                export_str.append(
                    f"{index}. {kv.key.__repr__()} : {kv.value.__repr__()}{os.linesep}"
                )
                index += 1

        if include_checkboxes and not self.checkboxes:
            logging.warning("Document does not contain checkbox elements.")
        elif include_checkboxes:
            for kv in self.checkboxes:
                export_str.append(
                    f"{index}. {kv.key.__repr__()} : {kv.value.__repr__()}{os.linesep}"
                )
                index += 1

        with open(filepath, "w") as text_file:
            text_file.write("".join(export_str))
        logging.info(
            f"txt file stored at location {os.path.join(os.getcwd(),filepath)}"
        )

    def independent_words(self) -> EntityList[Word]:
        """
        :return: Return all words in the document, outside of tables, checkboxes, key-values.
        :rtype: EntityList[Word]
        """
        if not self.words:
            logging.warning("Words have not been assigned to this Document object.")
            return []

        else:
            table_words = sum([table.words for table in self.tables], [])
            kv_words = sum([kv.words for kv in self.key_values], [])
            checkbox_words = sum([kv.words for kv in self.checkboxes], [])
            dependent_words = table_words + checkbox_words + kv_words
            dependent_word_ids = set([word.id for word in dependent_words])
            independent_words = [
                word for word in self.words if word.id not in dependent_word_ids
            ]
            return EntityList(independent_words)

    def export_tables_to_excel(self, filepath):
        """
        Creates an excel file and writes each table on a separate worksheet within the workbook.
        This is stored on the filepath passed by the user.

        :param filepath: Path to store the exported Excel file.
        :type filepath: str, required
        """
        if not filepath:
            logging.error("Filepath required to store excel file.")
        workbook = xlsxwriter.Workbook(filepath)
        for table in self.tables:
            workbook = table.to_excel(
                filepath=None, workbook=workbook, save_workbook=False
            )
        workbook.close()

    def _update_entity_page_num(self):
        """Updates page number if Textractor API call was given a list of images."""
        entities = (
            self.words + self.lines + self.key_values + self.checkboxes + self.tables
        )
        for entity in entities:
            entity.page = self.page_num

    def return_duplicates(self):
        """
        Returns a list containing :class:`EntityList` objects.
        Each :class:`EntityList` instance contains the key-values and the last item is the table which contains duplicate information.
        This function is intended to let the Textract user know of duplicate objects extracted by the various Textract models.

        :return: List of EntityList objects each containing the intersection of KeyValue and Table entities on the page.
        :rtype: List[EntityList]
        """
        tables = self.tables
        key_values = self.key_values

        document_duplicates = []

        for table in tables:
            table_duplicates = EntityList([])
            table_x1, table_x2, table_y1, table_y2 = (
                table.bbox.x,
                table.bbox.x + table.bbox.width,
                table.bbox.y,
                table.bbox.y + table.bbox.height,
            )
            for kv in key_values:
                if (
                    kv.bbox.x >= table_x1
                    and kv.bbox.x <= table_x2
                    and kv.bbox.y >= table_y1
                    and kv.bbox.y <= table_y2
                ):
                    table_duplicates.append(kv)

            if table_duplicates:
                table_duplicates.append(table)

            document_duplicates.append(table_duplicates)

        return document_duplicates

    def directional_finder(
        self,
        word_1: str = "",
        word_2: str = "",
        prefix: str = "",
        direction=Direction.BELOW,
        entities=[],
    ):
        """
        The function returns entity types present in entities by prepending the prefix provided by te user. This helps in cases of repeating
        key-values and checkboxes. The user can manipulate original data or produce a copy. The main advantage of this function is to be able to define direction.

        :param word_1: The reference word from where x1, y1 coordinates are derived
        :type word_1: str, required
        :param word_2: The second word preferably in the direction indicated by the parameter direction. When it isn't given the end of page coordinates are used in the given direction.
        :type word_2: str, optional
        :param prefix: User provided prefix to prepend to the key . Without prefix, the method acts as a search by geometry function
        :type prefix: str, optional
        :param entities: List of DirectionalFinderType inputs.
        :type entities: List[DirectionalFinderType]

        :return: Returns the EntityList of modified key-value and/or checkboxes
        :rtype: EntityList
        """

        if not word_1:
            return EntityList([])

        x1, x2, y1, y2 = self._get_coords(word_1, word_2, direction)

        if x1 == -1:
            return EntityList([])

        entity_dict = {
            DirectionalFinderType.KEY_VALUE_SET: self.key_values,
            DirectionalFinderType.SELECTION_ELEMENT: self.checkboxes,
        }

        entitylist = []
        for entity_type in entities:
            entitylist.extend(list(entity_dict[entity_type]))

        new_key_values = self._get_kv_with_direction(
            direction, entitylist, (x1, x2, y1, y2)
        )

        final_kv = []
        for kv in new_key_values:
            if kv.key:
                key_words = [deepcopy(word) for word in kv.key.words]
                key_words[0].text = prefix + key_words[0].text
                new_kv = deepcopy(kv)
                new_kv.key = key_words
                final_kv.append(new_kv)
            else:
                final_kv.append(kv)

        return EntityList(final_kv)

    def _get_kv_with_direction(self, direction, entitylist, coords):
        """Return key-values and checkboxes in entitiylist present in the direction given with respect to the coordinates."""
        if direction == Direction.ABOVE:
            new_key_values = [
                kv
                for kv in entitylist
                if kv.bbox.y <= coords[2] and kv.bbox.y >= coords[-1]
            ]

        elif direction == Direction.BELOW:
            new_key_values = [
                kv
                for kv in entitylist
                if kv.bbox.y >= coords[2] and kv.bbox.y <= coords[-1]
            ]

        elif direction == Direction.RIGHT:
            new_key_values = [
                kv
                for kv in entitylist
                if kv.bbox.x >= coords[0] and kv.bbox.x <= coords[1]
            ]
            new_key_values = [
                kv
                for kv in new_key_values
                if kv.bbox.y >= coords[2] - kv.bbox.height
                and kv.bbox.y <= coords[-1] + 3 * kv.bbox.height
            ]

        elif direction == Direction.LEFT:
            new_key_values = [
                kv
                for kv in entitylist
                if kv.bbox.x <= coords[0] and kv.bbox.x >= coords[1]
            ]
            new_key_values = [
                kv
                for kv in new_key_values
                if kv.bbox.y >= coords[2] - kv.bbox.height
                and kv.bbox.y <= coords[-1] + 3 * kv.bbox.height
            ]

        return new_key_values

    def _get_coords(self, word_1, word_2, direction):
        """
        Returns coordinates for the area within which to search for key-values with the directional_finder by retrieving coordinates of word_1 \
        and word_2 if it exists else end of page.
        """
        word_1_objects = self.search_lines(
            keyword=word_1,
            top_k=5,
            similarity_metric=SimilarityMetric.COSINE,
            similarity_threshold=0.5,
        )

        if not word_1_objects:
            logging.warning(f"{word_1} not found in page")
            return -1, -1, -1, -1
        else:
            word_1_obj = word_1_objects[0]
            x1, y1 = word_1_obj.bbox.x, word_1_obj.bbox.y

        if word_2:
            word_2_objects = self.search_lines(
                keyword=word_2,
                top_k=5,
                similarity_metric=SimilarityMetric.COSINE,
                similarity_threshold=0.5,
            )

            if not word_2_objects:
                logging.warning(f"{word_2} not found in page")
                return -1, -1, -1, -1
            else:
                word_2_obj = word_2_objects[0]
                x2, y2 = word_2_obj.bbox.x, word_2_obj.bbox.y
        else:
            x2, y2 = 1, 1

        if direction == Direction.ABOVE:
            x1, x2, y1, y2 = (x1, x2, y1, y2) if y2 < y1 else (x1, 0, y1, 0)

        elif direction == Direction.BELOW:
            x1, x2, y1, y2 = (x1, x2, y1, y2) if y2 > y1 else (x1, 1, y1, 1)

        elif direction == Direction.RIGHT:
            x1, x2, y1, y2 = (x1, x2, y1, y2) if x2 > x1 else (x1, 1, y1, y1)

        elif direction == Direction.LEFT:
            x1, x2, y1, y2 = (x1, x2, y1, y2) if x2 < x1 else (x1, 0, y1, y1)

        else:
            return -1, -1, -1, -1

        return x1, x2, y1, y2

    def visualize(self, *args, **kwargs):
        return EntityList(self).visualize(*args, **kwargs)