import logging
import trp.trp2 as t2
import os
from typing import List, Union
from dataclasses import dataclass, asdict
from PIL import Image, ImageSequence
from PyPDF2 import PdfReader
import boto3
import io

logger = logging.getLogger(__name__)

only_async_suffixes = ['.pdf']
tiff_suffixes = ['.tiff', '.tif']
sync_suffixes = ['.png', '.jpg', '.jpeg'] + tiff_suffixes
supported_suffixes = only_async_suffixes + sync_suffixes


@dataclass
class DocumentDimensions():
    doc_width: float
    doc_height: float


def get_size_from_filestream(fs, ext) -> List[DocumentDimensions]:
    return_value: List[DocumentDimensions] = list()
    if ext in only_async_suffixes:
        # TODO: assumes the order of pages in blocks is correct, when calling Textract with bytes the block.page is empty
        input1 = PdfReader(fs)
        for page in input1.pages:
            pdf_page = page.mediabox
            return_value.append(DocumentDimensions(doc_width=float(pdf_page[2]), doc_height=float(pdf_page[3])))
    else:
        img = Image.open(fs)
        for _, page in enumerate(ImageSequence.Iterator(img)):
            return_value.append(DocumentDimensions(doc_width=float(page.width), doc_height=float(page.height)))
    return return_value


def get_size_from_s3(s3_bucket, s3_key):
    _, ext = os.path.splitext(s3_key)
    if ext in supported_suffixes:
        s3 = boto3.client('s3')
        o = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        input_bytes = o.get('Body').read()
        f = io.BytesIO(input_bytes)
        return get_size_from_filestream(f, ext)
    else:
        raise ValueError(f"{s3_key} not in {supported_suffixes}")


def get_width_height_from_s3_object(s3_bucket, s3_key):
    return get_size_from_s3(s3_bucket, s3_key)


def get_width_height_from_file(filepath):
    _, ext = os.path.splitext(filepath)
    if ext in supported_suffixes:
        with open(filepath, 'rb') as input_fs:
            return get_size_from_filestream(input_fs, ext)
    else:
        raise ValueError(f"{filepath} not in {supported_suffixes}")


def add_page_dimensions(t_document: t2.TDocument, input_document: Union[str, bytes]) -> t2.TDocument:
    """
    adds Page Dimensions to each page of the document in the form of a custom property on the Block
    e. g. {'PageDimension': {'doc_width': 1549.0, 'doc_height': 370.0} }

    """
    page_dimensions: List[DocumentDimensions] = list()

    if isinstance(input_document, str):
        if len(input_document) > 7 and input_document.lower().startswith("s3://"):
            input_document = input_document.replace("s3://", "")
            s3_bucket, s3_key = input_document.split("/", 1)
            page_dimensions = get_width_height_from_s3_object(s3_bucket=s3_bucket, s3_key=s3_key)
        else:
            page_dimensions = get_width_height_from_file(filepath=input_document)

    elif isinstance(input_document, (bytes, bytearray)):
        page_dimensions = get_size_from_filestream(io.BytesIO(input_document), ext=None)
    # bytes do not return a page for the Block, cannot use the mapping logic as above
    if len(t_document.pages) != len(page_dimensions):
        raise AssertionError(
            f"number of pages in document did not match number of dimensions received: document-pages: {len(t_document.pages)}, dimension-pages: {len(page_dimensions)}"
        )
    for idx, block in enumerate(t_document.pages):
        if block.custom:
            if block.page:
                block.custom['PageDimension'] = asdict(page_dimensions[block.page - 1])
            else:
                block.custom['PageDimension'] = asdict(page_dimensions[idx])
        else:
            if block.page:
                block.custom = {'PageDimension': asdict(page_dimensions[block.page - 1])}
            else:
                block.custom = {'PageDimension': asdict(page_dimensions[idx])}

    return t_document
