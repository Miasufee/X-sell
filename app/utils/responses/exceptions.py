from fastapi import HTTPException, status
from typing import Optional, Any


class Exceptions:
    @staticmethod
    def raise_exception(detail: str, status_code: int):
        raise HTTPException(status_code=status_code, detail=detail)

    @staticmethod
    def not_found(model_name: Optional[str] = None, detail: Optional[str] = None, status_code: int = status.HTTP_404_NOT_FOUND):
        message = detail or (f"{model_name} not found" if model_name else "Resource not found")
        Exceptions.raise_exception(message, status_code)

    @staticmethod
    def no_objects_found(detail: str = "No objects found for deletion", status_code: int = status.HTTP_404_NOT_FOUND):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def bad_request(detail: str = "Bad request", status_code: int = status.HTTP_400_BAD_REQUEST):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def unauthorized(detail: str = "Unauthorized", status_code: int = status.HTTP_401_UNAUTHORIZED):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def forbidden(detail: str = "Forbidden", status_code: int = status.HTTP_403_FORBIDDEN):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def conflict(detail: str = "Conflict detected", status_code: int = status.HTTP_409_CONFLICT):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def un_processable_entity(detail: str = "Unprocessable Entity", status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def internal_server_error(detail: str = "Internal Server Error", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def email_exist(detail: str = "Email already exists", status_code: int = status.HTTP_409_CONFLICT):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def email_not_registered(detail: str = "Email is not registered", status_code: int = status.HTTP_404_NOT_FOUND):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def invalid_credentials(detail: str = "Invalid email or password", status_code: int = status.HTTP_401_UNAUTHORIZED):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def not_verify(detail: str = "User is not verified", status_code: int = status.HTTP_403_FORBIDDEN):
        Exceptions.raise_exception(detail, status_code)

    @staticmethod
    def invalid_verification_code(detail: str = "Invalid Verification code", status_code: int = status.HTTP_403_FORBIDDEN):
        Exceptions.raise_exception(detail, status_code)