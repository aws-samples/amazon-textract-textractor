"""The Document class is defined to host all the various DocumentEntity objects within it. :class:`DocumentEntity` objects can be 
accessed, searched and exported the functions given below."""

import boto3
import time
from typing import Any

from textractor.entities.document import Document
from textractor.parsers.response_parser import parse
from textractor.data.constants import TextractAPI
from textractor.utils.results_utils import results_exist
from textractcaller.t_call import (
    get_full_json,
    get_full_json_from_output_config,
    OutputConfig,
)


class LazyDocument:
    """
    LazyDocument is a proxy for Document when using the async APIs. It will not load the response until
    one if its property is used. You can access the underlying Document object using the document property.
    """

    def __init__(
        self,
        job_id: str,
        api: TextractAPI,
        textract_client=None,
        images=None,
        output_config: OutputConfig = None,
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
        self._output_config = output_config
        self._polling_interval = 1
        self._get_result_s3_timeout = 10

    @property
    def polling_interval(self) -> int:
        """Getter for the polling interval

        :return: Time between get_full_result calls
        :rtype: int
        """
        return self._polling_interval

    @polling_interval.setter
    def polling_interval(self, polling_interval: int):
        """Setter for the polling interval

        :param polling_interval: Time between get_full_result calls
        :type polling_interval: int
        """
        self._polling_interval = polling_interval

    @property
    def get_result_s3_timeout(self) -> int:
        """Getter for the timeout when getting results from S3. This is useful as a final condition when the Textract call failed.

        :return: Timeout in second to wait before calling Textract GetDocumentAnalysis
        :rtype: int
        """
        return self._get_result_s3_timeout

    @get_result_s3_timeout.setter
    def get_result_s3_timeout(self, timeout: int):
        """Setter for the timeout when getting results from S3.

        :param timeout: Timeout in second to wait before calling Textract GetDocumentAnalysis
        :type timeout: int
        """
        self._get_result_s3_timeout = timeout

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
        if __name in [
            "job_id",
            "_api",
            "_textract_client",
            "_document",
            "_images",
            "polling_interval",
            "_polling_interval",
            "get_result_s3_timeout",
            "_get_result_s3_timeout",
            "_output_config",
        ]:
            return object.__getattribute__(self, __name)

        if self._document is None:
            if self._output_config:
                s3_client = boto3.client("s3")
                start = time.time()
                response = None
                while not results_exist(
                    self.job_id,
                    self._output_config.s3_bucket,
                    self._output_config.s3_prefix,
                    s3_client,
                ):
                    time.sleep(self._polling_interval)
                    if time.time() - start > self._get_result_timeout:
                        response = get_full_json(
                            self.job_id,
                            TextractAPI.TextractAPI_to_Textract_API(self._api)
                            if isinstance(self._api, TextractAPI)
                            else self._api,
                            self._textract_client,
                            job_done_polling_interval=self._polling_interval,
                        )
                        break
                if not response:
                    response = get_full_json_from_output_config(
                        self._output_config,
                        self.job_id,
                        s3_client,
                    )
            else:
                if not self._textract_client:
                    self._textract_client = boto3.client("textract")
                response = get_full_json(
                    self.job_id,
                    TextractAPI.TextractAPI_to_Textract_API(self._api)
                    if isinstance(self._api, TextractAPI)
                    else self._api,
                    self._textract_client,
                    job_done_polling_interval=self._polling_interval,
                )
            self._document = parse(response)
            if self._images is not None:
                for i, page in enumerate(self._document.pages):
                    page.image = self._images[i]
            self._document.response = response
        return object.__getattribute__(
            object.__getattribute__(self, "_document"), __name
        )
