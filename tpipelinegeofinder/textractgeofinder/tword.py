from dataclasses import dataclass
from typing import Optional, List
import statistics
import math
import difflib
import re
from uuid import uuid4

from trp.trp2 import TPoint
from trp import FieldKey, FieldValue, Line, Word as trpWord

alphanum_regex_with_space = re.compile(r'[^a-zA-Z 0-9]+')
alphanum_regex_without_space = re.compile(r'[^a-zA-Z0-9]+')
number_regex = re.compile("[0-9]")


def make_alphanum_and_lower_for_non_numbers(word: str, with_space=True) -> str:
    # if contains number, most likely a value and not an identifier
    if number_regex.search(word):
        return word
    if with_space:
        return alphanum_regex_with_space.sub('', str(word)).lower().strip()
    else:
        return alphanum_regex_without_space.sub('', str(word)).lower().strip()


def get_diff_for_alphanum_words(word1: str, word2: str) -> float:
    return get_diff_for_words(word1=make_alphanum_and_lower_for_non_numbers(word=word1),
                              word2=make_alphanum_and_lower_for_non_numbers(word=word2))


def get_diff_for_words(word1: str, word2: str) -> float:
    return difflib.SequenceMatcher(isjunk=None, a=word1, b=word2).ratio()


@dataclass(repr=True)
class TWord():
    text: str
    original_text: str
    text_type: str
    confidence: float
    id: str
    xmin: int
    ymin: int
    xmax: int
    ymax: int
    page_number: int
    doc_width: int
    doc_height: int
    child_relationships: Optional[str] = None
    reference: Optional[str] = None
    resolver: Optional[str] = None

    def __init__(
            self,
            text: str = None,
            original_text: str = None,
            text_type: str = None,    # word, line or phrase
            confidence: float = None,
            id: str = None,
            xmin: int = None,
            ymin: int = None,
            xmax: int = None,
            ymax: int = None,
            page_number: int = None,
            ocrdb_row=None,
            trp_word: trpWord = None,
            doc_width: int = None,
            doc_height: int = None,
            child_relationships: str = "",
            reference: str = None,
            resolver: str = None):
        """
        resolver: textract, tquery, table, forms
        """

        len_word_params = len([x for x in [text, ocrdb_row, trp_word] if x])
        if len_word_params > 1:
            raise ValueError("Only can take one, text or trp_word or word_position or ocrdb_row.")
        if len_word_params == 0:
            raise ValueError("Have to pass in one of text or trp_word or word_position.")

        if text:
            missing_values: List[str] = list()
            if not text_type:
                missing_values.append("text_type")
            else:
                self.text_type = text_type.lower()
            if not text:
                missing_values.append("text")
            else:
                self.text = text.lower()
            if not id:
                missing_values.append("id")
            else:
                self.id = id
            if original_text:
                self.original_text = original_text
            if not confidence:
                missing_values.append("confidence")
            else:
                self.confidence: float = confidence
            if xmin == None or ymin == None or xmax == None or ymax == None:
                missing_values.append("xmin ymin xmax or ymax")
            else:
                self.xmin: int = xmin
                self.ymin: int = ymin
                self.xmax: int = xmax
                self.ymax: int = ymax
            if not page_number:
                missing_values.append("page_number")
            else:
                self.page_number: int = page_number
            if resolver:
                self.resolver = resolver
            if not doc_width or not doc_height:
                missing_values.append("doc_width or doc_height")
            else:
                self.doc_width = doc_width
                self.doc_height = doc_height
            self.child_relationships = child_relationships
            if reference:
                self.reference = reference
            if missing_values:
                raise ValueError(f"missing: {missing_values}")

        if ocrdb_row:
            self.page_number = ocrdb_row[1]
            self.text_type = ocrdb_row[2]
            self.text = ocrdb_row[3]
            self.original_text = ocrdb_row[4]
            self.confidence = ocrdb_row[5]
            self.xmin = ocrdb_row[6]
            self.ymin = ocrdb_row[7]
            self.xmax = ocrdb_row[8]
            self.ymax = ocrdb_row[9]
            self.id = ocrdb_row[10]
            self.doc_width = ocrdb_row[11]
            self.doc_height = ocrdb_row[12]
            self.child_relationships = ocrdb_row[13]
            self.reference = ocrdb_row[14]

        if trp_word:
            if not (doc_width and doc_height and page_number):
                raise ValueError(
                    f"when using trp_word, need doc_width and doc_height and page_number parameters as well. \
                    doc_width: {doc_width}, doc_height: {doc_height}, page_number: {page_number}")
            if isinstance(trp_word, FieldKey) or isinstance(trp_word, FieldValue):
                self.text = trp_word.text.lower()
                self.text_type = 'KEY' if isinstance(trp_word, FieldKey) else 'VALUE'
                self.original_text = trp_word.text
                if reference:
                    self.reference = reference
            if isinstance(trp_word, trpWord):
                self.text = trp_word.text.lower()
                self.text_type = 'word'
                self.original_text = trp_word.text
            self.confidence = trp_word.confidence
            bbox_width = trp_word.geometry.boundingBox.width
            bbox_height = trp_word.geometry.boundingBox.height
            bbox_left = trp_word.geometry.boundingBox.left
            bbox_top = trp_word.geometry.boundingBox.top
            self.xmin = round(bbox_left * doc_width)
            self.ymin = round(bbox_top * doc_height)
            self.xmax = round(self.xmin + (bbox_width * doc_width))
            self.ymax = round(self.ymin + (bbox_height * doc_height))
            self.page_number = page_number
            if resolver:
                self.resolver = resolver
            self.id = trp_word.id
            self.doc_width = doc_width
            self.doc_height = doc_height
            if isinstance(trp_word, Line):
                self.child_relationships = ",".join([x.id for x in trp_word.words])
            else:
                self.child_relationships = ""

    # def __repr__(self) -> str:
    #     return f"text: {self.text} original_text: {self.original_text} text_type: {self.text_type} confidence: {self.confidence} id: {self.id} xmin: {self.xmin} ymin: {self.ymin} xmax: {self.xmax} ymax: {self.ymax} page_number: {self.page_number} doc_width: {self.doc_width} doc_height: {self.doc_height} child_relationships: {self.child_relationships} reference: {self.reference} resolver: Optional[str] "

    def __eq__(self, o: object) -> bool:
        return isinstance(o, TWord) and self.id == o.id

    def __ne__(self, o: object) -> bool:
        return not self.__eq__

    def __gt__(self, o) -> bool:
        return isinstance(o, TWord) and self.id > o.id

    def __lt__(self, o) -> bool:
        return isinstance(o, TWord) and self.id < o.id

    @property
    def center(self) -> TPoint:
        return TPoint(x=(self.xmin + self.xmax) / 2, y=(self.ymin + self.ymax) / 2)

    @property
    def height(self) -> float:
        return abs(self.ymax - self.ymin)

    def euclid_distance(self, other_tword) -> float:
        center1 = self.center
        center2 = other_tword.center
        return math.dist((center1.x, center1.y), (center2.x, center2.y))

    @staticmethod
    def combine_multiple_words_to_phrase(tword_list: "list[TWord]") -> "TWord":
        """
        word_array = trp.Word objects

        get xmin, ymin, xmax, ymax for both words and combine them with space 'word1 word2' and insert
        simple calculation of new average confidence (conf1 + conf2) / 2
        returns tuble ('word1 word2', xmin, ymin, xmax, ymax)"""
        if not tword_list:
            raise ValueError(f"tword_list is empty.")
        phrase = " ".join([x.text for x in tword_list])
        original_text = " ".join([x.original_text for x in tword_list if x.original_text])
        text_type = 'phrase'
        xmin = min([x.xmin for x in tword_list])
        xmax = max([x.xmax for x in tword_list])
        ymin = min([x.ymin for x in tword_list])
        ymax = max([x.ymax for x in tword_list])
        page_number = int(tword_list[0].page_number)
        confidence = statistics.mean([x.confidence for x in tword_list])
        doc_width = tword_list[0].doc_width
        doc_height = tword_list[0].doc_height
        return TWord(page_number=page_number,
                     original_text=original_text,
                     text_type=text_type,
                     text=phrase,
                     confidence=confidence,
                     xmin=xmin,
                     ymin=ymin,
                     xmax=xmax,
                     ymax=ymax,
                     id=str(uuid4()),
                     doc_width=doc_width,
                     doc_height=doc_height)

    def __eq__(self, obj):
        return isinstance(obj, TWord) and obj.id == self.id

    @property
    def area(self):
        return abs(self.xmax - self.xmin) * abs(self.ymax - self.ymin)

    def get_tupel(self):
        return (self.text, self.confidence, self.xmin, self.ymin, self.xmax, self.ymax)
