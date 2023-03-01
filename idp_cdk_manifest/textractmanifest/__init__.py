import logging
from logging import NullHandler
from .manifest import IDPManifest as IDPManifest, IDPManifestSchema as IDPManifestSchema, Query as Query, QuerySchema as QuerySchema, MetaData as MetaData, MetaDataSchema as MetaDataSchema

logging.getLogger('tidpmanifest').addHandler(NullHandler())

__version__ = '0.0.1'
