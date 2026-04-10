from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.middleware.request_context import reset_correlation_id, set_correlation_id


CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get(CORRELATION_ID_HEADER, "").strip()
        correlation_id = incoming or f"req_{uuid4().hex}"
        token = set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id
        try:
            response = await call_next(request)
        finally:
            reset_correlation_id(token)
        response.headers.setdefault(CORRELATION_ID_HEADER, correlation_id)
        return response
