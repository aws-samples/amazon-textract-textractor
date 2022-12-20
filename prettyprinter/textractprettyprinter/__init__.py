from ._version import __version__

from .t_pretty_print import Pretty_Print_Table_Format as Pretty_Print_Table_Format
import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())
