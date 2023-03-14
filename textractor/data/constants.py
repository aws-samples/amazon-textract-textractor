"""Multiple feature calls within the Textractor tool require the use of input parameters from fixed choices. \
They've been defined as :code:`Enum` within the data package."""

from enum import Enum
from textractcaller.t_call import Textract_API

from textractor.exceptions import InputError

WORD = "WORD"
LINE = "LINE"
KEY_VALUE_SET = "KEY_VALUE_SET"
SELECTION_ELEMENT = "SELECTION_ELEMENT"
TABLE = "TABLE"
CELL = "CELL"
PAGE = "PAGE"
MERGED_CELL = "MERGED_CELL"
QUERY = "QUERY"
QUERY_RESULT = "QUERY_RESULT"
SIGNATURE = "SIGNATURE"

# cell type attributes
IS_COLUMN_HEAD = "isColumnHead"
IS_SECTION_TITLE_CELL = "isSectionTitleCell"
IS_SUMMARY_CELL = "isSummaryCell"
IS_TITLE_CELL = "isTitleCell"
IS_FOOTER_CELL = "isFooterCell"
IS_MERGED_CELL = "isMergedCell"

# Text Types
HANDWRITING = "HANDWRITING"
PRINTED = "PRINTED"


class Direction(Enum):
    """Directions available for search using DirectionalFinder"""

    ABOVE = 0
    BELOW = 1
    RIGHT = 2
    LEFT = 3


class TextTypes(Enum):
    """Textract recognizes TextType of all words in the document to fall into one of these 2 categories."""

    HANDWRITING = 0
    PRINTED = 1


# selection element attributes
SELECTED = "SELECTED"
NOT_SELECTED = "NOT_SELECTED"


class SelectionStatus(Enum):
    """These are the 2 categories defined for the SelectionStatus of a :class:`SelectionElement`."""

    SELECTED = 0
    NOT_SELECTED = 1


COLUMN_HEADER = "COLUMN_HEADER"
SECTION_TITLE = "SECTION_TITLE"
FLOATING_FOOTER = "FLOATING_FOOTER"
FLOATING_TITLE = "FLOATING_TITLE"
SUMMARY_CELL = "SUMMARY_CELL"


class CellTypes(Enum):
    """Special cells within the :class:`Table` belong to one of these categories."""

    COLUMN_HEADER = 0
    SECTION_TITLE = 1
    FLOATING_FOOTER = 2
    FLOATING_TITLE = 3
    SUMMARY_CELL = 4


FORCE_SYNC = "FORCE_SYNC"
FORCE_ASYNC = "FORCE_ASYNC"
DEFAULT = "DEFAULT"


FORMS = "FORMS"
TABLES = "TABLES"
QUERIES = "QUERIES"


class TextractFeatures(Enum):
    """Features to be used as parameter for AnalyzeDocument and StartDocumentAnalysis."""

    FORMS = 0
    TABLES = 1
    QUERIES = 2
    SIGNATURES = 3


class TextractType(Enum):
    """Document Entity types recognized by Textract APIs."""

    WORDS = 0
    LINES = 1
    KEY_VALUE_SET = 2
    SELECTION_ELEMENT = 3
    TABLES = 4
    TABLE_CELL = 5


class DirectionalFinderType(Enum):
    """Document Entity types recognized by Textract APIs."""

    KEY_VALUE_SET = 0
    SELECTION_ELEMENT = 1


class TableFormat(Enum):
    """Various formats of printing :class:`Table` data with the tabulate package."""

    CSV = 0
    PLAIN = 1
    SIMPLE = 2
    GITHUB = 3
    GRID = 4
    FANCY_GRID = 5
    PIPE = 6
    ORGTBL = 7
    JIRA = 8
    PRESTO = 9
    PRETTY = 10
    PSQL = 11
    RST = 12
    MEDIAWIKI = 13
    MOINMOIN = 14
    YOUTRACK = 15
    HTML = 16
    UNSAFEHTML = 17
    LATEX = 18
    LATEX_RAW = 19
    LATEX_BOOKTABS = 20
    LATEX_LONGTABLE = 21
    TEXTILE = 22
    TSV = 23


class SimilarityMetric(Enum):
    """
    Similarity metrics for search queries on Document data

    COSINE: Cosine similarity is a metric used to measure the similarity of two vectors. It measures the similarity in the direction or orientation of the vectors ignoring differences in their magnitude or scale.
    EUCLIDEAN: Euclidean distance is calculated as the square root of the sum of the squared differences between the two vectors.
    LEVENSHTEIN: The Levenshtein distance is a string metric for measuring difference between two sequences. It is the minimum number of single-character edits (i.e. insertions, deletions or substitutions) required to change one word into the other.
    """

    COSINE = 0
    EUCLIDEAN = 1
    LEVENSHTEIN = 2


class TextractAPI(Enum):
    """API types for asynchronous type fetching"""

    DETECT_TEXT = 0
    ANALYZE = 1
    EXPENSE = 2

    @classmethod
    def TextractAPI_to_Textract_API(cls, api):
        if api == TextractAPI.DETECT_TEXT:
            return Textract_API.DETECT
        elif api == TextractAPI.ANALYZE:
            return Textract_API.ANALYZE
        elif api == TextractAPI.EXPENSE:
            return Textract_API.EXPENSE
        else:
            raise InputError()

    @classmethod
    def Textract_API_to_TextractAPI(cls, api: Textract_API):
        if api == Textract_API.DETECT:
            return TextractAPI.DETECT_TEXT
        elif api == Textract_API.ANALYZE:
            return TextractAPI.ANALYZE
        elif api == Textract_API.EXPENSE:
            return TextractAPI.EXPENSE
        else:
            raise InputError()


