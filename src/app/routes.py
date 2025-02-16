import datetime
from http import HTTPStatus

from app.auth import protected

import config

from database.models import User

import jwt

from sanic import Blueprint, json, text

from sqlalchemy import select


main = Blueprint("main")
auth = Blueprint("auth")


@main.middleware("request")
async def fetch_user_from_token(request):
    if not request.token:
        request.ctx.user = None
        return
    try:
        payload = jwt.decode(
            request.token, request.app.config.SECRET, algorithms=["HS256"]
        )
    except jwt.InvalidTokenError:
        request.ctx.user = None
        return
    st = select(User).where(User.email == payload["sub"])
    async with request.app.ctx.session() as session:
        user = await session.scalar(st)
    request.ctx.user = user


@main.get("/", name="index")
async def main_handler(request):
    return text("Hello, world!")


@main.get("/me", name="info")
@protected
async def return_data(request):
    user = request.ctx.user
    payload = {
        "id": user.id,
        "email": user.email,
        "full name": user.full_name,
    }
    return json(payload, status=HTTPStatus.OK)


@auth.post("/login", name="login")
async def login_user(request):
    """Logs user in; credentials must be sent in
    request's JSON body, and are supposed to be email and password"""
    credentials = request.json
    if (
        "email" not in credentials.keys()
        or "password" not in credentials.keys()
    ):
        return json(
            {"error": "invalid credentials list"},
            status=HTTPStatus.UNAUTHORIZED,
        )

    stmt = select(User).where(User.email == credentials["email"])
    async with request.app.ctx.session() as session:
        user = await session.scalar(stmt)
        if not user.verify_password(credentials["password"]):
            return json(
                {"error: invalid password"}, status=HTTPStatus.UNAUTHORIZED
            )

    exp_time = (
        datetime.datetime.now(datetime.timezone.utc)
        + config.ACCESS_TOKEN_EXP_TIME
    )
    payload = {
        "sub": str(user.email),
        "exp": str(int(exp_time.timestamp())),
    }
    token = jwt.encode(payload, request.app.config.SECRET, algorithm="HS256")

    return json({"access_token": token}, status=HTTPStatus.OK)
