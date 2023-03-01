"""
:class:`Textractor` is the main class associated with this package. It needs to be instantiated before using any of the functionalities
the package provides. The main use of this class is to make calls to the Textract API and create Python objects for all the
document entities that are returned in the JSON output of the API. The response received is implicitly parsed and a :class:`Document` type 
object is returned containing all the document entities, their associated relationships and metadata.

The Textract API and Textractor method mapping is as below. Use these wrappers to make calls and parse the responses
in one step.

* (SYNC) DetectDocumentText : detect_document_text
* (SYNC) AnalyzeDocument : analyze_document
* (SYNC) AnalyzeID : analyze_id
* (SYNC) AnalyzeExpense : analyze_expense
* (ASYNC) StartDocumentTextDetection : start_document_text_detection
* (ASYNC) StartDocumentAnalysis : start_document_analysis
* (ASYNC) StartExpenseAnalysis : start_expense_analysis

"""

import io
import os
import boto3
import logging
import uuid
from PIL import Image
from copy import deepcopy
from typing import List, Union
from textractcaller import (
    call_textract,
    call_textract_analyzeid,
    call_textract_expense,
    OutputConfig,
    Query,
    QueriesConfig,
)
from textractcaller.t_call import Textract_Call_Mode, Textract_API, get_full_json

try:
    from pdf2image import convert_from_bytes, convert_from_path

    IS_PDF2IMAGE_INSTALLED = True
except ImportError:
    IS_PDF2IMAGE_INSTALLED = False
    logging.info("pdf2image is not installed, client-side PDF rasterizing is disabled")

from textractor.data.constants import (
    TextractAPI,
    TextractFeatures,
)
from textractor.entities.document import Document
from textractor.entities.lazy_document import LazyDocument
from textractor.parsers import response_parser
from textractor.utils.s3_utils import upload_to_s3, s3_path_to_bucket_and_prefix
from textractor.exceptions import (
    InputError,
    RegionMismatchError,
    IncorrectMethodException,
    MissingDependencyException,
    UnhandledCaseException,
)


