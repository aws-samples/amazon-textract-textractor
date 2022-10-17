"""
    Define exceptions specific to textractor.
"""


class RegionMismatchError(Exception):
    """Raised when region on the profile_name does not match the region of the S3 bucket being accessed."""

    pass


class NoImageException(Exception):
    """Raised when visualize() method is called without saving image during Textract API call."""

    pass


class InputError(Exception):
    """Raised when function inputs are incorrect."""


class EntityListCreationError(Exception):
    """Raised when EntityList is created without passing any object or list of objects."""

    pass


class InvalidProfileNameError(Exception):
    """Raised when profile_name passed to Textractor is invalid."""

    pass


class S3FilePathMissing(Exception):
    """Raised when s3 file path is missing."""

    pass


class MissingDependencyException(Exception):
    """Raised when a dependency is missing for a specific code path"""

    pass


class IncorrectMethodException(Exception):
    """Raised when wrong endpoint is called."""

    pass


class UnhandledCaseException(Exception):
    """Raised when no statement matched the condition"""

    pass
