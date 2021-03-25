__version__ = 0.0.1

import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())
