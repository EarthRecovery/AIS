from fastapi import Depends, HTTPException, Request, status


def get_request_user_id(request: Request) -> str:
    """Return user_id stored by middleware; raise 401 if missing."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user_id
