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

    header_prefix: str = "<h1>"
    
    header_suffix: str = "</h1>"
    
    section_header_prefix: str = "<h2>"

    section_header_suffix: str = "</h2>"

    text_prefix: str = "<p>"

    text_suffix: str = "</p>"

    entity_layout_prefix: str = "<p>"

    entity_layout_suffix: str = "</p>"

    table_prefix: str = "<table>"

    table_suffix: str = "</table>"

    table_row_prefix: str = "<tr>"

    table_row_suffix: str = "</tr>"

    table_cell_header_prefix: str = "<th>"

    table_cell_header_suffix: str = "</th>"

    table_cell_prefix: str = "<td>"

    table_cell_suffix: str = "</td>"

    table_column_separator: str = ""

    table_linearization_format: str = "html"
    
    table_add_title_as_caption: bool = True
    
    table_add_footer_as_paragraph: bool = True

    table_column_separator: str = ""

    list_layout_prefix: str = "<div>"
    
    list_layout_suffix: str = "</div>"
    
    table_layout_prefix: str = "<div>"

    table_layout_suffix: str = "</div>"
    
    key_value_layout_prefix: str = "<div>"

    key_value_layout_suffix: str = "</div>"
    
    figure_layout_prefix: str = "<div>"
     
    figure_layout_suffix: str = "</div>"

    footer_layout_prefix: str = "<div>"
     
    footer_layout_suffix: str = "</div>"

    page_num_prefix: str = "<div>"
    
    page_num_suffix: str = "</div>"