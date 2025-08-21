from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from uuid import UUID
from fastapi import status
from fastapi.responses import JSONResponse
from typing import Any, Optional, Dict, List
import enum
import json


# Custom JSON encoder that handles enums and other complex types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, enum.Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        elif hasattr(obj, "model_dump"):  # Pydantic v2 models
            return obj.model_dump()
        elif hasattr(obj, "dict"):  # Pydantic v1 models
            return obj.dict()
        elif hasattr(obj, "__dict__"):  # ORM objects
            # Convert ORM object to dict, then recursively serialize
            return {k: self.default(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                    for k, v in vars(obj).items() if not k.startswith('_')}
        return super().default(obj)


def serialize_value(value: Any) -> Any:
    """
    Recursively serialize values for JSON response compatibility.
    Handles complex types like enums, datetimes, UUIDs, and Pydantic models.
    """
    if isinstance(value, enum.Enum):
        return value.value
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, MappingProxyType):
        return {k: serialize_value(v) for k, v in value.items()}
    elif isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [serialize_value(v) for v in value]
    elif hasattr(value, "model_dump"):  # Pydantic v2 models
        return serialize_value(value.model_dump())
    elif hasattr(value, "dict"):  # Pydantic v1 models
        return serialize_value(value.dict())
    elif hasattr(value, "__dict__"):  # ORM objects
        # Filter out private attributes and serialize remaining
        obj_dict = {k: v for k, v in vars(value).items() if not k.startswith('_')}
        return serialize_value(obj_dict)
    return value


def create_json_response(content: Any, status_code: int = 200) -> JSONResponse:
    """
    Create a JSONResponse with proper serialization handling.
    """
    # Serialize the content using our custom function
    serialized_content = serialize_value(content)

    # Use custom JSON encoder for additional safety
    json_content = json.loads(json.dumps(serialized_content, cls=CustomJSONEncoder))

    return JSONResponse(status_code=status_code, content=json_content)


def set_token_cookie(response: JSONResponse, token: str, token_type: str, expires_in: int) -> JSONResponse:
    """
    Helper function to set a token as an HTTP-only cookie.
    """
    cookie_key = "access_token" if token_type.lower() == "bearer" else "refresh_token"
    expiry_time = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(seconds=expires_in)

    response.set_cookie(
        key=cookie_key,
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=expires_in,
        expires=expiry_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
    )

    print(f"Setting {cookie_key} cookie with value: {token[:10]}... (expires in {expires_in} seconds)")
    return response


