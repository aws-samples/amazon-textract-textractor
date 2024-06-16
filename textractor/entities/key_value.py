"""
The :class:`KeyValue` entity is a document entity representing the Forms output. The key in :class:`KeyValue` are typically words 
and the :class:`Value` could be :class:`Word` elements or :class:`SelectionElement` in case of checkboxes.

This class contains the associated metadata with the :class:`KeyValue` entity including the entity ID, 
bounding box information, value, existence of checkbox, page number, Page ID and confidence of detection.
"""

import logging
from typing import List
import uuid

from textractor.entities.word import Word
from textractor.entities.value import Value
from textractor.exceptions import InputError
from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.data.constants import TextTypes
from textractor.data.text_linearization_config import TextLinearizationConfig
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

        self._words: EntityList[Word] = []
        self.contains_checkbox = contains_checkbox
        self._confidence = confidence / 100
        self._value: Value = value
        self.selection_status = False
        self._page = None
        self._page_id = None

    @property
    def ocr_confidence(self):
        """
        Return the average OCR confidence
        :return:
        """
        key_confidences = [w.confidence for w in self.key]
        value_confidences = (
            [w.confidence for w in self.value.words] if self.value else []
        )

        key_confidence = (
            sum(key_confidences) / len(key_confidences) if key_confidences else None
        )
        value_confidence = (
            sum(value_confidences) / len(value_confidences)
            if value_confidences
            else None
        )
        return {
            "key_average": key_confidence,
            "key_min": min(key_confidences) if key_confidences else None,
            "value_average": value_confidence,
            "value_min": min(value_confidences) if value_confidences else None,
        }

    @property
    def words(self) -> List[Word]:
        """
        Returns all the :class:`Word` objects present in the key and value of the :class:`KeyValue` object.

        :return words: List of Word objects, each representing a word within the KeyValue entity.
        :rtype: EntityList[Word]
        """
        value_words = self.value.words if self.value is not None and not self.contains_checkbox else []
        return EntityList(
            sorted(self._words + value_words, key=lambda x: x.bbox.x + x.bbox.y)
        )

    @property
    def key(self):
        """
        :return: Returns :class:`EntityList[Word]` object (a list of words) associated with the key.
        :rtype: EntityList[Word]
        """
        if not self._words:
            logging.info("Key contains no words objects.")
            return []
        return self._words

    @key.setter
    def key(self, words: List[Word]):
        """
        Add :class:`Word` objects to the Key.

        :param words: List of Word objects, each representing a word within the Key.
        No specific ordering is assumed.
        :type words: list
        """
        self._words = EntityList(words)

    @property
    def value(self) -> Value:
        """
        :return: Returns the :class:`Value` mapped to the key if it has been assigned.
        :rtype: Value
        """
        if self._value is None:
            logging.warning(
                "Asked for a value but it was never attributed "
                "-> make sure to assign value to key with the `kv.value = <Value Object>` property setter"
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
        """
        For KeyValues containing a selection item, returns its `is_selected` status

        :return: Selection status of a selection item key value pair
        :rtype: bool
        """
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

    def get_text_and_words(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ):
        key_text, key_words = " ".join([w.text for w in self.key]), self.key
        value_text, value_words = self.value.get_text_and_words(config) if self.value else ("", "")
        words = []
        if not len(key_text) and not len(value_text):
            return "", []
        s = config.key_suffix.strip()
        key_suffix = (
            config.key_suffix
            if not (len(key_text) > len(s) and key_text[-len(s) :] == s)
            else " "
        )
        if config.add_prefixes_and_suffixes_in_text:
            text = f"{config.key_value_prefix}{config.key_prefix}{key_text}{key_suffix}{value_text}{config.key_value_suffix}"
        else:
            text = f"{key_text}{config.same_paragraph_separator}{value_text}"

        if config.add_prefixes_and_suffixes_as_words:
            words += [Word(str(uuid.uuid4()), self.bbox, config.key_value_prefix, is_structure=True)] if config.key_value_prefix else []
            if key_words:
                words += (
                    ([Word(str(uuid.uuid4()), BoundingBox.enclosing_bbox(self.key), config.key_prefix, is_structure=True)] if config.key_prefix else []) +
                    key_words +
                    ([Word(str(uuid.uuid4()), BoundingBox.enclosing_bbox(self.key), config.key_suffix, is_structure=True)] if config.key_suffix else [])
                )
            if value_words: 
                words += value_words
            words += ([Word(str(uuid.uuid4()), self.bbox, config.key_value_suffix, is_structure=True)] if config.key_value_suffix else [])
        else:
            words += key_words + value_words

        for w in words:
            w.kv_id = str(self.id)
            w.kv_bbox = self.bbox

        return text, words

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
