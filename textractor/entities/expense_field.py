from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity


class Expense(DocumentEntity):
    def __init__(self, text: str, confidence: float, bbox: BoundingBox):
        self._text = text
        self._confidence = confidence
        self._bbox = bbox

    @property
    def text(self):
        return self._text

    @property
    def confidence(self):
        return self._confidence

    @property
    def geometry(self):
        return self._bbox

    def __repr__(self):
        return self._text


class ExpenseField:
    def __init__(self, type: Expense, value: Expense, label: Expense = None):
        self._type = type
        self._key = label
        self._value = value

    @property
    def type(self) -> Expense:
        return self._type

    @property
    def key(self) -> Expense:
        return self._key

    @property
    def value(self) -> Expense:
        return self._value

    def __repr__(self) -> str:
        return str(self._value)
