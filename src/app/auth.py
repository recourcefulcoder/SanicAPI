from functools import wraps
from http import HTTPStatus

from app.utils import fetch_user_from_request

import jwt

from sanic import json


def check_token(request):
    if not request.token:
        return False
    try:
        jwt.decode(
            request.token, request.app.config.SECRET, algorithms=["HS256"]
        )
    except jwt.exceptions.InvalidTokenError:
        return False
    else:
        return True


def protected(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            is_authenticated = check_token(request)

            if is_authenticated:
                response = await f(request, *args, **kwargs)
                return response
            else:
                return json(
                    {"error": "you are unauthorized"}, HTTPStatus.UNAUTHORIZED
                )

        return decorated_function

    return decorator(wrapped)


def admin_only(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            user = await fetch_user_from_request(request)

            if user is None:
                return json(
                    {"error": "you are unauthorized"}, HTTPStatus.UNAUTHORIZED
                )
            if not user.is_admin:
                return json(
                    {"error": "only admins allowed"}, HTTPStatus.FORBIDDEN
                )

            response = await f(request, *args, **kwargs)
            return response

        return decorated_function

    return decorator(wrapped)
