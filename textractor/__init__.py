__version__ = "1.10.0"

from .entities.document import Document
from .entities.lazy_document import LazyDocument
from .textractor import Textractor

__all__ = ["Document", "LazyDocument", "Textractor"]
