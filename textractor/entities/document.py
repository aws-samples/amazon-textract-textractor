"""The Document class is defined to host all the various DocumentEntity objects within it. :class:`DocumentEntity` objects can be 
accessed, searched and exported the functions given below."""

import boto3
import json
import os
import string
import logging
import xlsxwriter
import io
from typing import List, IO, Union, AnyStr
from copy import deepcopy
from collections import defaultdict
from PIL import Image

from trp.trp2 import TDocument, TDocumentSchema

from textractor.entities.expense_document import ExpenseDocument
from textractor.entities.identity_document import IdentityDocument
from textractor.entities.word import Word
from textractor.entities.line import Line
from textractor.entities.page import Page
from textractor.entities.table import Table
from textractor.entities.query import Query
from textractor.entities.signature import Signature
from textractor.exceptions import InputError
from textractor.entities.key_value import KeyValue
from textractor.entities.bbox import SpatialObject
from textractor.data.constants import SelectionStatus
from textractor.utils.s3_utils import download_from_s3
from textractor.visualizers.entitylist import EntityList
from textractor.data.constants import (
    TextTypes,
    SimilarityMetric,
    Direction,
    DirectionalFinderType,
)
from textractor.entities.selection_element import SelectionElement
from textractor.utils.search_utils import SearchUtils, jaccard_similarity


