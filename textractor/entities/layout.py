"""
Represents a single :class:`Layout` Entity within the :class:`Document`.
The Textract API response returns groups of layout as LAYOUT_* BlockTypes.
"""

import os
from typing import List, Tuple
from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.entities.line import Line
from textractor.entities.word import Word
from textractor.data.constants import (
    LAYOUT_SECTION_HEADER,
    LAYOUT_TITLE,
    LAYOUT_TABLE,
    LAYOUT_FIGURE,
    LAYOUT_FOOTER,
    LAYOUT_HEADER,
    LAYOUT_KEY_VALUE,
    LAYOUT_LIST,
    LAYOUT_PAGE_NUMBER,
    LAYOUT_TEXT,
    LAYOUT_ENTITY,
)
from textractor.data.text_linearization_config import TextLinearizationConfig
from textractor.utils.text_utils import group_elements_horizontally, linearize_children


class Layout(DocumentEntity):
    """
    To create a new :class:`Layout` object we need the following:
    """

    def __init__(
        self,
        entity_id: str,
        bbox: BoundingBox,
        reading_order: int,
        label: str,
        confidence: float = 0,
    ):
        super().__init__(entity_id, bbox)
        self.reading_order = reading_order
        self.confidence = confidence / 100
        self.layout_type = label
        self._page = None
        self._page_id = None

    @property
    def page(self):
        """
        :return: Returns the page number of the page the :class:`Layout` entity is present in.
        :rtype: int
        """
        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the :class:`Layout` entity.

        :param page_num: Page number where the :class:`Layout` entity exists.
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
        Sets the Page ID of the :class:`Layout` entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """
        self._page_id = page_id

    @property
    def text(self):
        return self.get_text()

    @property
    def words(self, config: TextLinearizationConfig = TextLinearizationConfig()):
        _, words = self.get_text_and_words(config)
        return words

    def get_text(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ) -> str:
        """
        Returns the layout object text

        :param config: Text linearization configuration object, defaults to TextLinearizationConfig()
        :type config: TextLinearizationConfig, optional
        :return: Linearized layout object text
        :rtype: str
        """
        return self.get_text_and_words(config)[0]

    def get_text_and_words(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ) -> Tuple[str, List[Word]]:
        """
        Returns the layout object text and words sorted in reading order

        :param config: Text linearization configuration object, defaults to TextLinearizationConfig()
        :type config: TextLinearizationConfig, optional
        :return: Tuple of page text and words
        :rtype: Tuple[str, List[Word]]
        """

        if (
            (self.layout_type == LAYOUT_HEADER and config.hide_header_layout)
            or (self.layout_type == LAYOUT_FOOTER and config.hide_footer_layout)
            or (self.layout_type == LAYOUT_FIGURE and config.hide_figure_layout)
            or (self.layout_type == LAYOUT_PAGE_NUMBER and config.hide_page_num_layout)
        ):
            return "", []
        elif self.layout_type == LAYOUT_LIST:
            final_text = config.list_layout_prefix
            final_words = []
            for i, child in enumerate(
                sorted(self.children, key=lambda x: x.reading_order)
            ):
                child_text, child_words = child.get_text_and_words(config)
                final_text += (
                    (
                        config.list_element_prefix
                        if child_text[: len(config.list_element_prefix)]
                        != config.list_element_prefix
                        else ""
                    )
                    + (
                        child_text.replace("\n", " ")
                        if config.remove_new_lines_in_leaf_elements
                        else child_text
                    )
                    + (
                        config.list_element_separator
                        if i != len(self.children) - 1
                        else ""
                    )
                )
                final_words += child_words
            final_text += config.list_layout_suffix
        elif self.layout_type == LAYOUT_TITLE:
            final_text, final_words = linearize_children(
                self.children, config, no_new_lines=True
            )
            final_text = config.title_prefix + final_text + config.title_suffix
        elif self.layout_type == LAYOUT_SECTION_HEADER:
            final_text, final_words = linearize_children(
                self.children, config, no_new_lines=True
            )
            final_text = (
                config.section_header_prefix + final_text + config.section_header_suffix
            )
        elif self.layout_type == LAYOUT_TEXT:
            final_text, final_words = linearize_children(
                self.children,
                config,
                no_new_lines=True,
            )
        else:
            final_text, final_words = linearize_children(
                self.children,
                config,
                no_new_lines=False,
                is_layout_table=self.layout_type == LAYOUT_TABLE,
            )

        while (
            os.linesep * (config.max_number_of_consecutive_new_lines + 1) in final_text
        ):
            final_text = final_text.replace(
                "\n" * (config.max_number_of_consecutive_new_lines + 1),
                "\n" * config.max_number_of_consecutive_new_lines,
            )

        return final_text, final_words
