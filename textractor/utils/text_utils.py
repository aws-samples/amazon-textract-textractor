from functools import cmp_to_key
import os
from typing import List, Tuple

from textractor.data.text_linearization_config import TextLinearizationConfig
from textractor.entities.bbox import BoundingBox
from textractor.entities.line import Line
from textractor.entities.word import Word
from textractor.entities.document_entity import DocumentEntity

def compare_bounding_box(a, b):
    ha = a.bbox.height
    hb = b.bbox.height

    delta = (ha + hb) / 3.5

    ay_mid = a.bbox.y + (ha / 2.0)
    by_mid = b.bbox.y + (hb / 2.0)

    if abs(ay_mid - by_mid) < delta:
        if a.bbox.x > b.bbox.x:
            return 1
        else:
            return -1

    else:
        if ay_mid > by_mid:
            return 1
        else:
            return -1

def group_elements_horizontally(
    elements: List[DocumentEntity], overlap_ratio: float = 0.5
) -> List[List[DocumentEntity]]:
    """
    Groups DocumentEntity objects based on their height using an overlap heuristic

    :param elements: DocumentEntity list
    :type elements: List[DocumentEntity]
    :param overlap_ratio: Height overlap ratio over which unaligned elements will be combined into a single line, defaults to 0.5
    :type overlap_ratio: float, optional
    :return: DocumentEntity sub-groups
    :rtype: List[List[DocumentEntity]]
    """
    sorted_elements = sorted(elements, key=cmp_to_key(compare_bounding_box))

    def vertical_overlap(line1, line2):
        top = max(line1.bbox.y, line2.bbox.y)
        bottom = min(line1.bbox.y + line1.bbox.height, line2.bbox.y + line2.bbox.height)
        return max(bottom - top, 0)

    def should_group(line, group):
        if not group:
            return False
        max_height = max(l.bbox.height for l in group)
        total_overlap = sum(vertical_overlap(line, l) for l in group)
        return total_overlap / max_height >= overlap_ratio

    grouped_elements = []
    if not sorted_elements:
        return grouped_elements

    current_group = [sorted_elements[0]]
    for element in sorted_elements[1:]:
        if "Table" in element.__class__.__name__:
            if current_group:
                grouped_elements.append(current_group)
            grouped_elements.append([element])
            current_group = []
        elif not current_group:  # if the group is emtpy add the line
            current_group.append(element)
        elif should_group(element, current_group):
            current_group.append(element)
        else:
            grouped_elements.append(current_group)
            current_group = [element]
    grouped_elements.append(current_group)
    return grouped_elements


def linearize_children(
    elements: List[DocumentEntity],
    config: TextLinearizationConfig = TextLinearizationConfig(),
    no_new_lines: bool = False,
    is_layout_table: bool = False,
) -> Tuple[str, List[Word]]:
    """
    Convert the words in this group into lines, keeping all words from the same lines together
    For example this is useful when trying to keep together words from the same cell that might be from lines
    Spanning across several cells

    :param elements: _description_
    :type elements: List[DocumentEntity]
    :param config: Text linearization configuration object, defaults to TextLinearizationConfig()
    :type config: TextLinearizationConfig, optional
    :param no_new_lines: Removes new lines in the output (single paragrph mode), defaults to False
    :type no_new_lines: bool, optional
    :param is_layout_table: If the element is a layout table we use the column separator instead of the regular separator, defaults to False
    :type is_layout_table: bool, optional
    :return: Tuple of text and linearized words
    :rtype: Tuple[str, List[Word]]
    """

    words_in_elements = [e for e in elements if isinstance(e, Word)]
    lines = set([w.line for w in words_in_elements])
    new_lines = []
    for line in lines:
        if line is None:
            continue
        new_lines.append(
            Line(
                line.id,
                line.bbox,
                sorted(
                    [w for w in words_in_elements if w.line is not None and w.line.id == line.id],
                    key=lambda x: x.bbox.x,
                ),
            )
        )
    elements = [e for e in elements if not isinstance(e, Word)] + new_lines
    grouped_elements = group_elements_horizontally(
        elements, config.heuristic_overlap_ratio
    )

    def part_of_same_paragraph(element1, element2, config=config):
        if (
            "Line" in element1.__class__.__name__
            and "Line" in element2.__class__.__name__
        ):
            return abs(
                element1.bbox.x - element2.bbox.x
            ) <= config.heuristic_h_tolerance * element1.bbox.width and abs(
                element1.bbox.y + element1.bbox.height - element2.bbox.y
            ) <= config.heuristic_line_break_threshold * min(
                element1.bbox.height, element2.bbox.height
            )
        return False

    result = ""
    words_output = []
    prev_element = None

    for group_idx, group in enumerate(grouped_elements):
        sorted_group = sorted(group, key=lambda element: element.bbox.x)
        if not sorted_group:
            continue

        added_words = set()
        for idx, element in enumerate(sorted_group):
            text_element, words_element = element.get_text_and_words(config)
            if "Table" in element.__class__.__name__ and len(words_element):
                result += text_element
                for w in words_element:
                    added_words.add(w.id)
                words_output += words_element
            elif "KeyValue" in element.__class__.__name__ and len(words_element):
                separator = (
                    config.same_paragraph_separator
                    if prev_element and part_of_same_paragraph(prev_element, element, config) else
                    config.same_layout_element_separator
                )
                result += separator + text_element
                for w in words_element:
                    added_words.add(w.id)
                words_output += words_element
            elif prev_element is None:
                result += text_element
                words_output += words_element
            elif is_layout_table:
                result += (
                    "" if idx == 0 else config.table_column_separator
                ) + text_element
                words_output += words_element
            elif part_of_same_paragraph(prev_element, element, config):
                result += config.same_paragraph_separator + text_element
                words_output += words_element
            else:
                result += config.same_layout_element_separator + text_element
                words_output += words_element

            # FIXME: Seems like this would be mostly needed
            # result += os.linesep
            prev_element = element

        if is_layout_table:
            result += config.table_row_separator
        else:
            result += config.same_layout_element_separator

        # We make a dummy line element with the bbox from the previous group
        prev_element = Line(
            "", BoundingBox.enclosing_bbox([o.bbox for o in sorted_group])
        )

    output = "".join(result)

    if no_new_lines:
        while os.linesep in output:
            output = output.replace(os.linesep, " ")
        while "  " in output:
            output = output.replace("  ", " ")

    return output, words_output


def is_distinct_entity(entity1: DocumentEntity, entity2: DocumentEntity) -> bool:
    """
    Check whether two DocumentEntity have word overlap

    :param entity1: First DocumentEntity
    :type entity1: DocumentEntity
    :param entity2: Second DocumentEntity
    :type entity2: DocumentEntity
    :return: Entities overlap as a boolean
    :rtype: bool
    """
    for w in entity1.words():
        if w in entity2.words():
            return False
    return True
