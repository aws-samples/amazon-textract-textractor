import re
from typing import List, Union
from PIL import Image

try:
    import pypdfium2
    PYPDFIUM2_IS_INSTALLED = True
except ImportError:
    PYPDFIUM2_IS_INSTALLED = False

try:
    from pdf2image import convert_from_bytes, convert_from_path, pdfinfo_from_bytes, pdfinfo_from_path
    PDF2IMAGE_IS_INSTALLED = True
except ImportError:
    PDF2IMAGE_IS_INSTALLED = False
    

def rasterize_pdf(pdf: Union[str, bytes]) -> List[Image.Image]:
    """
    Convert a pdf into a list of images
    """
    if PYPDFIUM2_IS_INSTALLED:
        pdf = pypdfium2.PdfDocument(pdf)
        return [page.render(scale=250 / 72).to_pil() for page in pdf]
    elif PDF2IMAGE_IS_INSTALLED:
        if isinstance(pdf, str):
            return convert_from_path(pdf, dpi=250, fmt="jpeg")
        elif isinstance(pdf, bytes):
            return convert_from_bytes(pdf, dpi=250, fmt="jpeg")
        else:
            raise Exception(f"{type(pdf)} is not a supported type, should be str or bytes")
    else:
        raise Exception("PDF rasterization is not possible if neither pypdfium2 nor pdf2image are installed")