class ServiceError(Exception):
    def __init__(self, message="An error occurred", code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(ServiceError):
    def __init__(self, message="Validation failed", field=None):
        self.field = field
        super().__init__(message, code='validation_error')


class PermissionDeniedError(ServiceError):
    def __init__(self, message="Permission denied"):
        super().__init__(message, code='permission_denied')


class NotFoundError(ServiceError):
    def __init__(self, message="Resource not found"):
        super().__init__(message, code='not_found')


class DuplicateError(ServiceError):
    def __init__(self, message="Resource already exists"):
        super().__init__(message, code='duplicate')
