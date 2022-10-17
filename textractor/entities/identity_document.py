"""The IdentityDocument class is the object representation of an AnalyzeID response. It is similar to a dictionary. Despite its name it does not inherit from Document as the AnalyzeID response does not contains position information."""

import os
import string
import logging
import xlsxwriter
from typing import List, Dict, Union
from copy import deepcopy
from collections import defaultdict
from textractor.data.constants import AnalyzeIDFields
from textractor.entities.bbox import SpatialObject
from textractor.entities.identity_field import IdentityField

from textractor.exceptions import InputError


class IdentityDocument(SpatialObject):
    """
    Represents the description of a single ID document.
    """

    def __init__(self, fields=None):
        """
        Creates a new document, ideally containing entity objects pertaining to each page.

        :param num_pages: Number of pages in the input Document.
        """
        super().__init__(width=0, height=0)
        self._fields = IdentityDocument._fields_to_dict(fields)

    @classmethod
    def _fields_to_dict(cls, fields: Union[List[IdentityField], Dict[str, dict]]):
        if not fields:
            return {}
        elif isinstance(fields, list) and isinstance(fields[0], IdentityField):
            return {id_field.key: id_field for id_field in fields}
        elif isinstance(fields, dict):
            field_dict = {}
            for id_field in fields.values():
                field_dict[id_field["key"]] = IdentityField(
                    id_field["key"],
                    id_field["value"],
                    id_field["confidence"],
                )
            return field_dict
        else:
            raise InputError(
                f"fields needs to be a list of IdentityFields or a list of dictionaries, not {type(fields)}"
            )

    @property
    def fields(self) -> Dict[str, IdentityField]:
        return self._fields

    @fields.setter
    def fields(self, fields):
        self._fields = fields

    def keys(self) -> List[str]:
        keys = [key for key in self._fields.keys()]
        return keys

    def values(self) -> List[str]:
        values = [field.value for field in self._fields.values()]
        return values

    def __getitem__(self, key: Union[str, AnalyzeIDFields]) -> str:
        return self._fields[key if isinstance(key, str) else key.value].value

    def get(self, key: Union[str, AnalyzeIDFields]) -> Union[str, None]:
        result = self._fields.get(key if isinstance(key, str) else key.value)
        if result is None:
            return None
        return result.value

    def __repr__(self):
        return os.linesep.join([f"{str(k)}: {str(v)}" for k, v in self.fields.items()])
