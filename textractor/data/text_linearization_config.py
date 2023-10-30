import os
from dataclasses import dataclass


@dataclass
class TextLinearizationConfig:
    """
    The :class:`TextLinearizationConfig` object defines how a document is linearized into a text string
    """

    linearize_table: bool = True #: Include tables in the linearized output

    linearize_key_values: bool = True #: Include form key and values in the linearized output

    remove_new_lines_in_leaf_elements: bool = True #: Removes new lines in leaf layout elements, this removes extra whitespace

    max_number_of_consecutive_new_lines: int = 2 #: Removes extra whitespace

    hide_header_layout: bool = False #: Hide headers in the linearized output

    hide_footer_layout: bool = False #: Hide footers in the linearized output

    hide_figure_layout: bool = False #: Hide figures in the linearized output

    hide_page_num_layout: bool = False #: Hide page numbers in the linearized output

    page_num_prefix: str = "" #: Prefix for page number layout elements

    page_num_suffix: str = "" #: Suffix for page number layout elements

    same_paragraph_separator: str = " " #: Separator to use when combining elements within a text block

    layout_element_separator: str = os.linesep * 2 #: Separator to use when combining linearized layout elements

    list_element_separator: str = os.linesep #: Separator for elements in a list layout

    list_layout_prefix: str = "" #: Prefix for list layout elements (parent)

    list_layout_suffix: str = "" #: Suffix for list layout elements (parent)

    list_element_prefix: str = "" #: Prefix for elements in a list layout (children)

    list_element_suffix: str = "" #: Suffix for elements in a list layout (children)

    title_prefix: str = "" #: Prefix for title layout elements

    title_suffix: str = "" #: Suffix for title layout elements

    table_layout_prefix: str = os.linesep * 2 #: Prefix for table elements

    table_layout_suffix: str = os.linesep #: Suffix for table elements

    table_remove_column_headers: bool = False #: Remove column headers from tables

    table_linearization_format: str = "plaintext" #: How to represent tables in the linearized output. Choices are plaintext or markdown.

    table_tabulate_format: str = "github" #: Markdown tabulate format to use when table are linearized as markdown

    table_min_table_words: int = 0 #: Threshold below which tables will be rendered as words instead of using table layout

    table_column_separator: str = "\t" #: Table column separator, used when linearizing layout tables, not used if AnalyzeDocument was called with the TABLES feature

    table_row_separator: str = os.linesep #: Table row separator

    section_header_prefix: str = "" #: Prefix for section header layout elements

    section_header_suffix: str = "" #: Suffix for section header layout elements

    text_prefix: str = "" #: Prefix for text layout elements

    text_suffix: str = "" #: Suffix for text layout elements

    key_value_layout_prefix: str = os.linesep * 2 #: Prefix for key_value layout elements (not for individual key-value elements)

    key_value_layout_suffix: str = "" #: Suffix for key_value layout elements (not for individual key-value elements)

    key_prefix: str = "" #: Prefix for key elements

    key_suffix: str = " " #: Suffix for key elements

    value_prefix: str = "" #: Prefix for value elements

    value_suffix: str = "" #: Suffix for value elements

    selection_element_selected: str = "[X]" #: Representation for selection element when selected

    selection_element_not_selected: str = "[ ]" #: Representation for selection element when not selected

    heuristic_h_tolerance: float = 0.3 #: How much the line below and above the current line should differ in width to be separated

    heuristic_line_break_threshold: float = 0.9 #: How much space is acceptable between two lines before splitting them. Expressed in multiple of min heights

    heuristic_overlap_ratio: float = 0.5 #: How much vertical overlap is tolerated between two subsequent lines before merging them into a single line

    signature_token = "[SIGNATURE]" #: Signature representation in the linearized text
