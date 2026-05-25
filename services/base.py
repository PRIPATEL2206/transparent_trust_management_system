import logging
from functools import wraps
from .exceptions import ServiceError


class BaseService:
    @classmethod
    def get_logger(cls):
        return logging.getLogger(f'services.{cls.__name__}')

    @classmethod
    def log_action(cls, action, user=None, **kwargs):
        logger = cls.get_logger()
        extra = {'user': getattr(user, 'username', 'system'), **kwargs}
        logger.info(f"{action} | {extra}")


def service_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ServiceError:
            raise
        except Exception as e:
            logger = logging.getLogger('services')
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            raise ServiceError(f"An unexpected error occurred: {str(e)}")
    return wrapper