class AnalyzeIDFields(Enum):
    """Enum containing all the AnalyzeID keys"""

    FIRST_NAME = "FIRST_NAME"
    LAST_NAME = "LAST_NAME"
    MIDDLE_NAME = "MIDDLE_NAME"
    SUFFIX = "SUFFIX"
    CITY_IN_ADDRESS = "CITY_IN_ADDRESS"
    ZIP_CODE_IN_ADDRESS = "ZIP_CODE_IN_ADDRESS"
    STATE_IN_ADDRESS = "STATE_IN_ADDRESS"
    COUNTY = "COUNTY"
    DOCUMENT_NUMBER = "DOCUMENT_NUMBER"
    EXPIRATION_DATE = "EXPIRATION_DATE"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    STATE_NAME = "STATE_NAME"
    DATE_OF_ISSUE = "DATE_OF_ISSUE"
    CLASS = "CLASS"
    RESTRICTIONS = "RESTRICTIONS"
    ENDORSEMENTS = "ENDORSEMENTS"
    ID_TYPE = "ID_TYPE"
    VETERAN = "VETERAN"
    ADDRESS = "ADDRESS"
    # Only available in passports
    PLACE_OF_BIRTH = "PLACE_OF_BIRTH"

class AnalyzeExpenseLineItemFields(Enum):
    ITEM = "ITEM"
    PRICE = "PRICE"
    PRODUCT_CODE = "PRODUCT_CODE"
    QUANTITY = "QUANTITY"
    UNIT_PRICE = "UNIT_PRICE"
    EXPENSE_ROW = "EXPENSE_ROW"

class AnalyzeExpenseFields(Enum):
    ACCOUNT_NUMBER = "ACCOUNT_NUMBER"
    ADDRESS = "ADDRESS"
    ADDRESS_BLOCK = "ADDRESS_BLOCK"
    AMOUNT_DUE = "AMOUNT_DUE"
    AMOUNT_PAID = "AMOUNT_PAID"
    CITY = "CITY"
    COUNTRY = "COUNTRY"
    CUSTOMER_NUMBER = "CUSTOMER_NUMBER"
    DELIVERY_DATE = "DELIVERY_DATE"
    DISCOUNT = "DISCOUNT"
    DUE_DATE = "DUE_DATE"
    GRATUITY = "GRATUITY"
    INVOICE_RECEIPT_DATE = "INVOICE_RECEIPT_DATE"
    INVOICE_RECEIPT_ID = "INVOICE_RECEIPT_ID"
    NAME = "NAME"
    ORDER_DATE = "ORDER_DATE"
    OTHER = "OTHER"
    PAYMENT_TERMS = "PAYMENT_TERMS"
    PO_NUMBER = "PO_NUMBER"
    PRIOR_BALANCE = "PRIOR_BALANCE"
    RECEIVER_ABN_NUMBER = "RECEIVER_ABN_NUMBER"
    RECEIVER_ADDRESS = "RECEIVER_ADDRESS"
    RECEIVER_GST_NUMBER = "RECEIVER_GST_NUMBER"
    RECEIVER_NAME = "RECEIVER_NAME"
    RECEIVER_PAN_NUMBER = "RECEIVER_PAN_NUMBER"
    RECEIVER_PHONE = "RECEIVER_PHONE"
    RECEIVER_VAT_NUMBER = "RECEIVER_VAT_NUMBER"
    SERVICE_CHARGE = "SERVICE_CHARGE"
    SHIPPING_HANDLING_CHARGE = "SHIPPING_HANDLING_CHARGE"
    STATE = "STATE"
    STREET = "STREET"
    SUBTOTAL = "SUBTOTAL"
    TAX = "TAX"
    TAX_PAYER_ID = "TAX_PAYER_ID"
    TOTAL = "TOTAL"
    VENDOR_ABN_NUMBER = "VENDOR_ABN_NUMBER"
    VENDOR_ADDRESS = "VENDOR_ADDRESS"
    VENDOR_GST_NUMBER = "VENDOR_GST_NUMBER"
    VENDOR_NAME = "VENDOR_NAME"
    VENDOR_PAN_NUMBER = "VENDOR_PAN_NUMBER"
    VENDOR_PHONE = "VENDOR_PHONE"
    VENDOR_URL = "VENDOR_URL"
    VENDOR_VAT_NUMBER = "VENDOR_VAT_NUMBER"
    ZIP_CODE = "ZIP_CODE"

class AnalyzeExpenseFieldsGroup(Enum):
    RECEIVER = "RECEIVER"
    RECEIVER_BILL_TO = "RECEIVER_BILL_TO"
    RECEIVER_SHIP_TO = "RECEIVER_SHIP_TO"
    RECEIVER_SOLD_TO = "RECEIVER_SOLD_TO"
    VENDOR = "VENDOR"
    VENDOR_REMIT_TO = "VENDOR_REMIT_TO"
    VENDOR_SUPPLIER = "VENDOR_SUPPLIER"

class CLIPrint(Enum):
    ALL = 0
    TEXT = 1
    TABLES = 2
    FORMS = 3
    QUERIES = 4
    EXPENSES = 5
    SIGNATURES = 6
    IDS = 7


class CLIOverlay(Enum):
    ALL = 0
    WORDS = 1
    LINES = 2
    TABLES = 3
    FORMS = 4
    QUERIES = 5
    SIGNATURE = 6
