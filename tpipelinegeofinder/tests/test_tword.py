from textractgeofinder.tword import TWord
import logging

logger = logging.getLogger(__name__)


def test_creation(caplog):
    caplog.set_level(logging.DEBUG)
    tword: TWord = TWord(text="test",
                         text_type="text_type",
                         confidence=99,
                         id="test-id",
                         page_number=1,
                         ymin=1,
                         ymax=1,
                         xmin=10,
                         xmax=10,
                         original_text="original-text",
                         doc_width=100,
                         doc_height=100,
                         reference="test")
    logger.debug(f"tword: {tword}")
