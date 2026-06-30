class AppException(Exception):
    """
    Custom exception class for application-level errors.

    Args:
        message (str): The error message.
        status_code (int): The HTTP status code associated with the error.
        data (any): Optional additional data related to the error.
    """

    def __init__(self, message: str, status_code: int = 400, data: any = None):
        self.message = message
        self.status_code = status_code
        self.data = data
