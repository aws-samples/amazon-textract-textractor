from textractgeofinder.ocrdb import AreaSelection
from textractgeofinder.tgeofinder import KeyValue, TGeoFinder, AreaSelection, SelectionElement
import trp.trp2 as t2
import logging

logger = logging.getLogger(__name__)


def set_hierarchy_kv(list_kv: list[KeyValue], t_document: t2.TDocument, page_block: t2.TBlock, prefix="BORROWER"):
    for x in list_kv:
        t_document.add_virtual_key_for_existing_key(key_name=f"{prefix}_{x.key.text}",
                                                    existing_key=t_document.get_block_by_id(x.key.id),
                                                    page_block=page_block)


def add_sel_elements(t_document: t2.TDocument, selection_values: list[SelectionElement], key_base_name: str,
                     page_block: t2.TBlock) -> t2.TDocument:
    for sel_element in selection_values:
        sel_key_string = "_".join([s_key.original_text.upper() for s_key in sel_element.key if s_key.original_text])
        if sel_key_string:
            if sel_element.selection.original_text:
                t_document.add_virtual_key_for_existing_key(page_block=page_block,
                                                            key_name=f"{key_base_name}->{sel_key_string}",
                                                            existing_key=t_document.get_block_by_id(
                                                                sel_element.key[0].id))
    return t_document


def add_key_value_lables(t_document: t2.TDocument) -> t2.TDocument:
    t_doc = t2.TDocumentSchema().dump(t_document)
    doc_height = 1000
    doc_width = 1000
    geofinder_doc = TGeoFinder(t_doc, doc_height=doc_height, doc_width=doc_width)
    # patient information
    patient_information = geofinder_doc.find_phrase_on_page("patient information")[0]
    emergency_contact_1 = geofinder_doc.find_phrase_on_page("emergency contact 1:", min_textdistance=0.99)[0]
    top_left = t2.TPoint(y=patient_information.ymax, x=0)
    lower_right = t2.TPoint(y=emergency_contact_1.ymin, x=doc_width)
    form_fields = geofinder_doc.get_form_fields_in_area(
        area_selection=AreaSelection(top_left=top_left, lower_right=lower_right, page_number=1))
    set_hierarchy_kv(list_kv=form_fields, t_document=t_document, prefix='PATIENT', page_block=t_document.pages[0])

    #Emergency contact 1
    emergency_contact_2 = geofinder_doc.find_phrase_on_page("emergency contact 2:", min_textdistance=0.99)[0]
    logger.debug(f"emergency_contact_2: {emergency_contact_2}")
    top_left = t2.TPoint(y=emergency_contact_1.ymax, x=0)
    lower_right = t2.TPoint(y=emergency_contact_2.ymin, x=doc_width)
    form_fields = geofinder_doc.get_form_fields_in_area(
        area_selection=AreaSelection(top_left=top_left, lower_right=lower_right, page_number=1))
    set_hierarchy_kv(list_kv=form_fields,
                     t_document=t_document,
                     prefix='EMERGENCY_CONTACT_1',
                     page_block=t_document.pages[0])
    #Emergency contact 2
    fever_question = geofinder_doc.find_phrase_on_page("did you feel fever or feverish lately")[0]
    top_left = t2.TPoint(y=emergency_contact_2.ymax, x=0)
    lower_right = t2.TPoint(y=fever_question.ymin, x=doc_width)
    form_fields = geofinder_doc.get_form_fields_in_area(
        area_selection=AreaSelection(top_left=top_left, lower_right=lower_right, page_number=1))
    set_hierarchy_kv(list_kv=form_fields,
                     t_document=t_document,
                     prefix='EMERGENCY_CONTACT_2',
                     page_block=t_document.pages[0])

    # fever question
    top_left = t2.TPoint(y=fever_question.ymin - 50, x=0)
    lower_right = t2.TPoint(y=fever_question.ymax + 50, x=doc_width)
    sel_values: list[SelectionElement] = geofinder_doc.get_selection_values_in_area(area_selection=AreaSelection(
        top_left=top_left, lower_right=lower_right, page_number=1),
                                                                                    exclude_ids=[])
    add_sel_elements(t_document=t_document,
                     selection_values=sel_values,
                     key_base_name="FEVER",
                     page_block=t_document.pages[0])

    # shortness breath
    shortness_question = geofinder_doc.find_phrase_on_page("Are you having shortness of breath")[0]

    top_left = t2.TPoint(y=shortness_question.ymin - 50, x=0)
    lower_right = t2.TPoint(y=shortness_question.ymax + 50, x=doc_width)
    sel_values: list[SelectionElement] = geofinder_doc.get_selection_values_in_area(area_selection=AreaSelection(
        top_left=top_left, lower_right=lower_right, page_number=1),
                                                                                    exclude_ids=[])
    add_sel_elements(t_document=t_document,
                     selection_values=sel_values,
                     key_base_name="SHORTNESS",
                     page_block=t_document.pages[0])

    # cough breath
    question = geofinder_doc.find_phrase_on_page("Do you have a cough")[0]

    top_left = t2.TPoint(y=question.ymin - 50, x=0)
    lower_right = t2.TPoint(y=question.ymax + 50, x=doc_width)
    sel_values: list[SelectionElement] = geofinder_doc.get_selection_values_in_area(area_selection=AreaSelection(
        top_left=top_left, lower_right=lower_right, page_number=1),
                                                                                    exclude_ids=[])
    add_sel_elements(t_document=t_document,
                     selection_values=sel_values,
                     key_base_name="COUGH",
                     page_block=t_document.pages[0])
    # loss of taste
    question = geofinder_doc.find_phrase_on_page("Did you experience loss of taste or smell")[0]
    top_left = t2.TPoint(y=question.ymin - 50, x=0)
    lower_right = t2.TPoint(y=question.ymax + 50, x=doc_width)
    sel_values: list[SelectionElement] = geofinder_doc.get_selection_values_in_area(area_selection=AreaSelection(
        top_left=top_left, lower_right=lower_right, page_number=1),
                                                                                    exclude_ids=[])
    add_sel_elements(t_document=t_document,
                     selection_values=sel_values,
                     key_base_name="LOSS_OF_TASTE",
                     page_block=t_document.pages[0])
    # COVID Contact
    question = geofinder_doc.find_phrase_on_page("Where you in contact with any confirmed")[0]
    top_left = t2.TPoint(y=question.ymin - 50, x=0)
    lower_right = t2.TPoint(y=question.ymax + 50, x=doc_width)
    sel_values: list[SelectionElement] = geofinder_doc.get_selection_values_in_area(area_selection=AreaSelection(
        top_left=top_left, lower_right=lower_right, page_number=1),
                                                                                    exclude_ids=[])
    add_sel_elements(t_document=t_document,
                     selection_values=sel_values,
                     key_base_name="COVID_CONTACT",
                     page_block=t_document.pages[0])
    # travel
    question = geofinder_doc.find_phrase_on_page("Did you travel in the past 14 days")[0]
    top_left = t2.TPoint(y=question.ymin - 50, x=0)
    lower_right = t2.TPoint(y=question.ymax + 50, x=doc_width)
    sel_values: list[SelectionElement] = geofinder_doc.get_selection_values_in_area(area_selection=AreaSelection(
        top_left=top_left, lower_right=lower_right, page_number=1),
                                                                                    exclude_ids=[])
    add_sel_elements(t_document=t_document,
                     selection_values=sel_values,
                     key_base_name="TRAVEL",
                     page_block=t_document.pages[0])
    return t_document
