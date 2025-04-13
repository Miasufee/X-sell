from fastapi import status
from pydantic import BaseModel
from typing import Any, Optional, Dict


class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None


class Success:
    @staticmethod
    def response(
        detail: str,
        status_code: int = status.HTTP_200_OK,
        **data
    ) -> Dict[str, Any]:
        return {
            "status_code": status_code,
            "detail": detail,
            "data": data or None
        }

    @staticmethod
    def ok(detail: str = "successfully", **data):
        return Success.response(detail, status.HTTP_200_OK, **data)

    @staticmethod
    def created(detail: str = "Resource created successfully", **data):
        return Success.response(detail, status.HTTP_201_CREATED, **data)

    @staticmethod
    def accepted(detail: str = "Request accepted successfully", **data):
        return Success.response(detail, status.HTTP_202_ACCEPTED, **data)

    @staticmethod
    def updated(detail: str = "Resource updated successfully", **data):
        return Success.response(detail, status.HTTP_200_OK, **data)

    @staticmethod
    def deleted(detail: str = "Resource deleted successfully", **data):
        return Success.response(detail, status.HTTP_200_OK, **data)

    # ✅ User Authentication
    @staticmethod
    def account_created(user: Any):
        return Success.created(
            "Account created successfully. Verify email with a six-digit code.",
            user=user
        )

    @staticmethod
    def login_success(token: Optional[str] = None, user: Optional[Any] = None):
        return Success.ok("Login successful", token=token, user=user)

    @staticmethod
    def password_reset():
        return Success.ok("Password reset successfully")

    # ✅ Admin Authentication
    @staticmethod
    def admin_created(admin: Any):
        return Success.created("Admin account created successfully", admin=admin)

    @staticmethod
    def admin_login(token: Optional[str] = None, admin: Optional[Any] = None):
        return Success.ok("Admin login successful", token=token, admin=admin)

    # ✅ Seller Authentication
    @staticmethod
    def seller_created(seller: Any):
        return Success.created("Seller account created successfully", seller=seller)

    @staticmethod
    def seller_login(token: Optional[str] = None, seller: Optional[Any] = None):
        return Success.ok("Seller login successful", token=token, seller=seller)

    # ✅ Messaging & Notifications
    @staticmethod
    def message_sent():
        return Success.ok("Message sent successfully")

    @staticmethod
    def notification_sent():
        return Success.ok("Notification sent successfully")

    # ✅ Transactions & Payments
    @staticmethod
    def payment_success(transaction_id: Optional[str] = None):
        return Success.ok("Payment processed successfully", transaction_id=transaction_id)

    @staticmethod
    def refund_processed():
        return Success.ok("Refund processed successfully")

    # ✅ Token & Authentication
    @staticmethod
    def token_generated(token: str):
        return Success.ok("Token generated successfully", token=token)

    @staticmethod
    def logout_success():
        return Success.ok("Logout successful")

    @staticmethod
    def verification_code_sent(code):
        return Success.ok(f'here is the six digit otp {code} will expire 10 minutes')