"""JWT check and role-based access. Tokens carry  sub (user id)  and  role."""
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import config
from app.errors import ApiError

ROLES = ("student", "company_supervisor", "academic_supervisor", "coordinator")
bearer = HTTPBearer(auto_error=False)


@dataclass
class User:
    id: str
    role: str
    token: str


def current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> User:
    """401 when there is no valid token."""
    if creds is None:
        raise ApiError(401, "not_authenticated", "Missing bearer token")
    try:
        claims = jwt.decode(creds.credentials, config.jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        raise ApiError(401, "invalid_token", "Invalid or expired token")
    if claims.get("role") not in ROLES or not claims.get("sub"):
        raise ApiError(401, "invalid_token", "Token has no valid subject or role")
    return User(id=claims["sub"], role=claims["role"], token=creds.credentials)


def require_role(*roles: str):
    """403 when the user is logged in but has the wrong role."""
    def check(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles:
            raise ApiError(403, "forbidden", f"This action needs the role: {', '.join(roles)}")
        return user
    return check