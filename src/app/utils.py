import asyncio
import random
import re
from functools import wraps
from hashlib import sha256
from http import HTTPStatus
from typing import Dict, Optional
from uuid import UUID

import config

from database.models import User

import jwt

from sanic import json
from sanic.log import error_logger

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
