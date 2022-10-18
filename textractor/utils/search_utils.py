"""Utility functions for Document search"""

try:
    import numpy as np
except ImportError:
    # No need to log it here as numpy is only used if SentenceTransformers is used
    # The latter has numpy as dependency.
    pass

from textractor.data.constants import SimilarityMetric
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance
from textractor.exceptions import MissingDependencyException


from textractor.data.constants import (
    IS_COLUMN_HEAD,
    IS_FOOTER_CELL,
    IS_TITLE_CELL,
    IS_SUMMARY_CELL,
    IS_SECTION_TITLE_CELL,
    CellTypes,
)


class SearchUtils:
    model = None
    util = None
    model_string = "all-MiniLM-L6-v2"

    @classmethod
    def get_word_similarity(
        cls, word_1: str, word_2: str, similarity_metric: SimilarityMetric
    ) -> float:
        """
        Returns the extent of similarity between the input words using the similarity_metric input by the user.

        :param word_1: First word to check for similarity
        :type word_1: str
        :param word_2: Second word to check for similarity
        :type word_2: str
        :param similarity_metric: The function supports one of 3 metrics \
                                * Levenshtein distance/ edit distance \
                                * Euclidean distance \
                                * Cosine distance
        :type similarity_metric: str

        :return: Returns the similarity measure calculated based on the metric for the 2 input words.
        :rtype: float
        """
        if cls.model is None and similarity_metric != SimilarityMetric.LEVENSHTEIN:
            try:
                from sentence_transformers import SentenceTransformer, util
            except ImportError:
                raise MissingDependencyException(
                    "sentence_transformers is not installed. Use SimilarityMetric.LEVENSHTEIN."
                )
            cls.model = SentenceTransformer(cls.model_string)
            cls.util = util

        if similarity_metric == SimilarityMetric.LEVENSHTEIN:
            return normalized_damerau_levenshtein_distance(
                word_1.lower(), word_2.lower()
            )
        elif similarity_metric == SimilarityMetric.EUCLIDEAN:
            ref_word_emb = cls.model.encode([word_1])
            word_emb = cls.model.encode([word_2])
            dist = np.linalg.norm(ref_word_emb - word_emb)
            return dist
        else:
            ref_word_emb = cls.model.encode([word_1])
            word_emb = cls.model.encode([word_2])
            similarity = cls.util.cos_sim(ref_word_emb, word_emb)
            return similarity.item()


def jaccard_similarity(list_1: list, list_2: list) -> float:
    """
    Calculates Jaccard similarity between the 2 input lists.

    :param list_1: First list to check for similarity
    :type list_1: list
    :param list_2: Second list to check for similarity
    :type list_2: list

    :return: Returns the similarity measure calculated for the 2 input lists.
    :rtype: float
    """

    set_1 = set(list_1)
    set_2 = set(list_2)
    return float(len(set_1.intersection(set_2)) / len(set_1.union(set_2)))


def get_metadata_attr_name(cell_atr):
    """
    Returns metadata attribute mapping to the input CellType.

    :param cell_atr: Input cell type
    :type: enum
    :return: Returns metadata attribute mapping to the input CellType.
    :rtype: str
    """
    cell_map = {
        CellTypes.COLUMN_HEADER: IS_COLUMN_HEAD,
        CellTypes.SECTION_TITLE: IS_SECTION_TITLE_CELL,
        CellTypes.SUMMARY_CELL: IS_SUMMARY_CELL,
        CellTypes.FLOATING_TITLE: IS_TITLE_CELL,
        CellTypes.FLOATING_FOOTER: IS_FOOTER_CELL,
    }
    try:
        return cell_map[cell_atr]
    except:
        return ""
