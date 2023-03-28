class ServiceException(Exception):
    def __init__(self, status_code=500, **kwargs):
        self.status_code = status_code
        self.kwargs = kwargs

from .error_code import ErrorCode
