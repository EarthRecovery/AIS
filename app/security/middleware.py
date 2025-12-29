from fastapi import Request
from fastapi.responses import JSONResponse

from app.security.jwt import decode_access_token


async def attach_user_from_token(request: Request, call_next):
    """Extract user from Authorization header and attach user_id to request.state."""
    # Let CORS preflight pass through (no auth header on OPTIONS).
    if request.method == "OPTIONS":
        return await call_next(request)

    # Skip auth endpoints (e.g., /auth/register, /auth/login)
    if request.url.path.startswith("/auth"):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        try:
            request.state.user_id = decode_access_token(token)
        except Exception as exc:
            # Stop early if token is present but invalid/expired.
            return JSONResponse(status_code=401, content={"detail": str(exc)})
    else:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    response = await call_next(request)
    return response
