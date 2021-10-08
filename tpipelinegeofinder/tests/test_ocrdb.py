from textractgeofinder.ocrdb import OCRDB
from textractgeofinder.tword import TWord
import logging

logger = logging.getLogger(__name__)


def test_creation(caplog):
    caplog.set_level(logging.DEBUG)
    ocrdb = OCRDB.getInstance()
    tword: TWord = TWord(text='sometext',
                         original_text='SomeText',
                         text_type='word',
                         confidence=71.7424087524414,
                         id='e5d9a27b-483c-4c8b-9d09-4092d050e2e4',
                         xmin=100,
                         ymin=0,
                         xmax=263,
                         ymax=22,
                         page_number=1,
                         doc_width=1080,
                         doc_height=1920,
                         child_relationships='',
                         reference=None,
                         resolver=None)
    ocrdb.insert(textract_doc_uuid='bla', x=tword)
    logger.debug(f"tword: {tword}")
