"""
The :class:`KeyValue` entity is a document entity representing the Forms output. The key in :class:`KeyValue` are typically words 
and the :class:`Value` could be :class:`Word` elements or :class:`SelectionElement` in case of checkboxes.

This class contains the associated metadata with the :class:`KeyValue` entity including the entity ID, 
bounding box information, value, existence of checkbox, page number, Page ID and confidence of detection.
"""

import logging
from typing import List

from textractor.entities.line import Line
from textractor.entities.word import Word
from textractor.entities.value import Value
from textractor.exceptions import InputError
from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.data.constants import TextTypes
from textractor.visualizers.entitylist import EntityList


class KeyValue(DocumentEntity):
    """
    To create a new :class:`KeyValue` object we require the following:

    :param entity_id: Unique identifier of the KeyValue entity.
    :type entity_id: str
    :param bbox: Bounding box of the KeyValue entity.
    :type bbox: BoundingBox
    :param contains_checkbox: True/False to indicate if the value is a checkbox.
    :type contains_checkbox: bool
    :param value: Value object that maps to the KeyValue entity.
    :type value: Value
    :param confidence: confidence with which the entity was detected.
    :type confidence: float
    """

    def __init__(
        self,
        entity_id: str,
        bbox: BoundingBox,
        contains_checkbox: bool = False,
        value: Value = None,
        confidence: float = 0,
    ):
        super().__init__(entity_id, bbox)

        self._words: List[Word] = []
        self.contains_checkbox = contains_checkbox
        self._value: Value = value
        self.selection_status = False
        self.confidence = confidence / 100
        self._page = None
        self._page_id = None

    @property
    def words(self) -> List[Word]:
        """
        Returns all the :class:`Word` objects present in the key and value of the :class:`KeyValue` object.

        :return words: List of Word objects, each representing a word within the KeyValue entity.
        :rtype: EntityList[Word]
        """
        value_words = self.value.words if not self.contains_checkbox else []
        return EntityList(
            sorted(self._words + value_words, key=lambda x: x.bbox.x + x.bbox.y)
        )

    @property
    def key(self):
        """
        :return: Returns :class:`Line` object associated with the key.
        :rtype: Line
        """
        if not self._words:
            logging.warning(f"Key contains no words objects.")
            return []
        else:
            return Line(
                entity_id=self.id,
                bbox=self.bbox,
                words=self._words,
                confidence=self.confidence * 100,
            )

    @key.setter
    def key(self, words: List[Word]):
        """
        Add :class:`Word` objects to the Key.

        :param words: List of Word objects, each representing a word within the Key.
        No specific ordering is assumed.
        :type words: list
        """
        self._words = sorted(words, key=lambda x: x.bbox.x + x.bbox.y)

    @property
    def value(self) -> Value:
        """
        :return: Returns the :class:`Value` mapped to the key if it has been assigned.
        :rtype: Value
        """
        if self._value is None:
            logging.warning(
                f"Asked for a value but it was never attributed "
                f"-> make sure to assign value to key with the `kv.value = <Value Object>` property setter"
            )
            return None
        else:
            return self._value

    @value.setter
    def value(self, value: Value):
        """
        Add :class:`Value` object to the :class:`KeyValue`.

        :param value: Value object, representing a single value associated with the key.
        :type value: Value
        """
        self._value = value

    @property
    def page(self) -> int:
        """
        :return: Returns the page number of the page the :class:`Table` entity is present in.
        :rtype: int
        """
        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the :class:`Table` entity.

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
        Sets the Page ID of the :class:`Table` entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """
        self._page_id = page_id

    def get_words_by_type(self, text_type: str = TextTypes.PRINTED) -> List[Word]:
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
            logging.info("Document contains no word entities.")
            return []
        else:
            return EntityList(
                [word for word in self.words if word.text_type == text_type]
            )

    def is_selected(self) -> bool:
        if self.contains_checkbox:
            if len(self.value.children) == 1:
                return self.value.children[0].is_selected()
            else:
                logging.info(
                    "is_checked() was called on a KeyValue that contains more than one checkbox. Returning first checkbox"
                )
                return self.value.children[0].is_selected()
        else:
            logging.info(
                "is_checked() was called on a KeyValue that does not contain checkboxes. Returning False"
            )
            return False

    def __repr__(self) -> str:
        """
        :return: Returns KeyValue object as a formatted string.
        :rtype: str
        """
        repr_string = " ".join([word.text for word in self._words])

        if self.contains_checkbox:
            repr_string = self.value.__repr__() + " " + repr_string
        else:
            repr_string = repr_string
            repr_string += " : "
            repr_string += self.value.__repr__()
        return repr_string
