import dataclasses
import os
import logging

from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.data.constants import AnalyzeExpenseLineItemFields as AELineItems
from typing import List

@dataclasses.dataclass
class ExpenseType:
    """
    Type of an ExpenseField, e.g TOTAL or SUBTOTAL
    """
    text: str
    confidence: float
    raw_object: object

@dataclasses.dataclass
class ExpenseGroupProperty:
    """
    Associated with a given ExpenseField, which group it is associated with and the related type of the group
    """
    id: str
    types: List[str]

class Expense(DocumentEntity):
    """
    Holds the Key or the Value of an Expense
    """
    def __init__(self, bbox: BoundingBox, text: str, confidence: float, page: int):
        super(Expense, self).__init__(entity_id="", bbox=bbox)
        self._text = text
        self._confidence = confidence
        self._bbox = bbox
        self._page = page

    @property
    def page(self):
        return self._page

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


class ExpenseField(DocumentEntity):
    """
    The ExpenseField holds the information a given summary field, key, value and type.
    The bounding box of that ExpenseField is the enclosing one of all its components
    """
    def __init__(self, type: ExpenseType, value: Expense, group_properties: List[ExpenseGroupProperty], page:int, label: Expense = None, currency=None):
        super(ExpenseField, self).__init__('', BoundingBox.enclosing_bbox([label, value], spatial_object=value.bbox.spatial_object))
        self._type = type
        self._key = label
        self._value = value
        self._group_properties = group_properties
        self._currency = currency
        self.raw_object = None
        self._page = page

    @property
    def bbox(self) -> BoundingBox:
        return BoundingBox.enclosing_bbox([self.key, self.value], spatial_object=self.value.bbox.spatial_object)

    @property
    def type(self) -> ExpenseType:
        return self._type

    @property
    def key(self) -> Expense:
        return self._key

    @property
    def value(self) -> Expense:
        return self._value

    @property
    def page(self) -> int:
        return self._page

    @property
    def group_properties(self) -> List[ExpenseGroupProperty]:
        return self._group_properties

    def __repr__(self) -> str:
        repr = ""

        if self.type:
            repr += f"{'_' if len(repr) else ''}{str(self.type.text)}"

        if self.key:
            repr += f" ({str(self.key.text)})"

        if self.value:
            repr += f": {str(self.value.text)}".replace('\n', '\\n')

        if self._currency:
            repr += f" [{self._currency}]"

        return repr


class LineItemRow(DocumentEntity):
    """
    A LineItemRow contains several ExpenseField that are all inside the row. They don't always align in
    a structured column structure as tables do.
    """
    def __init__(self, index, line_item_expense_fields: List[ExpenseField], page:int):
        super().__init__('', bbox=BoundingBox.enclosing_bbox([i.bbox for i in line_item_expense_fields]))
        self._index = index
        self._line_item_expense_fields = line_item_expense_fields
        self._page = page

    @property
    def page(self):
        return self._page

    @property
    def expenses(self):
        return self._line_item_expense_fields

    @property
    def bbox(self):
        # Dangerous, we need at least one expense in an expense row
        return BoundingBox.enclosing_bbox([f.bbox for f in self._line_item_expense_fields], spatial_object=self.expenses[0].bbox.spatial_object)

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._line_item_expense_fields[index]
        else:
            for expense in self.expenses:
                if expense.type.text == index:
                    return expense
        raise IndexError(f"{index} is not present in this expense row")

    def get(self, index):
        return self[index]

    def __repr__(self):
        return str(self.expenses)

class LineItemGroup(DocumentEntity):
    """
    A LineItemGroup contains several LineItemRow. It is often similar to a table in invoices
    but in receipts, the table structure can be more loose and less aligned.
    """
    def __init__(self, index, line_item_rows: List[LineItemRow], page:int):
        super(LineItemGroup, self).__init__('', BoundingBox.enclosing_bbox([f.bbox for f in line_item_rows]))
        self._index = index
        self._line_item_rows = line_item_rows
        self._page = page

    @property
    def page(self):
        return self._page

    @property
    def rows(self):
        return self._line_item_rows

    @property
    def index(self):
        return self._index

    @property
    def bbox(self):
        # Dangerous, we need at least one line item in a line item rows
        return BoundingBox.enclosing_bbox([f.bbox for f in self._line_item_rows], self._line_item_rows[0].bbox.spatial_object)

    def to_pandas(self, include_EXPENSE_ROW=False):
        try:
            from pandas import DataFrame
        except ImportError:
            logging.info("pandas library is required for exporting tables to DataFrame objects")
            return None


        types = {field.name for field in AELineItems}
        columns = {field.name: i for i, field in enumerate(AELineItems)}
        for row in self.rows:
            for expense in row.expenses:
                if expense.type.text not in columns:
                    columns[expense.type.text] = max(columns.values()) + 1
                    types.add(expense.type.text)
        data = [['' for _ in range(len(types))] for _ in range(len(self.rows))]

        for i, row in enumerate(self.rows):
            for j, expense in enumerate(row.expenses):
                data[i][columns[expense.type.text]] = expense.value.text

        df = DataFrame(data=data, columns=columns.keys())

        if not include_EXPENSE_ROW:
            df = df.drop(columns=[AELineItems.EXPENSE_ROW.name])

        return df

    def to_csv(self):
        return self.to_pandas().to_csv()

    def to_json(self):
        return self.to_pandas().to_json()

    def __repr__(self) -> str:
        output = ""
        for row in self.rows:
            output += "|"
            for expense in row:
                output += expense.type.text + ": " + expense.value.text.replace(os.linesep, '\\n')
                output += " | "
            output += os.linesep
        return output

    def __getitem__(self, index):
        return self._line_item_rows[index]