class Document(SpatialObject):
    """
    Represents the description of a single document, as it would appear in the input to the Textract API.
    Document serves as the root node of the object model hierarchy,
    which should be used as an intermediate form for most analytic purposes.
    The Document node also contains the metadata of the document.
    """

    @classmethod
    def open(cls, fp: Union[dict, str, IO[AnyStr]]):
        """Create a Document object from a JSON file path, file handle or response dictionary

        :param fp: _description_
        :type fp: Union[dict, str, IO[AnyStr]]
        :raises InputError: Raised on input not being of type Union[dict, str, IO[AnyStr]]
        :return: Document object
        :rtype: Document
        """
        from textractor.parsers import response_parser

        if isinstance(fp, dict):
            return response_parser.parse(fp)
        elif isinstance(fp, str):
            if fp.startswith("s3://"):
                # FIXME: Opening s3 clients for everythign should be avoided
                client = boto3.client("s3")
                return response_parser.parse(json.load(download_from_s3(client, fp)))
            with open(fp, "r") as f:
                return response_parser.parse(json.load(f))
        elif isinstance(fp, io.IOBase):
            return response_parser.parse(json.load(fp))
        else:
            raise InputError(
                f"Document.open() input must be of type dict, str or file handle, not {type(fp)}"
            )

    def __init__(self, num_pages: int = 1):
        """
        Creates a new document, ideally containing entity objects pertaining to each page.

        :param num_pages: Number of pages in the input Document.
        """
        super().__init__(width=0, height=0)
        self.num_pages: int = num_pages
        self._pages: List[Page] = []
        self._identity_documents: List[IdentityDocument] = []
        self._trp2_document = None
        self.response = None

    @property
    def words(self) -> EntityList[Word]:
        """
        Returns all the :class:`Word` objects present in the Document.

        :return: List of Word objects, each representing a word within the Document.
        :rtype: EntityList[Word]
        """
        return EntityList(sum([page.words for page in self.pages], []))

    @property
    def text(self) -> str:
        """Returns the document text as one string

        :return: Page text seperated by line return
        :rtype: str
        """
        return os.linesep.join([page.text for page in self.pages])

    @property
    def identity_documents(self) -> EntityList[IdentityDocument]:
        """
        Returns all the :class:`IdentityDocument` objects present in the Document.

        :return: List of IdentityDocument objects, each representing an identity document within the Document.
        :rtype: EntityList[IdentityDocument]
        """
        return EntityList(self._identity_documents)

    @identity_documents.setter
    def identity_documents(self, identity_documents: List[IdentityDocument]):
        """
        Set all the identity documents detected inside the Document
        """
        self._identity_documents = identity_documents

    @property
    def expense_documents(self) -> EntityList[ExpenseDocument]:
        """
        Returns all the :class:`ExpenseDocument` objects present in the Document.

        :return: List of ExpenseDocument objects, each representing an expense document within the Document.
        :rtype: EntityList[ExpenseDocument]
        """
        return EntityList(sum([page.expense_documents for page in self.pages], []))

    @property
    def lines(self) -> EntityList[Line]:
        """
        Returns all the :class:`Line` objects present in the Document.

        :return: List of Line objects, each representing a line within the Document.
        :rtype: EntityList[Line]
        """
        return EntityList(sum([page.lines for page in self.pages], []))

    @property
    def key_values(self) -> List[KeyValue]:
        """
        Returns all the :class:`KeyValue` objects present in the Document.

        :return: List of KeyValue objects, each representing a key-value pair within the Document.
        :rtype: EntityList[KeyValue]
        """
        return EntityList(sum([page.key_values for page in self.pages], []))

    @property
    def checkboxes(self) -> List[KeyValue]:
        """
        Returns all the :class:`KeyValue` objects with SelectionElements present in the Document.

        :return: List of KeyValue objects, each representing a checkbox within the Document.
        :rtype: EntityList[KeyValue]
        """
        return EntityList(sum([page.checkboxes for page in self.pages], []))

    @property
    def tables(self) -> List[Table]:
        """
        Returns all the :class:`Table` objects present in the Document.

        :return: List of Table objects, each representing a table within the Document.
        :rtype: EntityList[Table]
        """
        return EntityList(sum([page.tables for page in self.pages], []))

    @property
    def queries(self) -> List[Query]:
        """
        Returns all the :class:`Query` objects present in the Document.

        :return: List of Query objects.
        :rtype: EntityList[Query]
        """
        return EntityList(sum([page.queries for page in self.pages], []))

    @property
    def signatures(self) -> List[Signature]:
        """
        Returns all the :class:`Signature` objects present in the Document.

        :return: List of Signature objects.
        :rtype: EntityList[Signature]
        """
        return EntityList(sum([page.signatures for page in self.pages], []))

    @property
    def identity_document(self) -> EntityList[IdentityDocument]:
        """
        Returns all the :class:`IdentityDocument` objects present in the Page.

        :return: List of IdentityDocument objects.
        :rtype: EntityList
        """
        return EntityList(self._identity_documents)

    @identity_document.setter
    def identity_document(self, identity_documents: List[IdentityDocument]):
        """
        Add IdentityDocument objects to the Page.

        :param tables: List of IdentityDocument objects.
        :type identity_documents: list
        """
        self._identity_document = identity_documents

    @property
    def images(self) -> List[Image.Image]:
        """
        Returns all the page images in the Document.

        :return: List of PIL Image objects.
        :rtype: PIL.Image
        """
        return [page.image for page in self._pages]

    @property
    def pages(self) -> List[Page]:
        """
        Returns all the :class:`Page` objects present in the Document.

        :return: List of Page objects, each representing a Page within the Document.
        :rtype: List
        """
        return self._pages

    @pages.setter
    def pages(self, pages: List[Page]):
        """
        Add Page objects to the Document.

        :param pages: List of Page objects, each representing a page within the document.
        No specific ordering is assumed with input.
        :type pages: List[Page]
        """
        self._pages = sorted(pages, key=lambda x: x.page_num)

    def page(self, page_no: int = 0):
        """
        Returns :class:`Page` object/s depending on the input page_no. Follows zero-indexing.

        :param page_no: if int, returns single Page Object, else if list, it returns a list of
                        Page objects.
        :type page_no: int if single page, list of int if multiple pages

        :return: Filters and returns Page objects depending on the input page_no
        :rtype: Page or List[Page]
        """
        if isinstance(page_no, int):
            return self.pages[page_no]
        elif isinstance(page_no, list):
            return [self.pages[num] for num in page_no]
        else:
            raise InputError("page_no parameter doesn't match required data type.")

    def __repr__(self):
        return os.linesep.join(
            [
                "This document holds the following data:",
                f"Pages - {len(self.pages)}",
                f"Words - {len(self.words)}",
                f"Lines - {len(self.lines)}",
                f"Key-values - {len(self.key_values)}",
                f"Checkboxes - {len(self.checkboxes)}",
                f"Tables - {len(self.tables)}",
                f"Queries - {len(self.queries)}",
                f"Signatures - {len(self.signatures)}",
                f"Identity Documents - {len(self.identity_documents)}",
                f"Expense Documents - {len(self.expense_documents)}",
            ]
        )

    def to_trp2(self) -> TDocument:
        """
        Parses the response to the trp2 format for backward compatibility

        :return: TDocument object that can be used with the older Textractor libraries
        :rtype: TDocument
        """
        if not self._trp2_document:
            self._trp2_document = TDocumentSchema().load(self.response)
        return self._trp2_document

    def visualize(self, *args, **kwargs):
        return EntityList(self.pages).visualize(*args, **kwargs)

    def keys(self, include_checkboxes: bool = True) -> List[str]:
        """
        Prints all keys for key-value pairs and checkboxes if the document contains them.

        :param include_checkboxes: True/False. Set False if checkboxes need to be excluded.
        :type include_checkboxes: bool

        :return: List of strings containing key names in the Document
        :rtype: List[str]
        """
        keys = []
        keys = [keyvalue.key for keyvalue in self.key_values]
        if include_checkboxes:
            keys += [keyvalue.key for keyvalue in self.checkboxes]
        return keys

    def filter_checkboxes(
        self, selected: bool = True, not_selected: bool = True
    ) -> List[KeyValue]:
        """
        Return a list of :class:`KeyValue` objects containing checkboxes if the document contains them.

        :param selected: True/False Return SELECTED checkboxes
        :type selected: bool
        :param not_selected: True/False Return NOT_SELECTED checkboxes
        :type not_selected: bool

        :return: Returns checkboxes that match the conditions set by the flags.
        :rtype: EntityList[KeyValue]
        """

        checkboxes = EntityList([])
        for page in self.pages:
            checkboxes.extend(
                page.filter_checkboxes(selected=selected, not_selected=not_selected)
            )
        return checkboxes

    def get_words_by_type(self, text_type: TextTypes = TextTypes.PRINTED) -> List[Word]:
        """
        Returns list of :class:`Word` entities that match the input text type.

        :param text_type: TextTypes.PRINTED or TextTypes.HANDWRITING
        :type text_type: TextTypes
        :return: Returns list of Word entities that match the input text type.
        :rtype: EntityList[Word]
        """
        if not self.words:
            logging.warn("Document contains no word entities.")
            return []

        filtered_words = EntityList()
        for page in self.pages:
            filtered_words.extend(page.get_words_by_type(text_type=text_type))
        return filtered_words

    def search_words(
        self,
        keyword: str,
        top_k: int = 1,
        similarity_metric: SimilarityMetric = SimilarityMetric.LEVENSHTEIN,
        similarity_threshold: float = 0.6,
    ) -> List[Word]:
        """
        Return a list of top_k words that match the keyword.

        :param keyword: Keyword that is used to query the document.
        :type keyword: str
        :param top_k: Number of closest word objects to be returned
        :type top_k: int
        :param similarity_metric: SimilarityMetric.COSINE, SimilarityMetric.EUCLIDEAN or SimilarityMetric.LEVENSHTEIN. SimilarityMetric.COSINE is chosen as default.
        :type similarity_metric: SimilarityMetric
        :param similarity_threshold: Measure of how similar document key is to queried key. default=0.6
        :type similarity_threshold: float

        :return: Returns a list of words that match the queried key sorted from highest
                 to lowest similarity.
        :rtype: EntityList[Word]
        """

        top_n_words = []
        for page in self.pages:
            top_n_words.extend(
                page._search_words_with_similarity(
                    keyword=keyword,
                    top_k=top_k,
                    similarity_metric=similarity_metric,
                    similarity_threshold=similarity_threshold,
                )
            )

        top_n_words = sorted(top_n_words, key=lambda x: x[0], reverse=True)[:top_k]
        top_n_words = EntityList([ent[1] for ent in top_n_words])

        return top_n_words

    def search_lines(
        self,
        keyword: str,
        top_k: int = 1,
        similarity_metric: SimilarityMetric = SimilarityMetric.LEVENSHTEIN,
        similarity_threshold: float = 0.6,
    ) -> List[Line]:
        """
        Return a list of top_k lines that contain the queried keyword.

        :param keyword: Keyword that is used to query the document.
        :type keyword: str
        :param top_k: Number of closest line objects to be returned
        :type top_k: int
        :param similarity_metric: SimilarityMetric.COSINE, SimilarityMetric.EUCLIDEAN or SimilarityMetric.LEVENSHTEIN. SimilarityMetric.COSINE is chosen as default.
        :type similarity_metric: SimilarityMetric
        :param similarity_threshold: Measure of how similar document key is to queried key. default=0.6
        :type similarity_threshold: float

        :return: Returns a list of lines that contain the queried key sorted from highest
                 to lowest similarity.
        :rtype: EntityList[Line]
        """
        if not isinstance(similarity_metric, SimilarityMetric):
            raise InputError(
                "similarity_metric parameter should be of SimilarityMetric type. Find input choices from textractor.data.constants"
            )

        top_n_lines = []
        for page in self.pages:
            top_n_lines.extend(
                page._search_lines_with_similarity(
                    keyword=keyword,
                    top_k=top_k,
                    similarity_metric=similarity_metric,
                    similarity_threshold=similarity_threshold,
                )
            )

        top_n_lines = EntityList([ent[1] for ent in top_n_lines][:top_k])

        return top_n_lines

    # KeyValue entity related functions
    def get(
        self,
        key: str,
        top_k_matches: int = 1,
        similarity_metric: SimilarityMetric = SimilarityMetric.LEVENSHTEIN,
        similarity_threshold: float = 0.6,
    ):
        """
        Return upto top_k_matches of key-value pairs for the key that is queried from the document.

        :param key: Query key to match
        :type key: str
        :param top_k_matches: Maximum number of matches to return
        :type top_k_matches: int
        :param similarity_metric: SimilarityMetric.COSINE, SimilarityMetric.EUCLIDEAN or SimilarityMetric.LEVENSHTEIN. SimilarityMetric.COSINE is chosen as default.
        :type similarity_metric: SimilarityMetric
        :param similarity_threshold: Measure of how similar document key is to queried key. default=0.6
        :type similarity_threshold: float

        :return: Returns a list of key-value pairs that match the queried key sorted from highest to lowest similarity.
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
            return EntityList([])

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
            f"csv file stored at location {os.path.join(os.getcwd(),filepath)}"
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
        export_str = ""
        index = 1
        if include_kv and not self.key_values:
            logging.warning("Document does not contain key-values.")
        elif include_kv:
            for kv in self.key_values:
                export_str += (
                    f"{index}. {kv.key.__repr__()} : {kv.value.__repr__()}{os.linesep}"
                )
                index += 1

        if include_checkboxes and not self.checkboxes:
            logging.warning("Document does not contain checkbox elements.")
        elif include_checkboxes:
            for kv in self.checkboxes:
                export_str += f"{index}. {kv.key.__repr__()} : {kv.value.children[0].status.name}{os.linesep}"
                index += 1

        with open(filepath, "w") as text_file:
            text_file.write(export_str)
        logging.info(
            f"txt file stored at location {os.path.join(os.getcwd(),filepath)}"
        )

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

    def independent_words(self):
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

    def return_duplicates(self):
        """
        Returns a dictionary containing page numbers as keys and list of :class:`EntityList` objects as values.
        Each :class:`EntityList` instance contains the key-values and the last item is the table which contains duplicate information.
        This function is intended to let the Textract user know of duplicate objects extracted by the various Textract models.

        :return: Dictionary containing page numbers as keys and list of EntityList objects as values.
        :rtype: Dict[page_num, List[EntityList[DocumentEntity]]]
        """
        document_duplicates = defaultdict(list)

        for page in self.pages:
            document_duplicates[page.page_num].extend(page.return_duplicates())

        return document_duplicates

    def directional_finder(
        self,
        word_1: str = "",
        word_2: str = "",
        page: int = -1,
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
        :param page: page number of the page in the document to search the entities in.
        :type page: int, required
        :param prefix: User provided prefix to prepend to the key . Without prefix, the method acts as a search by geometry function
        :type prefix: str, optional
        :param entities: List of DirectionalFinderType inputs.
        :type entities: List[DirectionalFinderType]

        :return: Returns the EntityList of modified key-value and/or checkboxes
        :rtype: EntityList
        """

        if not word_1 or page == -1:
            return EntityList([])

        x1, x2, y1, y2 = self._get_coords(word_1, word_2, direction, page)

        if x1 == -1:
            return EntityList([])

        page_obj = self.pages[page - 1]
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
        """Return key-values and checkboxes in entitylist present in the direction given with respect to the coordinates."""
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

    def _get_coords(self, word_1, word_2, direction, page):
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
        word_1_objects = (
            [word for word in word_1_objects if word.page == page] if page != -1 else []
        )

        if not word_1_objects:
            logging.warning(f"{word_1} not found in page {page}")
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
            word_2_objects = [word for word in word_2_objects if word.page == page]
            if not word_2_objects:
                logging.warning(f"{word_2} not found in page {page}")
                return -1, -1, -1, -1
            else:
                word_2_obj = word_2_objects[0]
                x2, y2 = word_2_obj.bbox.x, word_2_obj.bbox.y
        else:
            x2, y2 = x1, y1

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
