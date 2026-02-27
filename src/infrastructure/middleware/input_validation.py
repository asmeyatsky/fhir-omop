"""
Input Validation Middleware

Architectural Intent:
- Request body size limits to prevent abuse
- JSON depth limits to prevent stack overflow attacks
- Content-Type validation
"""
from __future__ import annotations

import json

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# 10 MB max body size
MAX_BODY_SIZE = 10 * 1024 * 1024
MAX_JSON_DEPTH = 20

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


def _check_json_depth(obj, depth=0) -> int:
    """Check the nesting depth of a JSON object."""
    if depth > MAX_JSON_DEPTH:
        return depth
    if isinstance(obj, dict):
        if not obj:
            return depth
        return max(_check_json_depth(v, depth + 1) for v in obj.values())
    if isinstance(obj, list):
        if not obj:
            return depth
        return max(_check_json_depth(v, depth + 1) for v in obj)
    return depth


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validates request body size and JSON depth."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body too large. Max size: {MAX_BODY_SIZE} bytes"},
            )

        # For POST/PUT/PATCH with JSON body, validate depth
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    if len(body) > MAX_BODY_SIZE:
                        return JSONResponse(
                            status_code=413,
                            content={"detail": "Request body too large"},
                        )
                    if body:
                        parsed = json.loads(body)
                        depth = _check_json_depth(parsed)
                        if depth > MAX_JSON_DEPTH:
                            return JSONResponse(
                                status_code=400,
                                content={
                                    "detail": f"JSON nesting too deep. Max depth: {MAX_JSON_DEPTH}"
                                },
                            )
                except json.JSONDecodeError:
                    pass  # Let FastAPI handle invalid JSON

        return await call_next(request)
