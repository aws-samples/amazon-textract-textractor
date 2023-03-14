"""The ExpenseDocument class is the object representation of an AnalyzeID response. It is similar to a dictionary. Despite its name it does not inherit from Document as the AnalyzeID response does not contains position information."""

from collections import defaultdict
from typing import List

from textractor.data.constants import AnalyzeExpenseFieldsGroup as AEFieldsGroup, AnalyzeExpenseFields as AEFields
from textractor.entities.expense_field import ExpenseField, LineItemGroup, BoundingBox, DocumentEntity


class Fields(dict):
    """
    Dictionary to hold Summary Fields
    Dynamically added properties to enable ease of discovery
    """
    def __init__(self):
        super(Fields, self).__init__()
        # We dynamically set the fields to None to help with discoverability
        for field in AEFields:
            setattr(self.__class__, field.name, property(lambda self, field=field: self.get(field.name)))

    def __repr__(self):
        output = ""
        for key, value in self.items():
            output += f"{key}:"
            offset = 0
            if len(value):
                output += "\n"
                offset = 4
            for field in value:
                output += " "*offset + str(field).replace('\n', '\\n') + "\n"

        return output

class FieldsGroups(dict):
    """
    Summary Fields Group dictionary
    {GROUP_KEY_NAME: {GROUP_ID_1: [SUMMARY_FIELD1, SUMMARY_FIELD2]}}
    """

    def __init__(self):
        super(FieldsGroups, self).__init__()
        for group in AEFieldsGroup:
            setattr(self.__class__, group.name, property(lambda self, group=group: self.get(group.name)))

    def __repr__(self):
        output = ""
        for key, group in self.items():
            output += f"{key}: \n"
            for block in group.values():
                for expense_field in block:
                    output +=  "  " + str(expense_field).replace('\n', '\\n') + "\n"
                output += "\n"
            output += "\n"
        return output

    def get_group_bboxes(self, key: str):
        """
        Return the enclosing bboxes for each group for a given group key
        :param key: Group key e.g VENDOR
        :return:
        """
        bboxes = []
        for groups in self.get(key, {}).values():
            bboxes.append(BoundingBox.enclosing_bbox([f.bbox for f in groups]))
        return bboxes


class ExpenseDocument(DocumentEntity):
    """
    Represents the description of a single expense document.
    """

    def __init__(
        self, summary_fields: List[ExpenseField], line_items_groups: List[LineItemGroup], bounding_box: BoundingBox, page:int
    ):
        """
        :param summary_fields: List of ExpenseFields, not including line item ones
        :param line_items_groups: Groups of Line Item tables
        :param bounding_box: The bounding box for that ExpenseDocument
        :param page: The page where that document is
        """
        super().__init__('', bbox=bounding_box)
        self._summary_fields_list = summary_fields
        self._line_items_groups = line_items_groups
        self.summary_fields = Fields()
        self.summary_groups = FieldsGroups()
        self._unnormalized_fields = defaultdict(list)
        self._assign_summary_fields()
        self._page = page

    @property
    def page(self):
        return self._page

    @property
    def bbox(self):
        return BoundingBox.enclosing_bbox([s.bbox for s in self._summary_fields_list]+[g.bbox for g in self._line_items_groups], spatial_object=self._bbox.spatial_object)

    def _assign_summary_fields(self):
        for field in self._summary_fields_list:
            # We assign them as properties
            name = field.type.text

            # Adding it to the dicts of normalized field
            if name in self.summary_fields:
                self.summary_fields[name].append(field)
            else:
                self.summary_fields[name] = [field]

            # Adding it to the dicts of unnormalized fields using the provided key
            key = field.key.text if field.key else ""
            self._unnormalized_fields[key].append(field)

            # If the field is part of a group, we add it to the list of fields for that group
            for group_properties in field.group_properties:
                for property_type in group_properties.types:
                    if property_type not in self.summary_groups:
                        self.summary_groups[property_type] = dict()
                    if group_properties.id not in self.summary_groups[property_type]:
                        self.summary_groups[property_type][group_properties.id] = []
                    self.summary_groups[property_type][group_properties.id].append(field)

    @property
    def summary_fields_list(self):
        return self._summary_fields_list

    @property
    def line_items_groups(self) -> List[LineItemGroup]:
        return self._line_items_groups

    def __repr__(self) -> str:
        output = f"Summary fields: {len(self.summary_fields)}\n"
        output += "Line Item Groups:"
        output += "\n" if len(self.line_items_groups) > 1 else " "
        for i, line_item in enumerate(self.line_items_groups):
            output += f"index {line_item.index}: {len(line_item.rows)} row{'s' if (len(line_item.rows) > 1) else ''}"
        return output

