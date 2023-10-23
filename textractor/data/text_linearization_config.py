import os
from dataclasses import dataclass


@dataclass
class TextLinearizationConfig:
    """
    The :class:`TextLinearizationConfig` object defines how a document is linearized into a text string
    """

    # Include tables in the linearized output
    linearize_table: bool = True

    # Include form key and values in the linearized output
    linearize_key_values: bool = True

    # Removes new lines in leaf layout elements, this removes extra whitespace
    remove_new_lines_in_leaf_elements: bool = True

    # Removes extra whitespace
    max_number_of_consecutive_new_lines: int = 2

    # Hide headers in the linearized output
    hide_header_layout: bool = False

    # Hide footers in the linearized output
    hide_footer_layout: bool = False

    # Hide figures in the linearized output
    hide_figure_layout: bool = False

    # Hide page numbers in the linearized output
    hide_page_num_layout: bool = False

    # Separator to use when combining elements within a text block
    same_paragraph_separator: str = " "

    # Separator to use when combining linearized layout elements
    layout_element_separator: str = os.linesep * 2

    # Separator for elements in a list layout
    list_element_separator: str = os.linesep

    # Prefix for list layout elements (parent)
    list_layout_prefix: str = ""

    # Suffix for list layout elements (parent)
    list_layout_suffix: str = ""

    # Prefix for elements in a list layout (children)
    list_element_prefix: str = ""

    # Suffix for elements in a list layout (children)
    list_element_suffix: str = ""

    # Prefix for title layout elements
    title_prefix: str = ""

    # Suffix for title layout elements
    title_suffix: str = ""

    # Prefix for table elements
    table_layout_prefix: str = os.linesep * 2

    # Suffix for table elements
    table_layout_suffix: str = os.linesep

    # Remove column headers from tables
    table_remove_column_headers: bool = False

    # How to represent tables in the linearized output. Choices are plaintext or markdown.
    table_linearization_format: str = "plaintext"

    # Markdown tabulate format to use when table are linearized as markdown
    table_tabulate_format: str = "github"

    # Threshold below which tables will be rendered as words instead of using table layout
    table_min_table_words: int = 0

    # Table column separator, used when linearizing layout tables, not used if AnalyzeDocument was called with the TABLES feature
    table_column_separator: str = "\t"

    # Table row separator
    table_row_separator: str = os.linesep

    # Prefix for section header layout elements
    section_header_prefix: str = ""

    # Suffix for section header layout elements
    section_header_suffix: str = ""

    # Prefix for text layout elements
    text_prefix: str = ""

    # Suffix for text layout elements
    text_suffix: str = ""

    # Prefix for key_value layout elements (not for individual key-value elements)
    key_value_layout_prefix: str = os.linesep * 2

    # Suffix for key_value layout elements (not for individual key-value elements)
    key_value_layout_suffix: str = ""

    # Prefix for key elements
    key_prefix: str = ""

    # Suffix for key elements
    key_suffix: str = " "

    # Prefix for value elements
    value_prefix: str = ""

    # Suffix for value elements
    value_suffix: str = ""

    # Representation for selection element when selected
    selection_element_selected: str = "[X]"

    # Representation for selection element when not selected
    selection_element_not_selected: str = "[ ]"

    # How much the line below and above the current line should differ in width to be separated
    heuristic_h_tolerance: float = 0.3

    # How much space is acceptable between two lines before splitting them. Expressed in multiple of min heights
    heuristic_line_break_threshold: float = 0.9

    # How much vertical overlap is tolerated between two subsequent lines before merging them into a single line
    heuristic_overlap_ratio: float = 0.5

    # Signature representation in the linearized text
    signature_token = "[SIGNATURE]"
