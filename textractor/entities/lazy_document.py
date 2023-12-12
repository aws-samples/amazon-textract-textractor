"""The Document class is defined to host all the various DocumentEntity objects within it. :class:`DocumentEntity` objects can be 
accessed, searched and exported the functions given below."""

import boto3
import time
from typing import Any

from textractor.entities.document import Document
from textractor.parsers.response_parser import parse
from textractor.data.constants import TextractAPI
from textractor.utils.results_utils import results_exist, get_full_json_from_output_config
from textractcaller.t_call import (
    get_job_response,
    get_full_json,
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
        self._s3_polling_interval = 1
        self._textract_polling_interval = 5

    @property
    def s3_polling_interval(self) -> int:
        """Getter for the polling interval

        :return: Time between get_full_result calls
        :rtype: int
        """
        return self._s3_polling_interval

    @s3_polling_interval.setter
    def s3_polling_interval(self, s3_polling_interval: int):
        """Setter for the polling interval

        :param polling_interval: Time between get_full_result calls
        :type polling_interval: int
        """
        self._s3_polling_interval = s3_polling_interval

    @property
    def textract_polling_interval(self) -> int:
        """Getter for the polling interval

        :return: Time between get_full_result calls
        :rtype: int
        """
        return self._textract_polling_interval

    @textract_polling_interval.setter
    def textract_polling_interval(self, textract_polling_interval: int):
        """Setter for the polling interval

        :param polling_interval: Time between get_full_result calls
        :type polling_interval: int
        """
        self._textract_polling_interval = textract_polling_interval

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
            "s3_polling_interval",
            "_s3_polling_interval",
            "textract_polling_interval",
            "_textract_polling_interval",
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
                    time.sleep(self._s3_polling_interval)
                    if time.time() - start > self._textract_polling_interval:
                        response = get_job_response(
                            job_id=self.job_id,
                            textract_api=TextractAPI.TextractAPI_to_Textract_API(self._api)
                            if isinstance(self._api, TextractAPI)
                            else self._api,
                            boto3_textract_client=self._textract_client,
                        )
                        job_status = response["JobStatus"]
                        if job_status == "IN_PROGRESS":
                            start = time.time()
                            response = None
                            continue
                        elif job_status == "SUCCEEDED" and "NextToken" in response:
                            response = get_full_json(
                                self.job_id,
                                TextractAPI.TextractAPI_to_Textract_API(self._api)
                                if isinstance(self._api, TextractAPI)
                                else self._api,
                                self._textract_client,
                                job_done_polling_interval=1,
                            )
                            break
                        elif job_status == "SUCCEEDED":
                            break
                        else:
                            raise Exception(f"Job failed with status: {job_status}\n{response}")
                        
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
                    job_done_polling_interval=self.textract_polling_interval,
                )
            self._document = parse(response)
            if self._images is not None:
                for i, page in enumerate(self._document.pages):
                    page.image = self._images[i]
            self._document.response = response
        return object.__getattribute__(
            object.__getattribute__(self, "_document"), __name
        )
