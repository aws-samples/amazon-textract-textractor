import os
from textractgeofinder.ocrdb import AreaSelection
from typing import List
from textractgeofinder.tgeofinder import SelectionElement, NoPhraseForAreaFoundError, PhraseCoordinate, PointValueType
import trp.trp2 as t2
import textractgeofinder.tgeofinder as tq
import json
import logging
import pytest

logger = logging.getLogger(__name__)


def test_words_between_words(caplog):
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger='textractgeofinder')
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/tquery_samples.json")
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=1000, doc_width=1000)
        word_left = qdoc.find_phrase_in_lines("word_left")[0]
        word_right = qdoc.find_phrase_in_lines("word_right")[0]
        r = qdoc.get_words_between_words(word_left, word_right)
        assert "text in between the words" == " ".join([w.text for w in r])


def test_get_value_for_phrase_coordiante(caplog):
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger='textractgeofinder')
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/test_sample.json")
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=1000, doc_width=1000)
        c = qdoc.get_values_for_phrase_coordinate(
            phrase_coordinates=[tq.PhraseCoordinate(phrase="word_left", coordinate=tq.PointValueType.XMAX)])
        assert c == [98]
        c = qdoc.get_values_for_phrase_coordinate(phrase_coordinates=[
            tq.PhraseCoordinate(phrase="blabla", coordinate=tq.PointValueType.XMAX),
            tq.PhraseCoordinate(phrase="word_left", coordinate=tq.PointValueType.XMAX)
        ])
        assert c == [98]
        # Exception
        with pytest.raises(NoPhraseForAreaFoundError):
            qdoc.get_values_for_phrase_coordinate(
                phrase_coordinates=[tq.PhraseCoordinate(phrase="blabla", coordinate=tq.PointValueType.XMAX)])

        # word_right
        c = qdoc.get_values_for_phrase_coordinate(phrase_coordinates=[
            tq.PhraseCoordinate(phrase="blabla", coordinate=tq.PointValueType.XMAX),
            tq.PhraseCoordinate(phrase="word_right", coordinate=tq.PointValueType.XMAX),
            tq.PhraseCoordinate(phrase="word_left", coordinate=tq.PointValueType.XMAX)
        ])
        assert c == [344]
        c = qdoc.get_values_for_phrase_coordinate(phrase_coordinates=[
            tq.PhraseCoordinate(phrase="blabla", coordinate=tq.PointValueType.XMAX),
            tq.PhraseCoordinate(phrase="word_right", coordinate=tq.PointValueType.XMAX),
            tq.PhraseCoordinate(phrase="word_left", coordinate=tq.PointValueType.XMAX)
        ])
        assert c == [344]
        # multi-value
        c = qdoc.get_values_for_phrase_coordinate(phrase_coordinates=[
            tq.PhraseCoordinate(phrase="test", coordinate=tq.PointValueType.XMAX),
        ])
        assert c == [296, 184, 69, 296, 184, 69]


def test_get_keys_in_area(caplog):
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger='textractgeofinder')

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/patient_intake_form_sample.json")
    doc_height = 1000
    doc_width = 1000
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=doc_height, doc_width=doc_width)
        patient_information = qdoc.find_phrase_in_lines("patient information")[0]
        emergency_contact_1 = qdoc.find_phrase_in_lines("emergency contact 1")[0]
        top_left = t2.TPoint(y=patient_information.ymax, x=0)
        lower_right = t2.TPoint(y=emergency_contact_1.ymin, x=doc_width)
        form_fields = qdoc.get_form_fields_in_area(
            area_selection=AreaSelection(top_left=top_left, lower_right=lower_right, page_number=1))
        assert form_fields
        assert len(form_fields) == 11


def test_get_keys_in_area_multipage(caplog):
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger='textractgeofinder')

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/multi_page_example_file.json")
    doc_height = 1000
    doc_width = 1000
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=doc_height, doc_width=doc_width)
        patient_information = qdoc.find_phrase_in_lines("patient information")[0]
        emergency_contact_1 = qdoc.find_phrase_in_lines("emergency contact 1")[0]
        top_left = t2.TPoint(y=patient_information.ymax, x=0)
        lower_right = t2.TPoint(y=emergency_contact_1.ymin, x=doc_width)
        form_fields = qdoc.get_form_fields_in_area(
            area_selection=AreaSelection(top_left=top_left, lower_right=lower_right, page_number=1))
        assert form_fields
        assert len(form_fields) == 11


