__version__ = '0.0.2'

import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())
