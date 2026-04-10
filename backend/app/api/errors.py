from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status


def error_detail(message: str, reason_code: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    detail: dict[str, Any] = {"message": message, "reason_code": reason_code}
    if context:
        detail["context"] = context
    return detail


def http_error(*, status_code: int, message: str, reason_code: str, context: dict[str, Any] | None = None) -> HTTPException:
    return HTTPException(status_code=status_code, detail=error_detail(message, reason_code, context=context))


def bad_request(message: str, *, reason_code: str, context: dict[str, Any] | None = None) -> HTTPException:
    return http_error(status_code=status.HTTP_400_BAD_REQUEST, message=message, reason_code=reason_code, context=context)


def unauthorized(message: str, *, reason_code: str, context: dict[str, Any] | None = None) -> HTTPException:
    return http_error(status_code=status.HTTP_401_UNAUTHORIZED, message=message, reason_code=reason_code, context=context)


def forbidden(message: str, *, reason_code: str, context: dict[str, Any] | None = None) -> HTTPException:
    return http_error(status_code=status.HTTP_403_FORBIDDEN, message=message, reason_code=reason_code, context=context)


def not_found(message: str, *, reason_code: str, context: dict[str, Any] | None = None) -> HTTPException:
    return http_error(status_code=status.HTTP_404_NOT_FOUND, message=message, reason_code=reason_code, context=context)


def conflict(message: str, *, reason_code: str, context: dict[str, Any] | None = None) -> HTTPException:
    return http_error(status_code=status.HTTP_409_CONFLICT, message=message, reason_code=reason_code, context=context)


def unprocessable(message: str, *, reason_code: str, context: dict[str, Any] | None = None) -> HTTPException:
    return http_error(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message=message, reason_code=reason_code, context=context)


def internal_error(message: str, *, reason_code: str, context: dict[str, Any] | None = None) -> HTTPException:
    return http_error(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=message, reason_code=reason_code, context=context)


def service_unavailable(message: str, *, reason_code: str, context: dict[str, Any] | None = None) -> HTTPException:
    return http_error(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, message=message, reason_code=reason_code, context=context)


def not_implemented(detail: str = "Not implemented yet.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)
