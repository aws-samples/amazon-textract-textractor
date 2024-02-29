import os
from dataclasses import dataclass

from textractor.data.text_linearization_config import TextLinearizationConfig

@dataclass
class MarkdownLinearizationConfig(TextLinearizationConfig):
    """
    This :class:`MarkdownLinearizationConfig` is a convenience configuration for converting a Document or DocumentEntity to Markdown.
    For a description of the parameters see :class:`TextLinearizationConfig`.
    """

    title_prefix: str = "# "

    table_linearization_format: str = "markdown"

    section_header_prefix: str = "## "

    table_remove_column_headers: bool = True