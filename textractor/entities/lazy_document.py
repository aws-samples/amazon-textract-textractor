"""The Document class is defined to host all the various DocumentEntity objects within it. :class:`DocumentEntity` objects can be 
accessed, searched and exported the functions given below."""

from typing import Any

from textractor.entities.document import Document
from textractor.parsers.response_parser import parse
from textractor.data.constants import TextractAPI
from textractcaller.t_call import get_full_json


class LazyDocument:
    """
    LazyDocument is a proxy for Document when using the async APIs. It will not load the response until
    one if its property is used. You can access the underlying Document object using the document property.
    """

    def __init__(
        self, job_id: str, api: TextractAPI, textract_client=None, images=None
    ):
        """
        Creates a new document, ideally containing entity objects pertaining to each page.

        :param num_pages: Number of pages in the input Document.
        """
        self.job_id = job_id
        self._api = api
        self._textract_client = textract_client
        self._document = None
        self._images = images

    @property
    def document(self) -> Document:
        """Getter for the underlying Document object

        :return: Proxied Document object
        :rtype: Document
        """
        return object.__getattribute__(self, "_document")

    def __getattr__(self, __name: str) -> Any:
        """Proxy that gets the Document result when a document property is
        accessed. This a blocking call.

        :param __name: Name of the attribute
        :type __name: str
        :return: Value of the attribute
        :rtype: Any
        """

        # Prevents infinite recursion on LazyDocument properties
        if __name in ["job_id", "_api", "_textract_client", "_document", "_images"]:
            return object.__getattribute__(self, __name)

        if self._document is None:
            response = get_full_json(
                self.job_id,
                TextractAPI.TextractAPI_to_Textract_API(self._api)
                if isinstance(self._api, TextractAPI)
                else self._api,
                self._textract_client,
            )
            self._document = parse(response)
            if self._images is not None:
                for i, page in enumerate(self._document.pages):
                    page.image = self._images[i]
            self._document.response = response
        return object.__getattribute__(
            object.__getattribute__(self, "_document"), __name
        )
