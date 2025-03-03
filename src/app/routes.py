import datetime
from http import HTTPStatus

from app.auth import protected

import config

from database.models import Account, Transaction, User

import jwt

from sanic import Blueprint, json, text

from sqlalchemy import select


main = Blueprint("main")
auth = Blueprint("auth", url_prefix="/auth")


@main.get("/", name="index")
async def main_handler(request):
    return text("Hello, world!")


@main.get("/me", name="personal_info")
@protected
async def get_personal_data(request):
    user = request.ctx.user
    payload = {
        "id": user.id,
        "email": user.email,
        "full name": user.full_name,
    }
    return json(payload, status=HTTPStatus.OK)


@main.get("/accounts", name="account_info")
@protected
async def get_account_data(request):
    user = request.ctx.user
    st = select(Account).where(Account.user_id == user.id)
    async with request.app.ctx.session() as session:
        accounts = await session.scalars(st)

    return_data = dict()
    for account in accounts:
        return_data[account.id] = account.balance

    return json(return_data, status=HTTPStatus.OK)


@main.get("/transactions", name="transactions_info")
@protected
async def get_transactions(request):
    user = request.ctx.user
    st = select(Transaction).where(Transaction.user_id == user.id)
    async with request.app.ctx.session() as session:
        transactions = await session.scalars(st)
    data = []
    for elem in transactions:
        data.append(elem.serialize())
    return json(data, HTTPStatus.OK)


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