class Success:
    """
    Standardized success responses for the API with proper JSON serialization.
    """

    @staticmethod
    def json_response(
            detail: str,
            status_code: int = status.HTTP_200_OK,
            **kwargs
    ) -> JSONResponse:
        """Base method for all success responses with proper serialization"""
        # Serialize all data before creating response
        data = serialize_value(kwargs) if kwargs else None
        content = {
            "status_code": status_code,
            "detail": detail,
            "data": data
        }
        return create_json_response(content, status_code)

    # ==================== GENERIC RESPONSES ====================

    @staticmethod
    def ok(detail: str = "Successfully completed", **kwargs) -> JSONResponse:
        """Standard 200 OK response"""
        return Success.json_response(detail, status.HTTP_200_OK, **kwargs)

    @staticmethod
    def created(detail: str = "Resource created successfully", **kwargs: Any) -> JSONResponse:
        """Standard 201 Created response with proper serialization"""
        # Serialize all kwargs properly
        serialized_data = serialize_value(kwargs)
        content = {"detail": detail, **serialized_data}
        return create_json_response(content, status.HTTP_201_CREATED)

    @staticmethod
    def accepted(detail: str = "Request accepted successfully", **kwargs) -> JSONResponse:
        """Standard 202 Accepted response"""
        return Success.json_response(detail, status.HTTP_202_ACCEPTED, **kwargs)

    @staticmethod
    def no_content() -> JSONResponse:
        """Standard 204 No Content response"""
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    # ==================== USER MANAGEMENT RESPONSES ====================

    @staticmethod
    def account_created(user: Any) -> JSONResponse:
        """Response for successful user account creation"""
        return Success.created(
            "Account created. Verify your email with a six-digit code.",
            user=user
        )

    @staticmethod
    def login_success(
            access_token: str,
            refresh_token: str,
            user: Any,
    ) -> JSONResponse:
        """
        Successful login response with tokens set as HTTP-only cookies.

        Args:
            access_token: JWT access token string
            refresh_token: JWT refresh token string
            user: User object or dict
            access_token_expires: timedelta for access token expiration
            refresh_token_expires: timedelta for refresh token expiration
        """


        # Create base response with all token info
        response = Success.ok(
            "Login successful",
            access_token=access_token,
            refresh_token=refresh_token,
            user=user,
        )

        # Set cookies with dynamic expiration times
        if access_token:
            response = set_token_cookie(
                response=response,
                token=access_token,
                token_type="bearer",
                expires_in=30 * 60
            )

        if refresh_token:
            response = set_token_cookie(
                response=response,
                token=refresh_token,
                token_type="refresh",
                expires_in=7 * 86400
            )

        # Set security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Cache-Control": "no-store"
        })

        return response


    @staticmethod
    def logout_success() -> JSONResponse:
        """Response for successful logout"""
        response = Success.ok("Logged out successfully")
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        return response

    @staticmethod
    def verification_code_sent(verification_code: str) -> JSONResponse:
        """Response for successful verification code sending"""
        return Success.ok(
            "Verification code sent successfully",
            verification_code=verification_code,
            expires_in="10 minutes"
        )

    @staticmethod
    def email_verified() -> JSONResponse:
        """Response for successful email verification"""
        return Success.ok("Email verified successfully")

    @staticmethod
    def password_reset_requested() -> JSONResponse:
        """Response for successful password reset request"""
        return Success.ok("Password reset instructions sent to your email")

    @staticmethod
    def password_changed() -> JSONResponse:
        """Response for successful password change"""
        return Success.ok("Password changed successfully")

    # ==================== ADMIN RESPONSES ====================

    @staticmethod
    def admin_created(admin: Any) -> JSONResponse:
        """Response for successful admin account creation"""
        return Success.created("Admin account created successfully", admin=admin)

    @staticmethod
    def admin_login(
            access_token: Optional[str] = None,
            admin: Optional[Any] = None
    ) -> JSONResponse:
        """Response for successful admin login"""
        response = Success.ok("Admin login successful", access_token=access_token, admin=admin)
        if access_token:
            response = set_token_cookie(
                response=response,
                token=access_token,
                token_type="bearer",
                expires_in=30 * 60  # Replace with your settings
            )
        return response

    @staticmethod
    def user_updated(user: Any) -> JSONResponse:
        """Response for successful user update by admin"""
        return Success.ok("User updated successfully", user=user)

    @staticmethod
    def user_deleted() -> JSONResponse:
        """Response for successful user deletion by admin"""
        return Success.ok("User deleted successfully")

    # ==================== PAYMENT RESPONSES ====================

    @staticmethod
    def payment_success(
            transaction_id: str,
            amount: float,
            currency: str = "USD",
            **additional_details
    ) -> JSONResponse:
        """Response for successful payment processing"""
        return Success.ok(
            "Payment processed successfully",
            transaction_id=transaction_id,
            amount=amount,
            currency=currency,
            **additional_details
        )

    @staticmethod
    def subscription_created(
            subscription_id: str,
            plan: str,
            start_date: datetime,
            end_date: datetime
    ) -> JSONResponse:
        """Response for successful subscription creation"""
        return Success.created(
            "Subscription created successfully",
            subscription_id=subscription_id,
            plan=plan,
            start_date=start_date,
            end_date=end_date
        )

    @staticmethod
    def subscription_updated(subscription: Any) -> JSONResponse:
        """Response for successful subscription update"""
        return Success.ok("Subscription updated successfully", subscription=subscription)

    @staticmethod
    def subscription_cancelled() -> JSONResponse:
        """Response for successful subscription cancellation"""
        return Success.ok("Subscription cancelled successfully")

    # ==================== TOKEN RESPONSES ====================

    @staticmethod
    def token_refreshed(
            access_token: str,
            expires_in: int = 30 * 60  # Replace with your settings
    ) -> JSONResponse:
        """Response for successful token refresh"""
        response = Success.ok(
            "Token refreshed successfully",
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in
        )
        response = set_token_cookie(
            response=response,
            token=access_token,
            token_type="bearer",
            expires_in=expires_in
        )
        return response

    @staticmethod
    def token_generated(
            access_token: str,
            token_type: str = "bearer",
            expires_in: int = 3600,
            refresh_token: Optional[str] = None
    ) -> JSONResponse:
        """Response for successful token generation"""
        response = Success.ok(
            "Token generated successfully",
            access_token=access_token,
            token_type=token_type,
            expires_in=expires_in
        )

        response = set_token_cookie(
            response=response,
            token=access_token,
            token_type=token_type,
            expires_in=expires_in
        )

        if refresh_token:
            response = set_token_cookie(
                response=response,
                token=refresh_token,
                token_type="refresh",
                expires_in=7 * 86400  # Replace with your settings
            )

        return response

    # ==================== CONTENT RESPONSES ====================

    @staticmethod
    def content_created(content: Any) -> JSONResponse:
        """Response for successful content creation"""
        return Success.created("Content created successfully", content=content)

    @staticmethod
    def content_updated(content: Any) -> JSONResponse:
        """Response for successful content update"""
        return Success.ok("Content updated successfully", content=content)

    @staticmethod
    def content_deleted() -> JSONResponse:
        """Response for successful content deletion"""
        return Success.ok("Content deleted successfully")

    @staticmethod
    def file_uploaded(file_url: str, file_name: str, file_size: int) -> JSONResponse:
        """Response for successful file upload"""
        return Success.created(
            "File uploaded successfully",
            file_url=file_url,
            file_name=file_name,
            file_size=file_size
        )

    # ==================== CUSTOM RESPONSES ====================

    @staticmethod
    def custom_success(
            detail: str,
            status_code: int = status.HTTP_200_OK,
            **kwargs
    ) -> JSONResponse:
        """For non-standard success scenarios"""
        return Success.json_response(detail, status_code, **kwargs)

    @staticmethod
    def data_list(
            items: List[Any],
            count: int,
            page: int = 1,
            page_size: int = 10,
            detail: str = "Data retrieved successfully"
    ) -> JSONResponse:
        """Response for paginated data lists"""
        return Success.ok(
            detail=detail,
            items=items,
            count=count,
            page=page,
            page_size=page_size,
            total_pages=(count + page_size - 1) // page_size
        )

