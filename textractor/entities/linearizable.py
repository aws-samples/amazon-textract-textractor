"""
:class:`Linearizable` is a class that defines how a component can be linearized (converted to text)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from textractor.data.text_linearization_config import TextLinearizationConfig
from textractor.data.html_linearization_config import HTMLLinearizationConfig
from textractor.data.markdown_linearization_config import MarkdownLinearizationConfig

class Linearizable(ABC):    
    def get_text(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ) -> str:
        """
        Returns the linearized text of the entity

        :param config: Text linearization confi 
        :type config:   
        :return: Linearized text of the entity
        :rtype: str
        """
        text, _ = self.get_text_and_words(config=config)
        return text

    @property
    def text(self) -> str:
        """
        Maps to .get_text()

        :return: Returns the linearized text of the entity
        :rtype: str
        """
        return self.get_text()

    def to_html(
        self,
        config: HTMLLinearizationConfig = HTMLLinearizationConfig()
    ) -> str:
        """
        Returns the HTML representation of the entity

        :return: HTML text of the entity
        :rtype: str
        """
        return self.get_text(config)

    def to_markdown(
        self,
        config: MarkdownLinearizationConfig = MarkdownLinearizationConfig()
    ) -> str:
        """
        Returns the markdown representation of the entity

        :return: Markdown text of the entity
        :rtype: str
        """
        return self.get_text(config)

    @abstractmethod
    def get_text_and_words(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ) -> Tuple[str, List]:
        """
        Used for linearization, returns the linearized text of the entity and the matching words

        :return: Tuple of text and word list
        :rtype: Tuple[str, List[Word]]
        """
        pass
