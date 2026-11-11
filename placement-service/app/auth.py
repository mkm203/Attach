"""Development token endpoint: mints the JWTs both services accept."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter

from app import config
from app.schemas import ErrorResponse, TokenRequest, TokenResponse

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse, responses={422: {"model": ErrorResponse}})
def issue_token(data: TokenRequest):
    """Return a signed HS256 token for the given user id and role.

    This is a development convenience (there is no user store yet); the real
    deployment must replace it with a proper login endpoint.
    """
    now = datetime.now(timezone.utc)
    expires_in = config.jwt_ttl_minutes() * 60
    payload = {
        "sub": data.sub,
        "role": data.role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, config.jwt_secret(), algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in,
            "sub": data.sub, "role": data.role}
