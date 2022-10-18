"""The ExpenseDocument class is the object representation of an AnalyzeID response. It is similar to a dictionary. Despite its name it does not inherit from Document as the AnalyzeID response does not contains position information."""

import os
from typing import List, Dict, Union
from textractor.entities.bbox import SpatialObject
from textractor.entities.expense_field import ExpenseField

from textractor.exceptions import InputError


class ExpenseDocument(SpatialObject):
    """
    Represents the description of a single expense document.
    """

    def __init__(
        self, summary_fields: List[ExpenseField], line_item_fields: List[ExpenseField]
    ):
        """
        Creates a new document, ideally containing entity objects pertaining to each page.

        :param num_pages: Number of pages in the input Document.
        """
        super().__init__(width=0, height=0)
        self._summary_fields = ExpenseDocument._fields_to_dict(summary_fields)
        self._line_item_fields = ExpenseDocument._fields_to_dict(line_item_fields)

    @classmethod
    def _fields_to_dict(
        cls, fields: Union[List[ExpenseField], List[Dict]]
    ) -> Dict[str, ExpenseField]:
        """Converts a list of expense field to a dictionary of ExpenseField

        :param fields: Expense fields
        :type fields: Union[List[ExpenseField], List[Dict]]
        :raises InputError: Raised if `fields` is not of of type Union[List[ExpenseField], List[Dict]])
        :return: Dictionary that maps keys to ExpenseFields
        :rtype: Dict[str, ExpenseField]
        """
        if not fields:
            return {}
        elif isinstance(fields, list) and isinstance(fields[0], ExpenseField):
            return {
                (
                    expense_field.key.text
                    if expense_field.key else
                    expense_field.type.text
                ): expense_field
                for expense_field in fields
            }
        elif isinstance(fields, list) and isinstance(fields[0], dict):
            field_dict = {}
            for expense_field in fields.values():
                field_dict[expense_field["key"]] = ExpenseField(
                    expense_field["key"],
                    expense_field["value"],
                    expense_field["confidence"],
                )
            return field_dict
        else:
            raise InputError(
                f"fields needs to be a list of ExpenseFields or a list of dictionaries, not {type(fields)}"
            )

    @property
    def summary_fields(self) -> Dict[str, ExpenseField]:
        """Returns a dictionary of summary fields

        :return: Dictionary of summary fields
        :rtype: Dict[str, ExpenseField]
        """
        return self._summary_fields

    @summary_fields.setter
    def summary_fields(self, summary_fields: Dict[str, ExpenseField]):
        """Setter for summary_fields

        :param summary_fields: Summary fields
        :type summary_fields: Dict[str, ExpenseField]
        """
        self._summary_fields = summary_fields

    def __getitem__(self, key) -> str:
        return self._summary_fields.get(key, self._line_item_fields.get(key)).value

    def get(self, key) -> Union[str, None]:
        result = self._summary_fields.get(key, self._line_item_fields.get(key))
        if result is None:
            return None
        return result.value

    def keys(self) -> List[str]:
        return list(self._summary_fields.keys())

    def __repr__(self) -> str:
        return os.linesep.join(
            [f"{str(k)}: {str(v)}" for k, v in self._summary_fields.items()]
        )
