import statistics
from typing import List
from copy import deepcopy
from collections.abc import Iterable


def flatten(list_of_lists):
    """
    Utility function to flatten a list of lists recursively.

    :param list_of_lists: List containing any depth of lists recursively to be flattened into a single list.
    :type list_of_lists: list
    :return: Flattened list of input list
    :rtype: list
    """
    for x in list_of_lists:
        if isinstance(x, Iterable):
            yield from flatten(x)
        else:
            yield x


def get_indices(numpy_indexing: str = ":", max_val=10) -> List[int]:
    """
    Function to convert numpy indexing format to list of indices to access cells within the Table.

    :param numpy_indexing: string containing start:stop:step format
    :param max_val: maximum rows or columns on the table depending on input.
    :return: Returns the indices of table rows and columns following the numpy indexing format.
    :rtype: list
    """
    indices = []
    assert isinstance(numpy_indexing, str)
    assert ":" in numpy_indexing or numpy_indexing.isdigit()

    if numpy_indexing == "None:None:None":
        indices = list(range(0, max_val))

    else:
        return_indices = numpy_indexing.split(":")
        assert len(return_indices) > 1

        start = (
            int(return_indices[0])
            if return_indices[0] != "" and return_indices[0] != "None"
            else 0
        )
        end = (
            int(return_indices[1])
            if return_indices[1] != "" and return_indices[1] != "None"
            else max_val
        )

        index_range = list(range(start, end))

        if len(return_indices) == 3:
            step = (
                int(return_indices[2])
                if return_indices[2] != "" and return_indices[2] != "None"
                else 1
            )
            indices += [i for i in index_range if index_range.index(i) % step == 0]
        else:
            indices = index_range

    return list(set(indices))

def sort_by_position(entities: List) -> List:
    return sorted(entities, key=lambda e: (e.bbox.y + e.bbox.height, e.bbox.x))