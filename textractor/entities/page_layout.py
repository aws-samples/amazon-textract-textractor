from textractor.entities.layout import Layout
from textractor.visualizers.entitylist import EntityList


class PageLayout:
    """
    Object representation of the layout components detected in the table.
    """

    def __init__(
        self,
        titles: EntityList[Layout] = EntityList([]),
        headers: EntityList[Layout] = EntityList([]),
        footers: EntityList[Layout] = EntityList([]),
        section_headers: EntityList[Layout] = EntityList([]),
        page_numbers: EntityList[Layout] = EntityList([]),
        lists: EntityList[Layout] = EntityList([]),
        figures: EntityList[Layout] = EntityList([]),
        tables: EntityList[Layout] = EntityList([]),
        key_values: EntityList[Layout] = EntityList([]),
    ):
        self._titles = titles
        self._headers = headers
        self._footers = footers
        self._section_headers = section_headers
        self._page_numbers = page_numbers
        self._lists = lists
        self._figures = figures
        self._tables = tables
        self._key_values = key_values

    @property
    def titles(self) -> EntityList[Layout]:
        """Titles detected in the Page

        :return: EntityList of titles detected in the page
        :rtype: EntityList[Layout]
        """
        return self._titles

    @property
    def headers(self) -> EntityList[Layout]:
        """Headers detected in the Page

        :return: EntityList of headers detected in the page
        :rtype: EntityList[Layout]
        """
        return self._headers

    @property
    def footers(self) -> EntityList[Layout]:
        """Footers detected in the Page

        :return: EntityList of footers detected in the page
        :rtype: EntityList[Layout]
        """
        return self._footers

    @property
    def section_headers(self) -> EntityList[Layout]:
        """Section headers detected in the Page

        :return: EntityList of section headers detected in the page
        :rtype: EntityList[Layout]
        """
        return self._section_headers

    @property
    def page_numbers(self) -> EntityList[Layout]:
        """Page numbers detected in the Page

        :return: EntityList of page numbers detected in the page
        :rtype: EntityList[Layout]
        """
        return self._page_numbers

    @property
    def lists(self) -> EntityList[Layout]:
        """Lists detected in the Page

        :return: EntityList of lists detected in the page
        :rtype: EntityList[Layout]
        """
        return self._lists

    @property
    def figures(self) -> EntityList[Layout]:
        """Figures detected in the Page

        :return: EntityList of figures detected in the page
        :rtype: EntityList[Layout]
        """
        return self._figures

    @property
    def tables(self) -> EntityList[Layout]:
        """Tables detected in the Page. This includes Tables detected by the AnalyzeDocument Tables API if used.

        :return: EntityList of tables detected in the page
        :rtype: EntityList[Layout]
        """
        return self._tables

    @property
    def key_values(self) -> EntityList[Layout]:
        """KeyValues detected in the Page

        :return: EntityList of keyvalues detected in the page
        :rtype: EntityList[Layout]
        """
        return self._key_values
