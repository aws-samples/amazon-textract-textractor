import os
from dataclasses import dataclass


@dataclass
class TextLinearizationConfig:
    """
    The :class:`TextLinearizationConfig` object defines how a document is linearized into a text string
    """

    remove_new_lines_in_leaf_elements: bool = True  #: Removes new lines in leaf layout elements, this removes extra whitespace

    max_number_of_consecutive_new_lines: int = 2  #: Removes extra whitespace

    max_number_of_consecutive_spaces: int = None  #: Removes extra whitespace (None skips whitespace removal)

    hide_header_layout: bool = False  #: Hide headers layouts in the linearized output

    hide_footer_layout: bool = False  #: Hide footers layouts in the linearized output

    hide_figure_layout: bool = False  #: Hide figures layouts in the linearized output

    hide_table_layout: bool = False #: Hide tables layouts in the linearized output

    hide_key_value_layout: bool = False #: Hide key-value layouts in the linearized output

    hide_page_num_layout: bool = False  #: Hide page numbers in the linearized output

    page_num_prefix: str = ""  #: Prefix for page number layout elements

    page_num_suffix: str = ""  #: Suffix for page number layout elements

    same_paragraph_separator: str = (
        " "  #: Separator to use when combining elements within a text block
    )

    same_layout_element_separator: str = (
        "\n" #: Separator to use when two elements are in the same layout element
    )

    layout_element_separator: str = (
        os.linesep * 2
    )  #: Separator to use when combining linearized layout elements

    list_element_separator: str = os.linesep  #: Separator for elements in a list layout

    list_layout_prefix: str = ""  #: Prefix for list layout elements (parent)

    list_layout_suffix: str = ""  #: Suffix for list layout elements (parent)

    list_element_prefix: str = ""  #: Prefix for elements in a list layout (children)

    list_element_suffix: str = ""  #: Suffix for elements in a list layout (children)

    title_prefix: str = ""  #: Prefix for title layout elements

    title_suffix: str = ""  #: Suffix for title layout elements

    table_layout_prefix: str = os.linesep * 2  #: Prefix for table elements

    table_layout_suffix: str = os.linesep  #: Suffix for table elements

    table_remove_column_headers: bool = False  #: Remove pandas index column headers from tables

    table_column_header_threshold: float = 0.9 #: Threshold for a row to be selected as header when rendering as markdown. 0.9 means that 90% of the cells must have the is_header_cell flag. 

    table_linearization_format: str = "plaintext"  #: How to represent tables in the linearized output. Choices are plaintext, markdown or html.

    table_add_title_as_caption: bool = False #: When using html linearization format, adds the title inside the table as <caption></caption>

    # FIXME
    table_add_footer_as_paragraph: bool = False 

    table_tabulate_format: str = "github"  #: Markdown tabulate format to use when table are linearized as markdown

    table_tabulate_remove_extra_hyphens: bool = False  #: By default markdown tables will have N hyphens to preserve alignement, this reduces the number of hyphens to 1, which is the minimum number allowed by the GitHub Markdown spec

    table_duplicate_text_in_merged_cells: bool = False #: Duplicate text in merged cells to preserve line alignment

    table_flatten_headers: bool = False #: Flatten table headers into a single row, unmerging the cells horizontally

    table_min_table_words: int = 0  #: Threshold below which tables will be rendered as words instead of using table layout

    table_column_separator: str = "\t"  #: Table column separator, used when linearizing layout tables, not used if AnalyzeDocument was called with the TABLES feature

    table_flatten_semi_structured_as_plaintext: bool = False #: Ignores table structure for SEMI_STRUCTURED tables and returns them as text

    table_prefix: str = ""

    table_suffix: str = ""

    table_row_separator: str = os.linesep  #: Table row separator

    table_row_prefix: str = "" #: Prefix for table row

    table_row_suffix: str = "" #: Suffix for table row

    table_cell_prefix: str = "" #: Prefix for table cell

    table_cell_suffix: str = "" #: Suffix for table cell

    table_cell_header_prefix: str = "" #: Prefix for header cell

    table_cell_header_suffix: str = "" #: Suffix for header cell

    table_cell_empty_cell_placeholder: str = "" #: Placeholder for empty cells

    table_cell_merge_cell_placeholder: str = "" #: Placeholder for merged cell

    table_cell_left_merge_cell_placeholder: str = "" #: Placeholder for left merge cell (L) see: 

    table_cell_top_merge_cell_placeholder: str = "" #: Placeholder for left merge cell (T)

    table_cell_cross_merge_cell_placeholder: str = "" #: Placeholder for left merge cell (X)

    table_title_prefix: str = "" #: Prefix for table title if it is outside of the table (floating)
    
    table_title_suffix: str = "" #: Suffix for table title if it is outside of the table (floating)

    table_footers_prefix: str = "" #: Prefix for table footers if they are outside of the table (floating)
    
    table_footers_suffix: str = "" #: Suffix for table footers if they are outside of the table (floating)

    header_prefix: str = ""  #: Prefix for header layout elements

    header_suffix: str = ""  #: Suffix for header layout elements

    section_header_prefix: str = ""  #: Prefix for section header layout elements

    section_header_suffix: str = ""  #: Suffix for section header layout elements

    text_prefix: str = ""  #: Prefix for text layout elements

    text_suffix: str = ""  #: Suffix for text layout elements

    key_value_layout_prefix: str = ""  #: Prefix for key_value layout elements (not for individual key-value elements)

    key_value_layout_suffix: str = ""  #: Suffix for key_value layout elements (not for individual key-value elements)

    key_value_prefix: str = "" #: Prefix for key-value elements

    key_value_suffix: str = "" #: Suffix for key-value elements

    key_prefix: str = ""  #: Prefix for key elements

    key_suffix: str = " "  #: Suffix for key elements

    value_prefix: str = ""  #: Prefix for value elements

    value_suffix: str = ""  #: Suffix for value elements

    entity_layout_prefix: str = "" #: Prefix for LAYOUT_ENTITY elements (layout elements without a predicted layout type)

    entity_layout_suffix: str = "" #: Suffix for LAYOUT_ENTITY elements (layout elements without a predicted layout type)

    figure_layout_prefix: str = "" #: Prefix for figure layout elements 
    
    figure_layout_suffix: str = "" #: Suffix for figure layout elements

    footer_layout_prefix: str = "" #: Prefix for figure layout elements 
     
    footer_layout_suffix: str = "" #: Suffix for figure layout elements

    selection_element_selected: str = (
        "[X]"  #: Representation for selection element when selected
    )

    selection_element_not_selected: str = (
        "[ ]"  #: Representation for selection element when not selected
    )

    heuristic_h_tolerance: float = 0.3  #: How much the line below and above the current line should differ in width to be separated

    heuristic_line_break_threshold: float = 0.9  #: How much space is acceptable between two lines before splitting them. Expressed in multiple of min heights

    heuristic_overlap_ratio: float = 0.5  #: How much vertical overlap is tolerated between two subsequent lines before merging them into a single line

    signature_token: str = "[SIGNATURE]"  #: Signature representation in the linearized text

    add_prefixes_and_suffixes_as_words: bool = False #: Controls if the prefixes/suffixes will be inserted in the words returned by `get_text_and_words`

    add_prefixes_and_suffixes_in_text: bool = True #: Controls if the prefixes/suffixes will be added to the linearized text
