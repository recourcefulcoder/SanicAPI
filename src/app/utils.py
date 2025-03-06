import asyncio
import datetime
import random
import re
from functools import wraps
from hashlib import sha256
from http import HTTPStatus
from typing import Dict, Final, Optional
from uuid import UUID

import config

from database.models import User

import jwt

from sanic import json
from sanic.log import error_logger

from sqlalchemy import select


ALLOWED_PASSWORD_CHARACTERS: Final = "!@#$%^&*()_+=-'\"<>,./\\|{}[]:;`~]+$"


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


def generate_jwt_token(user_email: str, secret: str, exp_time=None) -> str:
    if exp_time is None:
        exp_time = config.ACCESS_TOKEN_EXP_TIME

    exp_time = datetime.datetime.now(datetime.timezone.utc) + exp_time
    payload = {
        "sub": str(user_email),
        "exp": str(int(exp_time.timestamp())),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def email_is_valid(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.fullmatch(pattern, email))


def password_is_valid(password: str) -> bool:
    pattern = r"""^[A-Za-z0-9!@#$%^&*()_+=\-"'<>,./\\|{}\[\]:;`~]+$"""
    return bool(re.fullmatch(pattern, password))


def fullname_is_valid(full_name: str) -> bool:
    pattern = r"^[A-Za-z]+(?:\s[A-Za-z]+)*$"
    return bool(re.fullmatch(pattern, full_name))


def valid_email_decorator(wrapped):
    """returns BAD_REQUEST if
    email not in request data / email provided is invalid"""

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


def validate_user_creation_data(wrapped):
    """Decorator validating request data for user creation,
    returning error in case of invalid data and proceeding with
    handler on valid data"""

    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            data = request.json
            keys = data.keys()
            required_keys = {"password", "email"}
            if not data or not required_keys.issubset(keys):
                return json(
                    {
                        "error": "invalid request data: "
                        "missing email and/or password"
                    },
                    HTTPStatus.BAD_REQUEST,
                )

            if not email_is_valid(data["email"]):
                return json(
                    {"error": "invalid email format"}, HTTPStatus.BAD_REQUEST
                )
            if not password_is_valid(data["password"]):
                return json(
                    {
                        "error": "invalid password value - "
                        "only english letters, digits "
                        f"and special characters "
                        f"{ALLOWED_PASSWORD_CHARACTERS} allowed"
                    }
                )

            if "full_name" in keys and not fullname_is_valid(
                data["full_name"].strip()
            ):
                return json(
                    {
                        "error": "invalid full_name "
                        "value - it can be only "
                        "list of words, consisting of "
                        "ASCII characters"
                    },
                    HTTPStatus.BAD_REQUEST,
                )

            response = await f(request, *args, **kwargs)
            return response

        return decorated_function

    return decorator(wrapped)


def valid_webhook_data(json_obj: Dict[str, str]) -> bool:
    required_keys = {
        "transaction_id",
        "user_id",
        "account_id",
        "amount",
        "signature",
    }
    if not all(field in json_obj.keys() for field in required_keys):
        return False
    try:
        UUID(json_obj["transaction_id"])
        int(json_obj["account_id"])
        int(json_obj["user_id"])
        float(json_obj["amount"])
    except ValueError:
        return False
    return True


def webhook_signature_valid(json_obj: Dict[str, str]) -> bool:
    if not valid_webhook_data(json_obj):
        return False

    string = (
        f"{json_obj['account_id']}{json_obj['amount']}"
        f"{json_obj['transaction_id']}{json_obj['user_id']}"
        f"{config.WEBHOOK_SECRET}"
    )

    return sha256(string.encode("utf-8")).hexdigest() == json_obj["signature"]


def retry_decorator(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            retries = 3
            for i in range(retries):
                try:
                    return await f(request, *args, **kwargs)
                except Exception as e:
                    error_logger.warning(f"Error on processing webhook: {e}")
                    if i < retries - 1:
                        await asyncio.sleep(random.uniform(0.2, 0.4) * i)
                    else:
                        error_logger.error(
                            f"Failed to process webhook in {retries} tries"
                        )
                        return json(
                            {"error": "unexpected server error"},
                            HTTPStatus.INTERNAL_SERVER_ERROR,
                        )

        return decorated_function

    return decorator(wrapped)