class Textractor:
    """
    Initializes the customer credentials needed to make calls to Textract using boto3 package internally.

    :param profile_name: Customer's profile name as set in the ~/.aws/config file. This profile typically contains this format.
                                :code:`[default]
                                region = us-west-2
                                output=json`
    :type profile_name: str
    :param region_name: If AWSCLI isn't setup, the user can pass region to let boto3 pick up credentials from the system.
    :param region_name: str
    :type profile_name: str, optional
    :param kms_key_id: Customer's AWS KMS key (cryptographic key)
    :type kms_key_id: str, optional
    """

    def __init__(
        self,
        profile_name: str = None,
        region_name: str = None,
        kms_key_id: str = "",
    ):
        self.profile_name = profile_name
        self.region_name = region_name
        self.kms_key_id = kms_key_id

        if self.profile_name is not None:
            self.session = boto3.session.Session(profile_name=self.profile_name)
        elif self.region_name is not None:
            self.session = boto3.session.Session(region_name=self.region_name)
        else:
            raise InputError(
                "Unable to initiate Textractor. Either profile_name or region requires an input parameter."
            )
        self.textract_client = self.session.client("textract")
        self.s3_client = self.session.client("s3")

    def _get_document_images_from_path(self, filepath: str) -> List[Image.Image]:
        """
        Converts the every page in the document to an image. It supports pdfs and image formats that can be opened by
        PIL package. Documents can be stored in the local computer or on an S3 Bucket.

        :param filepath: filepath to the document stored locally or on an S3 bucket.
        :type filepath: str, required
        :return: Returns a list of PIL Images, one for each page of the document
        :rtype: List[Image]
        """
        images = []
        if "s3://" in filepath:
            edit_filepath = filepath.replace("s3://", "")
            bucket = edit_filepath.split("/")[0]
            key = edit_filepath[edit_filepath.index("/") + 1 :]

            s3_client = (
                boto3.session.Session(profile_name=self.profile_name).client("s3")
                if self.profile_name is not None
                else boto3.session.Session(region_name=self.region_name).client("s3")
            )
            file_obj = s3_client.get_object(Bucket=bucket, Key=key).get("Body").read()
            if filepath.endswith(".pdf"):
                if IS_PDF2IMAGE_INSTALLED:
                    images = convert_from_bytes(bytearray(file_obj))
                else:
                    raise MissingDependencyException("pdf2image is not installed. If you do not plan on using visualizations you can skip image generation using save_image=False in your function call.")
            else:
                images = [Image.open(io.BytesIO(bytearray(file_obj)))]

        else:
            if filepath.endswith(".pdf"):
                if IS_PDF2IMAGE_INSTALLED:
                    images = convert_from_path(filepath)
                else:
                    raise MissingDependencyException("pdf2image is not installed. If you do not plan on using visualizations you can skip image generation using save_image=False in your function call.")
            else:
                images = [Image.open(open(filepath, "rb"))]

        if not images:
            raise UnhandledCaseException(f"Could not get any images from {filepath}")

        return images

    def detect_document_text(
        self, file_source, s3_output_path: str = "", save_image: bool = True
    ) -> Document:
        """
        Make a call to the SYNC DetectDocumentText API, implicitly parses the response and produces a :class:`Document` object.
        This function is ideal for single page PDFs or single images.

        :param file_source: Path to a file stored locally, on an S3 bucket or PIL Image
        :type file_source: str or PIL.Image, required
        :param s3_output_path: S3 path to store the output.
        :type s3_output_path: str, optional
        :param save_image: Flag to indicate if document images are to be stored within the Document object. This is optional
                            and necessary only if the customer wants to visualize bounding boxes for their document entities.
        :type save_image: bool

        :return: Returns a Document object containing all the entities, relationships and metadata extracted by the Textract
                 DetectDocumentText API stored within it.
        :rtype: Document
        """

        if isinstance(file_source, list) and len(file_source) > 1:
            raise IncorrectMethodException(
                "List contains more than 1 image. Call start_document_text_detection instead."
            )

        elif isinstance(file_source, str):
            logging.debug("Filepath given.")
            images = self._get_document_images_from_path(file_source)
            if len(images) > 1:
                raise IncorrectMethodException(
                    "Input contains more than 1 page. Call start_document_text_detection instead."
                )
            file_source = _image_to_byte_array(images[0])

        elif isinstance(file_source, Image.Image):
            logging.debug("PIL Image given.")
            images = [file_source]
            file_source = _image_to_byte_array(file_source)

        elif isinstance(file_source, list) and isinstance(file_source[0], Image.Image):
            logging.debug("List of PIL Image given.")
            images = deepcopy(file_source)
            file_source = _image_to_byte_array(images[0])

        else:
            images = []
            raise InputError("Input file_source format not supported.")

        if not s3_output_path:
            output_config = None
        else:
            bucket, prefix = s3_path_to_bucket_and_prefix(s3_output_path)
            output_config = OutputConfig(s3_bucket=bucket, s3_prefix=prefix)

        try:
            response = call_textract(
                input_document=file_source,
                features=[],
                queries_config=None,  # not supported yet
                output_config=output_config,
                kms_key_id=self.kms_key_id,
                job_tag="",
                notification_channel=None,  # not supported yet
                client_request_token="",
                return_job_id=False,
                force_async_api=False,
                call_mode=Textract_Call_Mode.FORCE_SYNC,
                boto3_textract_client=self.textract_client,
                job_done_polling_interval=0,
            )
        except Exception as exception:
            if exception.__class__.__name__ == "InvalidS3ObjectException":
                raise RegionMismatchError(
                    "Region passed in the profile_name and S3 bucket do not match. Ensure the regions are the same."
                )
            raise exception

        document = response_parser.parse(response)
        document.response = response
        if save_image:
            for page in document.pages:
                page.image = images[document.pages.index(page)]
        return document

    def start_document_text_detection(
        self,
        file_source: Union[str, bytes, Image.Image],
        s3_output_path: str = "",
        s3_upload_path: str = "",
        client_request_token: str = "",
        job_tag: str = "",
        save_image: bool = True,
    ):
        """
        Make a call to the ASYNC StartDocumentTextDetection API.

        :param file_source: File bytes, path to a file stored locally or in an S3 bucket
        :type file_source: Union[str, bytes, Image.Image], required
        :param s3_output_path: Prefix to store the output on the S3 bucket (passed as param to Textractor).
        :type s3_output_path: str
        :param s3_upload_path: If given, will automatically upload the document to the given S3 prefix before calling Textract. Files are uploaded
                                    under a uuid. If not given the data is expected to be already in s3
        :type s3_upload_path: str, optional
        :param client_request_token: The idempotent token that's used to identify the start request. If you use the same. token
                                    with multiple StartDocumentTextDetection requests, the same. JobId is returned. Use ClientRequestToken
                                    to prevent the same. job from being accidentally started more than once.
        :type client_request_token: str, optional
        :param job_tag: An identifier that you specify that's included in the completion notification published to the Amazon SNS topic.
        :type job_tag: str, optional

        :return: Returns a job id which can be used to fetch the results
        :rtype: str
        """

        original_file_source = file_source

        if not (
            isinstance(file_source, str)
            or isinstance(file_source, bytes)
            or isinstance(file_source, Image.Image)
        ):
            raise InputError(
                f"file_source needs to be of type str, bytes or PIL Image, not {type(file_source)}"
            )

        # If the file is not already in S3
        if not file_source.startswith("s3://"):
            # Check if the user has given us a bucket to upload to
            if not s3_upload_path:
                raise InputError(
                    f"For files not in S3, an S3 upload path must be provided"
                )

            s3_file_path = os.path.join(s3_upload_path, str(uuid.uuid4()))
            upload_to_s3(self.s3_client, s3_file_path, file_source)
            file_source = s3_file_path

        output_config = None
        if s3_output_path:
            s3_bucket, s3_prefix = s3_path_to_bucket_and_prefix(s3_output_path)
            output_config = OutputConfig(s3_bucket=s3_bucket, s3_prefix=s3_prefix)

        try:
            response = call_textract(
                input_document=file_source,
                features=[],
                queries_config=None,  # not supported yet
                output_config=output_config,
                kms_key_id=self.kms_key_id,
                job_tag=job_tag,
                notification_channel=None,  # not supported yet
                client_request_token=client_request_token,
                return_job_id=True,
                force_async_api=True,
                call_mode=Textract_Call_Mode.FORCE_ASYNC,
                boto3_textract_client=self.textract_client,
                job_done_polling_interval=1,
            )
        except Exception as exception:
            if exception.__class__.__name__ == "InvalidS3ObjectException":
                raise RegionMismatchError(
                    "Region passed in the profile_name and S3 bucket do not match. Ensure the regions are the same."
                )
            raise exception

        images = None
        if save_image:
            if isinstance(original_file_source, Image.Image):
                images = [original_file_source]
            elif (
                isinstance(original_file_source, list)
                and len(original_file_source)
                and isinstance(original_file_source[0], Image.Image)
            ):
                images = original_file_source
            else:
                images = self._get_document_images_from_path(original_file_source)

        return LazyDocument(
            response["JobId"],
            TextractAPI.DETECT_TEXT,
            textract_client=self.textract_client,
            images=images,
        )

    def analyze_document(
        self,
        file_source,
        features,
        queries: Union[QueriesConfig, List[Query], List[str]] = None,
        s3_output_path: str = "",
        save_image: bool = True,
    ) -> Document:
        """
        Make a call to the SYNC AnalyzeDocument API, implicitly parses the response and produces a :class:`Document` object.
        This function is ideal for single page PDFs or single images.

        :param file_source: Path to a file stored locally, on an S3 bucket or PIL Image
        :type file_source: str or PIL.Image, required
        :param features: List of TextractFeatures to be extracted from the Document by the TextractAPI
        :type features: list, required
        :param queries: Queries to run on the document
        :type features: Union[QueriesConfig, List[Query], List[str]]
        :param s3_output_path: Prefix to store the output on the S3 bucket (passed as param to Textractor).
        :type s3_output_path: str, optional
        :param save_image: Flag to indicate if document images are to be stored within the Document object. This is optional
                            and necessary only if the customer wants to visualize bounding boxes for their document entities.
        :type save_image: bool

        :return: Returns a Document object containing all the entities, relationships and metadata extracted by the Textract
                 AnalyzeDocument API stored within it.
        :rtype: Document
        """
        if isinstance(file_source, list) and len(file_source) > 1:
            raise IncorrectMethodException(
                "List contains more than 1 image. Call start_document_analysis() instead."
            )

        elif isinstance(file_source, str):
            logging.debug("Filepath given.")
            images = self._get_document_images_from_path(file_source)
            if len(images) > 1:
                raise IncorrectMethodException(
                    "Input contains more than 1 page. Call start_document_analysis() instead."
                )
            file_source = _image_to_byte_array(images[0])

        elif isinstance(file_source, Image.Image):
            logging.debug("PIL Image given.")
            images = [file_source]
            file_source = _image_to_byte_array(file_source)

        elif isinstance(file_source, list) and isinstance(file_source[0], Image.Image):
            logging.debug("List of PIL Image given.")
            images = deepcopy(file_source)
            file_source = _image_to_byte_array(images[0])

        else:
            images = []
            raise InputError("Input file_source format not supported.")

        if not s3_output_path:
            output_config = None
        else:
            bucket, prefix = s3_path_to_bucket_and_prefix(s3_output_path)
            output_config = OutputConfig(s3_bucket=bucket, s3_prefix=prefix)

        if not isinstance(features, list):
            features = [features]

        if queries and TextractFeatures.QUERIES not in features:
            raise InputError(
                "Queries were given as a parameter but QUERIES is not enabled in the feature set"
            )

        if queries and not isinstance(queries, QueriesConfig):
            if not isinstance(queries, List):
                raise InputError(
                    f"Queries must be of type QueriesConfig, List[Query] or List[str], not {type(queries)}"
                )
            if isinstance(queries[0], Query):
                queries_config = QueriesConfig(queries)
                queries = queries_config
            elif isinstance(queries[0], str):
                queries_config = QueriesConfig([Query(query) for query in queries])
                queries = queries_config
            else:
                raise InputError(
                    f"Queries must be of type QueriesConfig, List[Query] or List[str], not {type(queries)}"
                )

        try:
            response = call_textract(
                input_document=file_source,
                features=features,
                queries_config=queries,  # not supported yet
                output_config=output_config,
                kms_key_id=self.kms_key_id,
                job_tag="",
                notification_channel=None,  # not supported yet
                client_request_token="",
                return_job_id=False,
                force_async_api=False,
                call_mode=Textract_Call_Mode.FORCE_SYNC,
                boto3_textract_client=self.textract_client,
                job_done_polling_interval=0,
            )
        except Exception as exception:
            if exception.__class__.__name__ == "InvalidS3ObjectException":
                raise RegionMismatchError(
                    "Region passed in the profile_name and S3 bucket do not match. Ensure the regions are the same."
                )
            raise exception

        document = response_parser.parse(response)
        document.response = response
        if save_image:
            for page in document.pages:
                page.image = images[document.pages.index(page)]
        return document

    # FIXME: This should not be synchronous
    def start_document_analysis(
        self,
        file_source: Union[str, bytes, Image.Image],
        features,
        s3_output_path: str = "",
        s3_upload_path: str = "",
        queries: Union[QueriesConfig, List[Query], List[str]] = None,
        client_request_token: str = "",
        job_tag: str = "",
        save_image: bool = True,
    ) -> LazyDocument:
        """
        Make a call to the ASYNC StartDocumentAnalysis API, implicitly parses the response and produces a :class:`Document` object.
        This function is ideal for multipage PDFs or list of images.

        :param file_source: Path to a file stored locally, on an S3 bucket or list of PIL Images
        :type file_source: str or List[PIL.Image], required
        :param features: List of TextractFeatures to be extracted from the Document by the TextractAPI
        :type features: list, required
        :param s3_output_path: Path to store the output on the S3 bucket (passed as param to Textractor).
        :type s3_output_path: str
        :param s3_upload_path: If given, will automatically upload the document to the given S3 prefix before calling Textract. Files are uploaded
                               under a uuid. If not given the data is expected to be already in s3
        :type s3_upload_path: str, optional
        :param client_request_token: The idempotent token that's used to identify the start request. If you use the same. token
                                    with multiple StartDocumentTextDetection requests, the same. JobId is returned. Use ClientRequestToken
                                    to prevent the same. job from being accidentally started more than once.
        :type client_request_token: str, optional
        :param job_tag: An identifier that you specify that's included in the completion notification published to the Amazon SNS topic.
        :type job_tag: str, optional
        :param save_image: Flag to indicate if document images are to be stored within the Document object. This is optional
                            and necessary only if the customer wants to visualize bounding boxes for their document entities.
        :type save_image: bool

        :return: Returns a Document object containing all the entities, relationships and metadata extracted by the Textract
                 StartDocumentAnalysis API stored within it.
        :rtype: Document
        """

        original_file_source = file_source

        if not (
            isinstance(file_source, str)
            or isinstance(file_source, bytes)
            or isinstance(file_source, Image.Image)
        ):
            raise InputError(
                f"file_source needs to be of type str, bytes or PIL Image, not {type(file_source)}"
            )

        # If the file is not already in S3
        if not isinstance(file_source, str) or not file_source.startswith("s3://"):
            # Check if the user has given us a bucket to upload to
            if not s3_upload_path:
                raise InputError(
                    f"For files not in S3, an S3 upload path must be provided"
                )

            s3_file_path = os.path.join(s3_upload_path, str(uuid.uuid4()))
            upload_to_s3(self.s3_client, s3_file_path, file_source)
            file_source = s3_file_path

        output_config = None
        if s3_output_path:
            s3_bucket, s3_prefix = s3_path_to_bucket_and_prefix(s3_output_path)
            output_config = OutputConfig(s3_bucket=s3_bucket, s3_prefix=s3_prefix)

        if not isinstance(features, list):
            features = [features]

        if queries and TextractFeatures.QUERIES not in features:
            raise InputError(
                "Queries were given as a parameter but QUERIES is not enabled in the feature set"
            )

        if queries and not isinstance(queries, QueriesConfig):
            if not isinstance(queries, List):
                raise InputError(
                    f"Queries must be of type QueriesConfig, List[Query] or List[str], not {type(queries)}"
                )
            if isinstance(queries[0], Query):
                queries_config = QueriesConfig(queries)
                queries = queries_config
            elif isinstance(queries[0], str):
                queries_config = QueriesConfig([Query(query) for query in queries])
                queries = queries_config
            else:
                raise InputError(
                    f"Queries must be of type QueriesConfig, List[Query] or List[str], not {type(queries)}"
                )

        try:
            response = call_textract(
                input_document=file_source,
                features=features,
                queries_config=queries,  # not supported yet
                output_config=output_config,
                kms_key_id=self.kms_key_id,
                job_tag=job_tag,
                notification_channel=None,  # not supported yet
                client_request_token=client_request_token,
                return_job_id=True,
                force_async_api=True,
                call_mode=Textract_Call_Mode.FORCE_ASYNC,
                boto3_textract_client=self.textract_client,
                job_done_polling_interval=1,
            )
        except Exception as exception:
            if exception.__class__.__name__ == "InvalidS3ObjectException":
                raise RegionMismatchError(
                    "Region passed in the profile_name and S3 bucket do not match. Ensure the regions are the same."
                )
            raise exception

        images = None
        if save_image:
            if isinstance(original_file_source, Image.Image):
                images = [original_file_source]
            elif (
                isinstance(original_file_source, list)
                and len(original_file_source)
                and isinstance(original_file_source[0], Image.Image)
            ):
                images = original_file_source
            else:
                images = self._get_document_images_from_path(original_file_source)

        return LazyDocument(
            response["JobId"],
            TextractAPI.ANALYZE,
            textract_client=self.textract_client,
            images=images,
        )

    def analyze_id(
        self,
        file_source: Union[str, List[Image.Image], List[str]],
        save_image: bool = True,
    ) -> Document:
        """AnalyzeID parses identity documents such as passports and driver's license and
        returns the result as a dictionary of standardized fields. See https://docs.aws.amazon.com/textract/latest/dg/identitydocumentfields.html
        for a complete list.

        :param file_source: Path to a file stored locally, on an S3 bucket or list of PIL Images
        :type file_source: Union[str, List[Image.Image], List[str]]
        :param save_image: Saves the images in the returned Document object for visualizing the results, defaults to False
        :type save_image: bool, optional
        :raises InputError: Raised when the file_source could not be parsed
        :raises RegionMismatchError: Raised when the S3 object passed as file source is in a region that does not match the one used to create the Textractor object.
        :raises exception: Raised when the Textract call fails
        :return: Document
        :rtype: Document
        """
        if isinstance(file_source, str):
            logging.debug("Filepath given.")
            images = self._get_document_images_from_path(file_source)
        elif isinstance(file_source, Image.Image):
            logging.debug("PIL Image given.")
            images = [file_source]
        elif isinstance(file_source, list) and isinstance(file_source[0], Image.Image):
            logging.debug("List of PIL Image given.")
            # FIXME: Is this needed?
            images = deepcopy(file_source)
        else:
            images = []
            raise InputError("Input file_source format not supported.")

        images_bytes = [_image_to_byte_array(image) for image in images]

        try:
            response = call_textract_analyzeid(
                document_pages=images_bytes,
                boto3_textract_client=self.textract_client,
            )
        except Exception as exception:
            if exception.__class__.__name__ == "InvalidS3ObjectException":
                raise RegionMismatchError(
                    "Region passed in the profile_name and S3 bucket do not match. Ensure the regions are the same."
                )
            raise exception

        document = response_parser.parse(response)
        document.response = response
        if save_image:
            for page in document.pages:
                page.image = images[document.pages.index(page)]
        return document

    def analyze_expense(
        self,
        file_source: Union[str, List[Image.Image], List[str]],
        s3_output_path: str = "",
        save_image: bool = True,
    ):
        """Make a call to the SYNC AnalyzeExpense API, implicitly parses the response and produces a :class:`Document` object.
        This function is ideal for multipage PDFs or list of images.

        :param file_source: Path to a file stored locally, on an S3 bucket or PIL Image
        :type file_source: Union[str, List[Image.Image], List[str]]
        :param s3_output_path: S3 output path. When used the job output is save to the given S3 path, defaults to ""
        :type s3_output_path: str, optional
        :param save_image: Whether to keep the file source as PIL Images inside the returned Document object, defaults to False
        :type save_image: bool, optional
        :raises IncorrectMethodException: Raised when the file source type is incompatible with the Textract API being called
        :raises InputError: Raised when the file source type is invalid
        :raises RegionMismatchError: Raised when the file source region is different the API region.
        :raises exception: Raised if the Textract API call fails
        :return: Document
        :rtype: Document
        """
        if isinstance(file_source, list) and len(file_source) > 1:
            raise IncorrectMethodException(
                "List contains more than 1 image. Call start_expense_analysis instead."
            )

        elif isinstance(file_source, str):
            logging.debug("Filepath given.")
            images = self._get_document_images_from_path(file_source)
            if len(images) > 1:
                raise IncorrectMethodException(
                    "Input contains more than 1 page. Call start_expense_analysis instead."
                )
            file_source = _image_to_byte_array(images[0])

        elif isinstance(file_source, Image.Image):
            logging.debug("PIL Image given.")
            images = [file_source.copy()]
            file_source = _image_to_byte_array(file_source)

        elif isinstance(file_source, list) and isinstance(file_source[0], Image.Image):
            logging.debug("List of PIL Image given.")
            images = deepcopy(file_source)
            file_source = _image_to_byte_array(images[0])

        else:
            images = []
            raise InputError("Input file_source format not supported.")

        if not s3_output_path:
            output_config = None
        else:
            bucket, prefix = s3_path_to_bucket_and_prefix(s3_output_path)
            output_config = OutputConfig(s3_bucket=bucket, s3_prefix=prefix)

        try:
            response = call_textract_expense(
                input_document=file_source,
                output_config=output_config,
                kms_key_id=self.kms_key_id,
                job_tag="",
                notification_channel=None,  # not supported yet
                client_request_token="",
                return_job_id=False,
                force_async_api=False,
                boto3_textract_client=self.textract_client,
                job_done_polling_interval=0,
            )
        except Exception as exception:
            if exception.__class__.__name__ == "InvalidS3ObjectException":
                raise RegionMismatchError(
                    "Region passed in the profile_name and S3 bucket do not match. Ensure the regions are the same."
                )
            raise exception

        document = response_parser.parse(response)
        document.response = response
        if save_image:
            for page in document.pages:
                page.image = images[document.pages.index(page)]
        return document

    def start_expense_analysis(
        self,
        file_source: Union[str, bytes, Image.Image],
        s3_output_path: str = "",
        s3_upload_path: str = "",
        client_request_token: str = "",
        job_tag: str = "",
        save_image: bool = True,
    ) -> LazyDocument:
        """Make a call to the ASYNC StartExpenseAnalysis API, implicitly parses the response and produces a :class:`Document` object.
        This function is ideal for multipage PDFs or list of images.

        :param file_source: Path to a file stored locally, on an S3 bucket or list of PIL Images
        :type file_source: Union[str, bytes, Image.Image]
        :param s3_output_path: Path to store the output on the S3 bucket (passed as param to Textractor).
        :type s3_output_path: str
        :param s3_upload_path: If given, will automatically upload the document to the given S3 prefix before calling Textract. Files are uploaded
                               under a uuid. If not given the data is expected to be already in s3
        :type s3_upload_path: str, optional
        :param client_request_token: The idempotent token that's used to identify the start request. If you use the same. token
                                    with multiple StartDocumentTextDetection requests, the same. JobId is returned. Use ClientRequestToken
                                    to prevent the same. job from being accidentally started more than once.
        :type client_request_token: str, optional
        :param job_tag: An identifier that you specify that's included in the completion notification published to the Amazon SNS topic.
        :type job_tag: str, optional
        :param save_image: Flag to indicate if document images are to be stored within the Document object. This is optional
                            and necessary only if the customer wants to visualize bounding boxes for their document entities.
        :type save_image: bool
        :raises InputError: Raised when the file source type is invalid
        :raises RegionMismatchError: Raised when the file source region is different the API region.
        :raises exception: Raised if the Textract API call fails
        :return: Lazy-loaded Document object
        :rtype: LazyDocument
        """

        original_file_source = file_source
        
        if not (
            isinstance(file_source, str)
            or isinstance(file_source, bytes)
            or isinstance(file_source, Image.Image)
        ):
            raise InputError(
                f"file_source needs to be of type str, bytes or PIL Image, not {type(file_source)}"
            )

        # If the file is not already in S3
        if not file_source.startswith("s3://"):
            # Check if the user has given us a bucket to upload to
            if not s3_upload_path:
                raise InputError(
                    f"For files not in S3, an S3 upload path must be provided"
                )

            s3_file_path = os.path.join(s3_upload_path, str(uuid.uuid4()))
            upload_to_s3(self.s3_client, s3_file_path, file_source)
            file_source = s3_file_path

        output_config = None
        if s3_output_path:
            s3_bucket, s3_prefix = s3_path_to_bucket_and_prefix(s3_output_path)
            output_config = OutputConfig(s3_bucket=s3_bucket, s3_prefix=s3_prefix)

        try:
            response = call_textract_expense(
                input_document=file_source,
                output_config=output_config,
                kms_key_id=self.kms_key_id,
                job_tag=job_tag,
                notification_channel=None,  # not supported yet
                client_request_token=client_request_token,
                return_job_id=True,
                force_async_api=True,
                boto3_textract_client=self.textract_client,
                job_done_polling_interval=1,
            )
        except Exception as exception:
            if exception.__class__.__name__ == "InvalidS3ObjectException":
                raise RegionMismatchError(
                    "Region passed in the profile_name and S3 bucket do not match. Ensure the regions are the same."
                )
            raise exception

        images = None
        if save_image:
            if isinstance(original_file_source, Image.Image):
                images = [original_file_source]
            elif (
                isinstance(original_file_source, list)
                and len(original_file_source)
                and isinstance(original_file_source[0], Image.Image)
            ):
                images = original_file_source
            else:
                images = self._get_document_images_from_path(original_file_source)

        return LazyDocument(
            response["JobId"],
            TextractAPI.EXPENSE,
            textract_client=self.textract_client,
            images=images,
        )

    def get_result(self, job_id: str, api: Union[TextractAPI, Textract_API]):
        """ """

        response = get_full_json(
            job_id,
            TextractAPI.TextractAPI_to_Textract_API(api)
            if isinstance(api, TextractAPI)
            else api,
            boto3_textract_client=self.textract_client,
            job_done_polling_interval=1,
        )

        document = response_parser.parse(response)
        document.response = response

        return document


def _image_to_byte_array(image: Image) -> bytes:
    """
    Function to convert PIL.Image to bytearray for processing Document using Textract service.
    :param image: Image to be converted to bytearray
    :type image: PIL.Image, required
    :return: Returns a bytearray of the input image
    :rtype: bytes
    """
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr
