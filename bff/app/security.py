"""JWT decoding and GraphQL authorization helpers."""
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Request, Response
from graphql import GraphQLError

from app import config

ROLES = ("student", "company_supervisor", "academic_supervisor", "coordinator")


@dataclass
class User:
    id: str
    role: str
    token: str


def _user_from_header(header: str | None) -> User | None:
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        claims = jwt.decode(token, config.jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    if claims.get("role") not in ROLES or not claims.get("sub"):
        return None
    return User(id=claims["sub"], role=claims["role"], token=token)


async def get_context(request: Request, response: Response) -> dict[str, Any]:
    """Decode the bearer token once per GraphQL request."""
    return {
        "request": request,
        "response": response,
        "user": _user_from_header(request.headers.get("Authorization")),
    }


def require_user(info: Any) -> User:
    """Set HTTP 401 and raise a GraphQL error when the token is missing/invalid."""
    user = info.context.get("user")
    if user is None:
        info.context["response"].status_code = 401
        raise GraphQLError("Missing or invalid bearer token",
                           extensions={"code": "not_authenticated"})
    return user


def require_role(info: Any, *roles: str) -> User:
    """Set HTTP 403 and raise a GraphQL error when the role is wrong."""
    user = require_user(info)
    if user.role not in roles:
        info.context["response"].status_code = 403
        raise GraphQLError(f"This action needs the role: {', '.join(roles)}",
                           extensions={"code": "forbidden"})
    return user
