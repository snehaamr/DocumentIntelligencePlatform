class DocumentNotFoundError(Exception):
    """
    Raised when a requested document does not exist
    or does not belong to the current user.
    """


class DocumentRetryNotAllowedError(Exception):
    """
    Raised when a document is not currently eligible
    for retry.
    """