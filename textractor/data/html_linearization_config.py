import os
from dataclasses import dataclass

from textractor.data.text_linearization_config import TextLinearizationConfig

@dataclass
class HTMLLinearizationConfig(TextLinearizationConfig):
    """
    This :class:`HTMLLinearizationConfig` is a convenience configuration for converting a Document or DocumentEntity to HTML.
    For a description of the parameters see :class:`TextLinearizationConfig`.
    """

    title_prefix: str = "<h1>"

    title_suffix: str = "</h1>"

    section_header_prefix: str = "<h2>"

    section_header_suffix: str = "</h2>"

    text_prefix: str = "<p>"

    text_suffix: str = "</p>"

    table_prefix: str = "<table>"

    table_suffix: str = "</table>"

    table_row_prefix: str = "<tr>"

    table_row_suffix: str = "</tr>"

    table_cell_header_prefix: str = "<th>"

    table_cell_header_suffix: str = "</th>"

    table_cell_prefix: str = "<td>"

    table_cell_suffix: str = "</td>"

    table_column_separator: str = ""