def test_get_selection_values_in_area(caplog):
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger='textractgeofinder')

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/patient_intake_form_sample.json")
    doc_height = 1000
    doc_width = 1000
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=doc_height, doc_width=doc_width)
        fever_question = qdoc.find_phrase_on_page("did you feel fever or feverish lately")[0]
        top_left = t2.TPoint(y=fever_question.ymin - 50, x=0)
        lower_right = t2.TPoint(y=fever_question.ymax + 50, x=doc_width)
        sel_values: List[SelectionElement] = qdoc.get_selection_values_in_area(area_selection=AreaSelection(
            top_left=top_left, lower_right=lower_right, page_number=1),
                                                                               exclude_ids=[])
        assert sel_values
        assert len(sel_values) == 2

        cough_question = qdoc.find_phrase_on_page("do you have a cough")[0]
        top_left = t2.TPoint(y=cough_question.ymin - 50, x=0)
        lower_right = t2.TPoint(y=cough_question.ymax + 50, x=doc_width)
        sel_values: List[SelectionElement] = qdoc.get_selection_values_in_area(area_selection=AreaSelection(
            top_left=top_left, lower_right=lower_right, page_number=1),
                                                                               exclude_ids=[])
        assert sel_values
        assert len(sel_values) == 2


def test_phrase_coordinates(caplog):
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger='textractgeofinder')

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/patient_intake_form_sample.json")
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=1000, doc_width=1000)
        r: list[float] = qdoc.get_values_for_phrase_coordinate([
            PhraseCoordinate(phrase="patient information", coordinate=PointValueType.YMIN, min_textdistance=0.95),
            PhraseCoordinate(phrase="emergency contact 1:", coordinate=PointValueType.YMIN, min_textdistance=0.92),
        ])
        assert r


def test_find_word_on_page(caplog):
    caplog.set_level(logging.DEBUG, logger='textractgeofinder')
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/test_sample.json")
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=1920, doc_width=1080)
        r = qdoc.find_word_on_page(word_to_find="word", min_textdistance=0.9)
        assert len(r) == 3

        r = qdoc.find_word_on_page(word_to_find="phrase", min_textdistance=0.9)
        assert len(r) == 3

        r = qdoc.find_word_on_page(word_to_find="test", min_textdistance=0.9)
        assert len(r) == 3


def test_find_phrase_on_page(caplog):
    # caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger='textractquery.tquery')

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/test_sample.json")
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=1920, doc_width=1080)
        r = qdoc.find_phrase_on_page(phrase="word phrase test", min_textdistance=0.9)
        assert len(r) == 3


def test_find_phrase_on_multi_page(caplog):
    # caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger='textractquery.tquery')

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/multi_page_example_file.json")
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=1920, doc_width=1080)
        r = qdoc.find_phrase_on_page(phrase="patient information", min_textdistance=0.9)
        assert r
        r = qdoc.find_phrase_on_page(phrase="patient information", min_textdistance=0.9, page_number=2)
        assert not r
        r = qdoc.find_phrase_on_page(phrase="applicant information", min_textdistance=0.9, page_number=2)
        assert r
        r = qdoc.find_phrase_on_page(phrase="applicant information", min_textdistance=0.9, page_number=1)
        assert not r


def test_find_key_value_on_multi_page(caplog):
    # caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger='textractgeofinder')

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(SCRIPT_DIR, "data/multi_page_example_file.json")
    doc_width = 1080
    with open(os.path.join(SCRIPT_DIR, input_filename)) as input_fp:
        qdoc = tq.TGeoFinder(json.load(input_fp), doc_height=1920, doc_width=doc_width)
        applicant_information = qdoc.find_phrase_on_page(phrase="applicant information",
                                                         min_textdistance=0.9,
                                                         page_number=2)[0]
        assert applicant_information
        previous_employment_history = qdoc.find_phrase_on_page(phrase="previous employment history",
                                                               min_textdistance=0.9,
                                                               page_number=2)[0]
        assert previous_employment_history
        area_selection = AreaSelection(t2.TPoint(x=0, y=applicant_information.ymax),
                                       t2.TPoint(x=doc_width, y=previous_employment_history.ymin),
                                       page_number=2)
        assert area_selection
        area_twords = qdoc.get_area(area_selection)
        assert area_twords
        form_fields = qdoc.get_form_fields_in_area(area_selection=area_selection)
        assert form_fields


def test_phrase_combinations(caplog):
    caplog.set_level(logging.DEBUG)
    phrase = ["test", "1", "2", "3"]
    phrase_combiantions = [["test1", "2", "3"], ["test", "12", "3"], ["test", "1", "23"]]
    assert tq.TGeoFinder.get_phrase_combinations(phrase) == phrase_combiantions
