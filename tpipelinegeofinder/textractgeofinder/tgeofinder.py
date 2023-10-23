from typing import List, Iterable, Optional
import difflib
import uuid
import logging
import re
import trp
import trp.trp2 as t2
from warnings import warn

from dataclasses import dataclass
from enum import Enum, auto

from textractgeofinder.tword import TWord, make_alphanum_and_lower_for_non_numbers, get_diff_for_alphanum_words
from textractgeofinder.ocrdb import OCRDB, AreaSelection

logger = logging.getLogger(__name__)


class PointValueType(Enum):
    """XMIN, XMAX, YMIN, YMAX
    """
    XMIN = auto()
    XMAX = auto()
    YMIN = auto()
    YMAX = auto()


@dataclass
class SelectionElement:
    selection: TWord
    key: List[TWord]


@dataclass(repr=True)
class KeyValue:
    key: TWord
    value: Optional[TWord] = None


class NoPhraseForAreaFoundError(Exception):
    pass


@dataclass
class PhraseCoordinate:
    phrase: str
    coordinate: PointValueType
    min_textdistance: float = 0.8


class TGeoFinder():
    supported_suffixes = ['.png', '.jpg', '.jpeg', '.pdf']
    image_suffixes = ['.png', '.jpg', '.jpeg']
    approx_line_difference = 5
    approx_word_distance = 30
    resolver_type = 'tquery'

    def __init__(self, textract_result_json, doc_width, doc_height):
        if not doc_width or not doc_height:
            raise ValueError(f"doc_width and doc_height are required")
        self.textract_doc_uuid = str(uuid.uuid4())
        self.ocrdb = OCRDB.getInstance()
        self.doc_width = doc_width
        self.doc_height = doc_height
        self.doc = trp.Document(textract_result_json)
        self.trp2_doc: t2.TDocument = t2.TDocumentSchema().load(textract_result_json)
        self.__fill_sql_from_textract_json()

    def __del__(self):
        if self.ocrdb:
            deleted_words = self.ocrdb.delete(self.textract_doc_uuid)
            logger.debug(f"deleted words: {deleted_words}")
        else:
            logger.error(f"no ocrdb")

    def get_TWord_from_TBlock(self, block: t2.TBlock) -> TWord:
        bbox_width = block.geometry.bounding_box.width
        bbox_height = block.geometry.bounding_box.height
        bbox_left = block.geometry.bounding_box.left
        bbox_top = block.geometry.bounding_box.top
        x_min = round(bbox_left * self.doc_width)
        y_min = round(bbox_top * self.doc_height)
        x_max = round(x_min + (bbox_width * self.doc_width))
        y_max = round(y_min + (bbox_height * self.doc_height))
        page_number = block.page if block.page else 1
        if block.text:
            text = make_alphanum_and_lower_for_non_numbers(block.text)
            original_text = block.text
        elif block.selection_status:
            text = block.selection_status
            original_text = block.selection_status
        else:
            text = ""
            original_text = ""

        return TWord(text=text,
                     original_text=original_text,
                     confidence=block.confidence,
                     id=block.id,
                     text_type=block.block_type,
                     ymin=y_min,
                     xmin=x_min,
                     ymax=y_max,
                     xmax=x_max,
                     page_number=page_number,
                     doc_width=self.doc_width,
                     doc_height=self.doc_height)

    def get_coords_from_geo(self, word):
        """
        return tuple(x_min, y_min, x_max, y_max)
        """
        bbox_width = word.geometry.boundingBox.width
        bbox_height = word.geometry.boundingBox.height
        bbox_left = word.geometry.boundingBox.left
        bbox_top = word.geometry.boundingBox.top
        x_min = round(bbox_left * self.doc_width)
        y_min = round(bbox_top * self.doc_height)
        x_max = round(x_min + (bbox_width * self.doc_width))
        y_max = round(y_min + (bbox_height * self.doc_height))
        return (x_min, y_min, x_max, y_max)

    def __fill_sql_from_textract_json(self):
        logger.debug("__fill_sql_from_textract_json")
        word_list: "list[TWord]" = list()
        line_list: "list[TWord]" = list()
        forms_list: List[TWord] = list()
        selection_elements: List[TWord] = list()

        for idx, page in enumerate(self.doc.pages):
            logger.debug(f"page: {idx}")
            if idx >= 1:
                selection_elements_tblocks = self.trp2_doc.get_blocks_by_type(
                    block_type_enum=t2.TextractBlockTypes.SELECTION_ELEMENT, page=self.trp2_doc.pages[idx])
                logger.debug(f"selection_elements_tblocks: {selection_elements_tblocks}")
                selection_elements = [self.get_TWord_from_TBlock(b) for b in selection_elements_tblocks]
                logger.debug(f"selection_elements: {[s.text for s in selection_elements]}")
            else:
                selection_elements = [
                    self.get_TWord_from_TBlock(b)
                    for b in self.trp2_doc.get_blocks_by_type(block_type_enum=t2.TextractBlockTypes.SELECTION_ELEMENT,
                                                              page=self.trp2_doc.pages[idx])
                ]
                logger.debug(f"selection_elements: {[s.text for s in selection_elements]}")

            for field in page.form.fields:
                reference = ""
                if field.key:
                    logger.debug(f"field-key: {field.key}")
                    if field.value:
                        forms_list.append(
                            TWord(trp_word=field.value,
                                  reference=field.key.id,
                                  doc_width=self.doc_width,
                                  doc_height=self.doc_height,
                                  page_number=idx + 1))
                        reference = field.value.id
                    else:
                        logger.warning(f"field.value is None: {field.value}")

                    forms_list.append(
                        TWord(trp_word=field.key,
                              reference=reference,
                              doc_width=self.doc_width,
                              doc_height=self.doc_height,
                              page_number=idx + 1))
                else:
                    logger.warning(f"field.key is None: {field.key}")

            for line in page.lines:
                line_text = make_alphanum_and_lower_for_non_numbers(line.text)
                xmin, ymin, xmax, ymax = self.get_coords_from_geo(line)
                if line_text:
                    line_text = line_list.append(
                        TWord(text=line_text,
                              text_type='line',
                              original_text=line.text,
                              page_number=idx + 1,
                              confidence=line.confidence,
                              xmin=xmin,
                              ymin=ymin,
                              xmax=xmax,
                              ymax=ymax,
                              id=line.id,
                              doc_width=self.doc_width,
                              doc_height=self.doc_height,
                              child_relationships=",".join([x.id for x in line.words])))

                for word in line.words:
                    # old_text = word.text
                    text = make_alphanum_and_lower_for_non_numbers(word.text)
                    if text:
                        xmin, ymin, xmax, ymax = self.get_coords_from_geo(word)
                        word_list.append(
                            TWord(text=text,
                                  original_text=word.text,
                                  text_type='word',
                                  page_number=idx + 1,
                                  confidence=word.confidence,
                                  xmin=xmin,
                                  ymin=ymin,
                                  xmax=xmax,
                                  ymax=ymax,
                                  id=word.id,
                                  doc_width=self.doc_width,
                                  doc_height=self.doc_height))
                    else:    # if no text left, store only original
                        xmin, ymin, xmax, ymax = self.get_coords_from_geo(word)
                        word_list.append(
                            TWord(text=word.text,
                                  original_text=word.text,
                                  text_type='word',
                                  page_number=idx + 1,
                                  confidence=word.confidence,
                                  xmin=xmin,
                                  ymin=ymin,
                                  xmax=xmax,
                                  ymax=ymax,
                                  id=word.id,
                                  doc_width=self.doc_width,
                                  doc_height=self.doc_height))

        if self.ocrdb:
            self.ocrdb.insert_bulk(textract_doc_uuid=self.textract_doc_uuid, rows=word_list)
            self.ocrdb.insert_bulk(textract_doc_uuid=self.textract_doc_uuid, rows=line_list)
            self.ocrdb.insert_bulk(textract_doc_uuid=self.textract_doc_uuid, rows=selection_elements)
            self.ocrdb.insert_bulk(textract_doc_uuid=self.textract_doc_uuid, rows=forms_list)
        else:
            logger.error(f"no ocrdb")

    def get_keys_for_key_variations(self, key_variations: List[str], min_textdistance=0.8) -> List[t2.TBlock]:
        """does return for all pages values found for the key given"""
        logger.debug(f"key_variations: {key_variations}")
        key_list: List[t2.TBlock] = list()
        for key_variation in key_variations:
            for page in self.trp2_doc.pages:
                for doc_key in self.trp2_doc.keys(page=page):
                    key_in_doc = make_alphanum_and_lower_for_non_numbers(
                        t2.TDocument.get_text_for_tblocks(
                            self.trp2_doc.get_blocks_for_relationships(doc_key.get_relationships_for_type())))
                    key_in_list = make_alphanum_and_lower_for_non_numbers(key_variation)
                    if difflib.SequenceMatcher(isjunk=None, a=key_in_doc, b=key_in_list).ratio() > min_textdistance:
                        key_list.append(doc_key)
        return key_list

    def find_word(self, text: str) -> List[TWord]:
        return self.ocrdb.select_text(textract_doc_uuid=self.textract_doc_uuid, text=text.lower())

    def get_words_below(self,
                        anker: AreaSelection,
                        number_of_words_to_return: int = None,
                        text_type: str = 'word',
                        area_selection: AreaSelection = None,
                        page_number: int = 1,
                        exclude_ids: List[str] = None) -> List[TWord]:
        xmin = anker.top_left.x
        xmax = anker.lower_right.x
        ymax = anker.lower_right.y

        query = ''' and ? < (xmin + xmax) / 2
                    and ? > ( xmin + xmax ) / 2
                    and ? < ymin
                    and text_type = ?
                    order by ymin  asc '''
        params = [xmin, xmax, ymax, text_type]
        if number_of_words_to_return:
            query += " limit ? "
            params.append(number_of_words_to_return)

        return self.ocrdb.execute(query=query,
                                  textract_doc_uuid=self.textract_doc_uuid,
                                  params=params,
                                  area_selection=area_selection,
                                  page_number=page_number,
                                  exclude_ids=exclude_ids)
        
    def get_words_above(self,
                        anker: AreaSelection,
                        number_of_words_to_return: int = None,
                        text_type: str = 'word',
                        area_selection: AreaSelection = None,
                        page_number: int = 1,
                        exclude_ids: List[str] = None) -> List[TWord]:
        xmin = anker.top_left.x
        ymin = anker.top_left.y
        xmax = anker.lower_right.x
        ymax = anker.lower_right.y
        
        query = ''' and ? < (xmin + xmax) / 2
                    and ? > ( xmin + xmax ) / 2
                    and ? > ymax
                    and text_type = ?
                    order by ymin  asc '''
        params = [xmin, xmax, ymin, text_type]
        if number_of_words_to_return:
            query += " limit ? "
            params.append(number_of_words_to_return)

        return self.ocrdb.execute(query=query,
                                  textract_doc_uuid=self.textract_doc_uuid,
                                  params=params,
                                  area_selection=area_selection,
                                  page_number=page_number,
                                  exclude_ids=exclude_ids)         

    def get_words_to_the_right(self,
                               anker: AreaSelection,
                               number_of_words_to_return: int = None,
                               text_type: str = 'word',
                               area_selection: AreaSelection = None,
                               page_number: int = 1,
                               exclude_ids: List[str] = None) -> List[TWord]:
        ymin_pos = anker.top_left.y - TGeoFinder.approx_line_difference
        ymin_pos = ymin_pos if ymin_pos >= 0 else 0
        ymax_pos = anker.lower_right.y + TGeoFinder.approx_line_difference

        query = '''and ? < ( ymin + ymax ) / 2
                and ? > ( ymin + ymax ) / 2
                and ? < xmin
                and text_type = ?
                order by (xmin - ?) asc '''
        params = [ymin_pos, ymax_pos, anker.lower_right.x, text_type, anker.lower_right.x]
        if number_of_words_to_return:
            query += " limit ? "
            params.append(number_of_words_to_return)

        return self.ocrdb.execute(query=query,
                                  textract_doc_uuid=self.textract_doc_uuid,
                                  params=params,
                                  area_selection=area_selection,
                                  page_number=page_number,
                                  exclude_ids=exclude_ids)

    def find_intersect_for_area(self, area1: AreaSelection, area2: AreaSelection) -> List[TWord]:
        if area1.page_number != area2.page_number:
            raise ValueError(f"page numbers don't match for areas. area1: {area1}, area2: {area2}")
        xmax = min(area1.lower_right.x, area2.lower_right.x)
        xmin = max(area1.top_left.x, area2.top_left.x)
        ymax = min(area1.lower_right.y, area2.lower_right.y)
        ymin = max(area1.top_left.y, area2.top_left.y)
        return self.get_twords_in_area(area_selection=AreaSelection(
            top_left=t2.TPoint(x=xmin, y=ymin), lower_right=t2.TPoint(x=xmax, y=ymax), page_number=area1.page_number))

    def find_intersect_value(self,
                             word_left: str,
                             word_up: str,
                             word_up_minus_x: int = 0,
                             word_up_plus_x: int = 0,
                             text_type: str = 'word',
                             stop_words: "list[str]" = None,
                             area_selection: AreaSelection = None,
                             page_number: int = 1,
                             min_textdistance: float = 0.8,
                             number_of_other_words_allowed: int = 0,
                             exclude_ids: List[str] = None) -> "list[TWord]":
        """
        find intersect value by looking for the left word/phrase and the upper word/phrase and finding values where the center is in that block
        """
        logger.debug(f"word_left: {word_left}, word_up: {word_up}")
        result_tword_list: "list[TWord]" = list()
        word_left = word_left.lower()
        word_up = word_up.lower()
        word_left_list = self.find_phrase_on_page(word_left, min_textdistance, page_number,
                                                  number_of_other_words_allowed, area_selection, exclude_ids)
        word_up_list = self.find_phrase_on_page(word_up, min_textdistance, page_number, number_of_other_words_allowed,
                                                area_selection, exclude_ids)
        logger.debug(f"word_left_list: {word_left_list} \n word_up_list: {word_up_list}")
        # TODO: one query instead of loop would be better
        for tword_left in word_left_list:
            # get ordered list of word_up that are higher and to the right of word_left
            query = ''' and text=?
                        and ymin < ?
                        and xmin > ?
                        and page_number = ?
                        order by ( ((? - xmin) * (? - xmin)) + ((? - ymin) * (? - ymin))) asc
                               '''
            params = [
                word_up, tword_left.ymin, tword_left.xmin, tword_left.page_number, tword_left.xmin, tword_left.xmin,
                tword_left.ymin, tword_left.ymin
            ]

            j = self.ocrdb.execute(query=query,
                                   params=params,
                                   area_selection=area_selection,
                                   textract_doc_uuid=self.textract_doc_uuid,
                                   page_number=page_number,
                                   exclude_ids=exclude_ids)
            if j and len(j) >= 1:
                logger.debug(f"found a word_up: {j}")
                query = ''' and ((xmin + xmax) / 2) < ?
                            and ((xmin + xmax) / 2) > ?
                            and ((ymin + ymax) / 2) > ?
                            and ((ymin + ymax) / 2) < ?
                            and text_type=?
                            and page_number = ?
                '''
                params = [
                    j[0].xmax + word_up_plus_x, j[0].xmin - word_up_minus_x, tword_left.ymin, tword_left.ymax,
                    text_type, tword_left.page_number
                ]
                found_intersect_word = self.ocrdb.execute(query=query,
                                                          params=params,
                                                          textract_doc_uuid=self.textract_doc_uuid,
                                                          area_selection=area_selection,
                                                          page_number=page_number,
                                                          exclude_ids=exclude_ids)
                result_tword_list.extend(found_intersect_word)
        if result_tword_list:
            logger.info(f"word_left: {word_left}, word_up: {word_up}, result_tuples: {[p for p in result_tword_list]}")
        return result_tword_list

    # get all lines to the right above another phrase
    def get_lines_to_right_and_above(self,
                                     current_word: TWord,
                                     below_word: TWord,
                                     area_selection: AreaSelection = None,
                                     page_number: int = 1,
                                     exclude_ids: List[str] = None):
        ymin_pos = current_word.ymin - TGeoFinder.approx_line_difference
        ymin_pos = ymin_pos if ymin_pos >= 0 else 0
        below_word_ymin_pos = below_word.ymin - TGeoFinder.approx_line_difference
        below_word_ymin_pos = below_word_ymin_pos if below_word_ymin_pos >= 0 else 0

        query = ''' and text_type='line'
                and ((ymin + ymax) / 2) between ? and ?
                and ? < xmin
                order by ymin asc '''
        params = [ymin_pos, below_word_ymin_pos, current_word.xmax]

        return self.ocrdb.execute(query=query,
                                  params=params,
                                  textract_doc_uuid=self.textract_doc_uuid,
                                  area_selection=area_selection,
                                  page_number=page_number,
                                  exclude_ids=exclude_ids)

    def get_lines_in_area(self,
                          area_selection: AreaSelection,
                          page_number: int = 1,
                          exclude_ids: List[str] = None) -> List[TWord]:
        query = " and text_type=? order by ymin asc"
        params = ['line']
        return self.ocrdb.execute(query=query,
                                  params=params,
                                  page_number=page_number,
                                  exclude_ids=exclude_ids,
                                  textract_doc_uuid=self.textract_doc_uuid,
                                  area_selection=area_selection)

    def get_lines_between_phrases(self,
                                  current_word: TWord,
                                  below_word: TWord,
                                  current_word_x_offset: int = 0,
                                  below_word_x_offset: int = 0,
                                  area_selection: AreaSelection = None,
                                  page_number: int = 1,
                                  exclude_ids: List[str] = None):
        ymin_pos = current_word.ymin - TGeoFinder.approx_line_difference
        ymin_pos = ymin_pos if ymin_pos >= 0 else 0
        ymax_pos = current_word.ymax
        below_word_ymin_pos = below_word.ymin - TGeoFinder.approx_line_difference
        below_word_ymin_pos = below_word_ymin_pos if below_word_ymin_pos >= 0 else 0

        query = ''' and text_type='line'
                    and ((ymin + ymax) / 2) between ? and ?
                    and ((xmin + xmax) / 2) between ? and ?
                    order by ymin asc '''

        params = [
            ymax_pos, below_word_ymin_pos,
            min(current_word.xmin, below_word.xmin),
            max(current_word.xmax, below_word.xmax)
        ]

        return self.ocrdb.execute(query=query,
                                  params=params,
                                  textract_doc_uuid=self.textract_doc_uuid,
                                  area_selection=area_selection,
                                  page_number=page_number,
                                  exclude_ids=exclude_ids)

    def get_words_in_area(self,
                          area_selection: AreaSelection = None,
                          page_number: int = 1,
                          exclude_ids: List[str] = None):
        query = " and text_type=? order by xmin asc "
        params = ['word']
        r = self.ocrdb.execute(query=query,
                               params=params,
                               textract_doc_uuid=self.textract_doc_uuid,
                               page_number=page_number,
                               area_selection=area_selection,
                               exclude_ids=exclude_ids)
        logger.debug(f"result: {r}")
        return r

    def get_words_between_words(self,
                                left_word: TWord,
                                right_word: TWord,
                                text_type: List[str] = ['word'],
                                area_selection: AreaSelection = None,
                                page_number: int = 1,
                                exclude_ids: List[str] = None):
        logger.debug(
            f"get_words_between_words - left_word: {left_word}, right_word: {right_word}, text_type: {text_type}")
        ymin_pos = min([left_word.ymin, right_word.ymin]) - TGeoFinder.approx_line_difference
        ymin_pos = ymin_pos if ymin_pos >= 0 else 0
        ymax_pos = max([left_word.ymax, right_word.ymax]) + TGeoFinder.approx_line_difference
        xmin_pos = left_word.xmax
        xmax_pos = right_word.xmin

        query = f" and text_type in ({','.join(['?']*len(text_type))}) \
                                    and (ymin + ymax) / 2 > ? \
                                    and (ymin + ymax) / 2 < ? \
                                    and xmin > ? \
                                    and xmax < ? \
                                    and page_number = ? \
                                    order by xmin asc"

        params = list()
        params.extend(text_type)
        params.extend([ymin_pos, ymax_pos, xmin_pos, xmax_pos, left_word.page_number])
        r = self.ocrdb.execute(query=query,
                               params=params,
                               textract_doc_uuid=self.textract_doc_uuid,
                               area_selection=area_selection,
                               page_number=page_number,
                               exclude_ids=exclude_ids)

        logger.debug(f"result: {r}")
        return r

    def get_values_for_phrase_coordinate(self, phrase_coordinates: List[PhraseCoordinate]) -> List[float]:
        """This method makes it easier to develop resilient templates but allowing to get area-coordinate from different phrases and pick one that workds.
        It only returns the list of first ones found, not all.
        finding phrases is an expensive operation (maybe make it lazy...)
        """
        return_value: List[float] = list()
        for phrase_coordinate in phrase_coordinates:
            phrases_found: List[TWord] = self.find_phrase_on_page(phrase=phrase_coordinate.phrase,
                                                                  min_textdistance=phrase_coordinate.min_textdistance)
            if phrases_found:
                logger.debug(f"get_values_for_phrase_coordinate: found value for phrase: {phrases_found}")
                for tword_phrase in phrases_found:
                    if phrase_coordinate.coordinate == PointValueType.XMAX:
                        r_value_add = tword_phrase.xmax
                    elif phrase_coordinate.coordinate == PointValueType.YMAX:
                        r_value_add = tword_phrase.ymax
                    elif phrase_coordinate.coordinate == PointValueType.XMIN:
                        r_value_add = tword_phrase.xmin
                    elif phrase_coordinate.coordinate == PointValueType.YMIN:
                        r_value_add = tword_phrase.ymin
                    else:
                        r_value_add = None
                        logger.warn(f"no coordinate for phrase_coordinate: {phrase_coordinate}")
                    if r_value_add:
                        return_value.append(r_value_add)
            if return_value:
                if len(return_value) > 1:
                    logger.warning(
                        f"non unique - (len={len(return_value)}) for phrase_coordinate.phrase: {phrase_coordinate.phrase}, phrases_found:{phrases_found}"
                    )
                logger.debug(f"get_values_for_phrase_coordinate - {return_value}")
                return return_value

        if not return_value:
            raise NoPhraseForAreaFoundError(f"nothin found for phrase_coordinates: {phrase_coordinates}")
        return return_value

    def get_next_selection_element_to_the_right(self,
                                                word: TWord,
                                                xmax: int,
                                                area_selection: AreaSelection = None,
                                                page_number: int = 1,
                                                exclude_ids: List[str] = None):
        ymin_pos = word.ymin - TGeoFinder.approx_line_difference
        ymin_pos = ymin_pos if ymin_pos >= 0 else 0
        ymax_pos = word.ymax + TGeoFinder.approx_line_difference
        xmin_pos = word.xmax
        query = ''' and text_type='selection_element'
                    and (ymin + ymax) / 2 > ?
                    and (ymin + ymax) / 2 < ?
                    and xmin > ?
                    and xmax < ?
                    order by xmin asc limit 1'''
        params = [ymin_pos, ymax_pos, xmin_pos, xmax]
        return self.ocrdb.execute(query=query,
                                  params=params,
                                  textract_doc_uuid=self.textract_doc_uuid,
                                  area_selection=area_selection,
                                  page_number=page_number,
                                  exclude_ids=exclude_ids)

    def get_form_fields_in_area(self, area_selection: AreaSelection, exclude_ids: List[str] = None) -> List[KeyValue]:
        if not area_selection:
            raise ValueError("need and area_selection")
        keys: List[TWord] = self.get_area(area_selection=area_selection, exclude_ids=exclude_ids, text_type=["KEY"])
        result_set: List[KeyValue] = list()
        logger.debug(f"get_form_fields_in_area: found keys: {keys}")
        for k in keys:
            logger.debug(f"get_form_fields_in_area: key: {k}")
            value = None
            if k.reference:
                value = self.ocrdb.get_id(id=k.reference, textract_doc_uuid=self.textract_doc_uuid)
                logger.debug(f"get_form_fields_in_area: value: {value}")
            result_set.append(KeyValue(key=k, value=value))
        return result_set

    # FIXME: add block_type to ocrdb  for easier check if selection element
    # "BlockType": "SELECTION_ELEMENT"
    def get_selection_values_in_area(self,
                                     area_selection: AreaSelection,
                                     exclude_ids: List[str] = None) -> List[SelectionElement]:
        if not area_selection:
            raise ValueError("need and area_selection")
        keys: List[TWord] = self.get_area(area_selection=area_selection, exclude_ids=exclude_ids, text_type=["KEY"])
        result_set: List[SelectionElement] = list()
        logger.debug(f"get_form_fields_in_area: found keys: {keys}")
        for k in keys:
            logger.debug(f"get_form_fields_in_area: key: {k}")
            value = None
            if k.reference:
                value = self.ocrdb.get_id(id=k.reference, textract_doc_uuid=self.textract_doc_uuid)
                logger.debug(f"get_form_fields_in_area: value: {value}")
                if value and ((value.original_text and value.original_text == "NOT_SELECTED") or
                              (value.original_text and value.original_text == "SELECTED")):
                    result_set.append(SelectionElement(key=[k], selection=value))
        return result_set

    @staticmethod
    def get_area_selection_for_twords(twords: Iterable[TWord]) -> AreaSelection:
        xmin = min([tw.xmin for tw in twords])
        xmax = max([tw.xmax for tw in twords])
        ymin = min([tw.ymin for tw in twords])
        ymax = max([tw.ymax for tw in twords])
        pages = {x.page_number for x in twords}
        if len(pages) > 1:
            raise ValueError(f"all twords should be on same page: {twords}")
        if len(pages) < 1:
            raise ValueError("twords without x/y coordinates")
        page = pages.pop()
        return AreaSelection(top_left=t2.TPoint(x=xmin, y=ymin),
                             lower_right=t2.TPoint(x=xmax, y=ymax),
                             page_number=page)

    def get_area(self,
                 area_selection: AreaSelection,
                 exclude_ids: List[str] = None,
                 text_type: List[str] = ['word', 'selection_element']) -> List[TWord]:
        words: List[TWord] = self.ocrdb.execute(
            query=f" and text_type in ({','.join(['?']*len(text_type))}) order by xmin asc",
            params=text_type,
            textract_doc_uuid=self.textract_doc_uuid,
            page_number=area_selection.page_number,
            area_selection=area_selection,
            exclude_ids=exclude_ids)
        logger.debug(f"get_area: number of words: {len(words)}")
        return words

    def get_twords_in_area(self,
                           area_selection: AreaSelection,
                           text_type: List[str] = ["word"],
                           exclude_ids: List[str] = None) -> List[TWord]:
        query = ""
        params = []
        if text_type:
            query += " and text_type = ?"
            params.extend(text_type)
        query += " order by xmin asc"
        return self.ocrdb.execute(query=query,
                                  params=params,
                                  textract_doc_uuid=self.textract_doc_uuid,
                                  area_selection=area_selection,
                                  page_number=area_selection.page_number,
                                  exclude_ids=exclude_ids)

    def get_selection_boxes_to_left(self,
                                    word: TWord,
                                    number_of_boxes_to_return: int = None,
                                    area_selection: AreaSelection = None,
                                    page_number: int = 1,
                                    exclude_ids: List[str] = None):
        ymin_pos = word.ymin - TGeoFinder.approx_line_difference
        ymin_pos = ymin_pos if ymin_pos >= 0 else 0
        ymax_pos = word.ymax + TGeoFinder.approx_line_difference
        xmin_pos = word.xmax
        xmax_pos = word.xmin

        query = ''' and text_type='selection_element'
                    and (ymin + ymax) / 2 > ?
                    and (ymin + ymax) / 2 < ?
                    and xmax < ?
                    order by xmin asc '''
        params = [ymin_pos, ymax_pos, xmin_pos, xmax_pos]
        if number_of_boxes_to_return:
            query += "limit ?"
            params.append(number_of_boxes_to_return)

        return self.ocrdb.execute(query=query,
                                  params=params,
                                  textract_doc_uuid=self.textract_doc_uuid,
                                  area_selection=area_selection,
                                  page_number=page_number,
                                  exclude_ids=exclude_ids)

    @staticmethod
    def get_min_distance(word1: TWord, word2: TWord) -> float:
        """word1 should be above or to the left of word2
        """
        return min([abs(word1.xmax - word2.xmin), abs(word1.ymax - word2.ymin)])

    @staticmethod
    def get_min_distance_for_list_of_tword(twords: List[TWord]) -> float:
        min_distances = list()
        for idx, word_start in enumerate(twords[:-1]):
            min_distances.append(TGeoFinder.get_min_distance(word_start, twords[idx + 1]))
        return max(min_distances)

    # @staticmethod
    # def get_anker_for_twords(words: List[TWord]) -> AreaSelection:
    #     xmin = min([x.xmin for x in words])
    #     xmax = max([x.xmax for x in words])
    #     ymin = min([x.ymin for x in words])
    #     ymax = max([x.ymax for x in words])
    #     return AreaSelection(top_left=t2.TPoint(x=xmin, y=ymin), lower_right=t2.TPoint(x=xmax, y=ymax))

    def find_word_on_page(self,
                          word_to_find: str,
                          page_number: int = 1,
                          min_textdistance=0.8,
                          area_selection: AreaSelection = None,
                          exclude_ids: List[str] = None) -> List[TWord]:
        query = " and text_type=? and page_number=? "
        params = ["word", page_number]
        words = self.ocrdb.execute(textract_doc_uuid=self.textract_doc_uuid,
                                   page_number=page_number,
                                   area_selection=area_selection,
                                   params=params,
                                   query=query,
                                   exclude_ids=exclude_ids)
        alphanum_word_to_find = make_alphanum_and_lower_for_non_numbers(word_to_find)
        result_list: List[TWord] = list()
        if not alphanum_word_to_find:
            logger.warn(f"did not find anything for: {word_to_find}")
            return list()
        for word in words:
            if difflib.SequenceMatcher(isjunk=None, a=alphanum_word_to_find, b=word.text).ratio() > min_textdistance:
                result_list.append(word)

        return result_list

    @staticmethod
    def get_sum_of_area_for_twords(twords: List[TWord]) -> float:
        return sum([tw.area for tw in twords])

    def __find_phrase_on_page(self,
                              phrase_words: List[str],
                              min_textdistance: float = 0.9,
                              page_number: int = 1,
                              number_of_other_words_allowed: int = 0,
                              area_selection: AreaSelection = None,
                              exclude_ids: List[str] = None) -> List[TWord]:
        logger.debug(
            f"find_phrase_on_page: phrase_words: {phrase_words}, min_textdistance: {min_textdistance}, area_selection: {area_selection}"
        )
        found_phrases: List[TWord] = list()
        valid_combinations: List[List[TWord]] = list()
        # find first words and then walk to right and down and lower_left_word is always the left-most and lowest
        lower_left_word = phrase_words[0]
        first_word_twords: List[TWord] = self.find_word_on_page(lower_left_word,
                                                                page_number=page_number,
                                                                min_textdistance=min_textdistance,
                                                                exclude_ids=exclude_ids)
        logger.debug(f"find_phrase_on_page - first_word_twords: {first_word_twords}")

        for first_word_option in first_word_twords:
            logger.debug(f"find_phrase_on_page - trying to find phrase starting with: {first_word_option}")
            lower_left_word = first_word_option
            valid_combination: List[TWord] = list()
            valid_combination.append(first_word_option)
            below_area: AreaSelection = AreaSelection(
                top_left=t2.TPoint(x=lower_left_word.xmin, y=lower_left_word.ymax),
                lower_right=t2.TPoint(x=lower_left_word.xmax + lower_left_word.height * 3, y=self.doc_width),
                page_number=page_number)

            found_combination = True
            current_word = first_word_option
            for word in phrase_words[1:]:
                logger.debug(f"find_phrase_on_page - looking for word: {word} with current_word: {current_word}")
                words_to_right = self.get_words_to_the_right(anker=TGeoFinder.get_area_selection_for_twords(
                    [current_word]),
                                                             number_of_words_to_return=1,
                                                             page_number=page_number)
                logger.debug(f"find_phrase_on_page - words to the right: {words_to_right}")
                if words_to_right and get_diff_for_alphanum_words(word1=words_to_right[0].text,
                                                                  word2=word) > min_textdistance:
                    logger.debug(f"find_phrase_on_page - found word_to_right: {words_to_right[0]}")
                    current_word = words_to_right[0]
                    valid_combination.append(words_to_right[0])
                    #found one, next word to check
                    continue

                # find below, take area from ymax of first word and get first words in there ordered by y
                logger.debug(
                    f"find_phrase_on_page - trying to find below word: {word} from lower_left: {lower_left_word}")
                words_below = self.get_twords_in_area(area_selection=below_area)
                logger.debug(f"find_phrase_on_page - found words_below: {words_below}")
                euclidean_distance_list = [x.euclid_distance(first_word_option) for x in words_below]
                combined_list = [x for x in zip(euclidean_distance_list, words_below)]
                if len(combined_list):
                    sorted_below_words = sorted(combined_list)
                    word_below_sorted = [x for (_, x) in sorted_below_words]
                    if word_below_sorted and get_diff_for_alphanum_words(word1=word_below_sorted[0].text,
                                                                         word2=word) > min_textdistance:
                        logger.debug(f"find_phrase_on_page - found word_below: {word_below_sorted[0]}")
                        valid_combination.append(word_below_sorted[0])
                        lower_left_word = word_below_sorted[0]
                        current_word = word_below_sorted[0]
                        continue
                logger.debug(f"find_phrase_on_page - did not find word right or below for {word}")
                found_combination = False
                break
            if found_combination:
                logger.debug(f"find_phrase_on_page - found valid combination: {valid_combination}")
                valid_combinations.append(valid_combination)

        for found_combination in valid_combinations:
            found_phrase: TWord = TWord.combine_multiple_words_to_phrase(list(found_combination))
            found_phrases.append(found_phrase)

        # store for future requests
        logger.debug(f"find_phrase_on_page: result: {found_phrases}")
        if found_phrases:
            self.ocrdb.insert_bulk(textract_doc_uuid=self.textract_doc_uuid, rows=found_phrases)
        return found_phrases

    @staticmethod
    def clean_up_phrase_words(phrase_words: List[str]) -> List[str]:
        new_list: List[str] = list()
        for word in phrase_words:
            new_word = make_alphanum_and_lower_for_non_numbers(word)
            if new_word:
                new_list.append(new_word)
        return new_list

    def find_phrase_on_page(self,
                            phrase: str,
                            min_textdistance: float = 0.8,
                            page_number: int = 1,
                            number_of_other_words_allowed: int = 0,
                            area_selection: AreaSelection = None,
                            exclude_ids: List[str] = None) -> List[TWord]:
        """returns new phrases, regardless of orientation"""
        """TODO: cannot do the caching this way with area_selection, because when using with area_selection first, it will create a phrase for the area and it will just return the value and not consider the other areas """
        phrase_words = phrase.split(" ")
        phrase_words = TGeoFinder.clean_up_phrase_words(phrase_words=phrase_words)
        logger.debug(f"find_phrase_on_page: phrase_words: {phrase_words}")
        if len(phrase_words) < 1:
            raise ValueError(f"no valid phrase: '{phrase}")
        # check if already in DB
        found_phrases: "list[TWord]" = self.ocrdb.select_text(textract_doc_uuid=self.textract_doc_uuid,
                                                              page_number=page_number,
                                                              text=make_alphanum_and_lower_for_non_numbers(phrase),
                                                              area_selection=area_selection,
                                                              exclude_ids=exclude_ids)
        if found_phrases:
            logger.debug(f"phrase already there, pull from DB: {found_phrases}")
            return found_phrases
        else:
            # first try to find with split
            found_phrases = self.__find_phrase_on_page(phrase_words=phrase_words,
                                                       min_textdistance=min_textdistance,
                                                       page_number=page_number,
                                                       number_of_other_words_allowed=number_of_other_words_allowed,
                                                       area_selection=area_selection,
                                                       exclude_ids=exclude_ids)
            if found_phrases:
                return found_phrases
            # now we try phrase combinations
            else:
                phrase_combinations = TGeoFinder.get_phrase_combinations(phrase_words)
                logger.debug(f"find_phrase_on_page: phrase_combinations: {phrase_combinations}")
                for phrase_combination in phrase_combinations:
                    found_phrases = self.__find_phrase_on_page(
                        phrase_words=phrase_combination,
                        min_textdistance=min_textdistance,
                        page_number=page_number,
                        number_of_other_words_allowed=number_of_other_words_allowed,
                        area_selection=area_selection,
                        exclude_ids=exclude_ids)
                    if found_phrases:
                        logger.debug(f"find_phrase_on_page: found_phrases: {found_phrases}")
                        return found_phrases
        # if really nothing found, then empty
        logger.debug(
            f"find_phrase_on_page: found nothing for {phrase} in area: {area_selection} with min_distance:{min_textdistance} on page: {page_number}"
        )
        return found_phrases

    @staticmethod
    def get_phrase_combinations(phrase: List[str]) -> List[List[str]]:
        """Sometimes the spacing and resolution of a document does lead to words being combined. This method creates a list of words that are combined, only do one permutation for each subsequent word, not combinations of multiple missing spaces (full permutations)
        e. g. ["test", "1", "2", "3"] -> [["test1", "2", "3"], ["test", "12", "3"], ["test", "1", "23"]] 
        """
        result_list: List[List[str]] = list()
        for idx, p in enumerate(phrase[:-1]):
            if idx >= 1:
                new_entry_list = phrase[:idx]
            else:
                new_entry_list = list()
            new_entry_list.append(f"{p}{phrase[idx + 1]}")
            if idx < len(phrase) - 2:
                new_entry_list.extend(phrase[idx + 2:])
            result_list.append(new_entry_list)
        logger.debug(f"get_phrase_combinations: {result_list}")
        return result_list

    def find_phrase_in_lines(self, phrase: str, min_textdistance=0.6, page_number: int = 1) -> List[TWord]:
        """
        phrase = words separated by space char
        """
        warn(
            'This function is deprecated and will be removed in later releases start using find_phrase_on_page. Processing of multi-page documents will result in wrong WORD list.',
            DeprecationWarning,
            stacklevel=2)
        # first check if we already did find this phrase and stored it in the DB
        # TODO: Problem: it will not find Current: when the phrase has current and there are other current values in the document without :
        if not phrase:
            raise ValueError(f"no valid phrase: '{phrase}")
        phrase_words = phrase.split(" ")
        if len(phrase_words) < 1:
            raise ValueError(f"no valid phrase: '{phrase}")
        # TODO: check for page_number impl
        found_phrases: "list[TWord]" = self.ocrdb.select_text(textract_doc_uuid=self.textract_doc_uuid,
                                                              text=make_alphanum_and_lower_for_non_numbers(phrase))
        if found_phrases:
            return found_phrases

        alphanum_regex = re.compile(r'[\W_]+')
        # find phrase (words that follow each other) in trp lines
        for page in self.doc.pages:
            page_number = 1
            for line in page.lines:
                for line_idx, word in enumerate(line.words):
                    found_words: "list[TWord]" = []
                    match_phrase = False
                    if difflib.SequenceMatcher(isjunk=None,
                                               a=alphanum_regex.sub('', str(phrase_words[0].lower())),
                                               b=alphanum_regex.sub('', str(
                                                   word.text.lower()))).ratio() > min_textdistance:
                        # assume the phrase to be correct
                        tword = TWord(trp_word=word,
                                      text_type='word',
                                      doc_width=self.doc_width,
                                      doc_height=self.doc_height,
                                      page_number=page_number)
                        tword.text = phrase_words[0].lower()
                        found_words.append(tword)
                        for phrase_idx, phrase_word in enumerate(phrase_words[1:]):
                            if len(line.words) <= line_idx + 1 + phrase_idx:
                                match_phrase = False
                                break
                            next_word = line.words[line_idx + 1 + phrase_idx]
                            if difflib.SequenceMatcher(isjunk=None,
                                                       a=alphanum_regex.sub('', str(phrase_word.lower())),
                                                       b=alphanum_regex.sub('', str(
                                                           next_word.text.lower()))).ratio() > min_textdistance:
                                match_phrase = True
                                tword = TWord(trp_word=next_word,
                                              doc_width=self.doc_width,
                                              doc_height=self.doc_height,
                                              page_number=page_number)
                                tword.text = phrase_word.lower()
                                found_words.append(tword)
                    if match_phrase:
                        found_phrase: TWord = TWord.combine_multiple_words_to_phrase(found_words)
                        found_phrases.append(found_phrase)
                        # found_tuples.append((self.textract_doc_uuid, ) +
                        #                     found_phrase.get_tupel())
            page_number += 1
        # store for future requests
        self.ocrdb.insert_bulk(textract_doc_uuid=self.textract_doc_uuid, rows=found_phrases)
        return found_phrases

    def get_db_conn(self):
        return self.ocrdb.conn
