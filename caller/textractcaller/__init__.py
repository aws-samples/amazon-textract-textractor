from ._version import __version__
from .t_call import NotificationChannel, OutputConfig, DocumentLocation, Document, get_job_response, get_full_json_from_output_config, get_full_json, call_textract, Textract_Features, call_textract_analyzeid, DocumentPage, QueriesConfig, Query, AdaptersConfig, Adapter, call_textract_expense, Textract_Call_Mode, Textract_API, Textract_Types, call_textract_lending, get_full_json_lending, get_full_json_lending_from_output_config, get_s3_output_config_keys

import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())
