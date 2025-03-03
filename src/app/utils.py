import re
from functools import wraps
from http import HTTPStatus
from typing import Optional

from database.models import User

import jwt

from sanic import json

from sqlalchemy import select


async def fetch_user_from_request(request) -> Optional[User]:
    if not request.token:
        return None
    try:
        payload = jwt.decode(
            request.token, request.app.config.SECRET, algorithms=["HS256"]
        )
    except jwt.InvalidTokenError:
        return None
    st = select(User).where(User.email == payload["sub"])
    async with request.app.ctx.session() as session:
        user = await session.scalar(st)
    return user


async def fetch_user_middleware(request):
    request.ctx.user = await fetch_user_from_request(request)


def email_is_valid(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def valid_email_decorator(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            data = request.json
            if "email" in data and not email_is_valid(data["email"]):
                return json(
                    {"error": "invalid email format"}, HTTPStatus.BAD_REQUEST
                )

            response = await f(request, *args, **kwargs)
            return response

        return decorated_function

    return decorator(wrapped)
