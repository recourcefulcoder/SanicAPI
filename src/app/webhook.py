from http import HTTPStatus
from typing import Dict, Optional

from app.utils import retry_decorator, webhook_signature_valid

from database.models import Account, Transaction, User

from sanic import Blueprint, json

from sqlalchemy import insert, select

webhook = Blueprint("webhook")


async def check_entities(
    session_maker, data: Dict[str, str]
) -> Optional[Dict[str, str]]:
    """checks whether transaction and user with given id exist and are valid;
    if not, returns errors JSON data; if do, returns nothing"""
    async with session_maker() as session:
        transaction = await session.execute(
            select(Transaction).where(Transaction.id == data["transaction_id"])
        )
        if transaction.scalar():
            return {"error": "transaction already exists"}

        user = await session.execute(
            select(User).where(User.id == int(data["user_id"]))
        )
        user = user.scalar()

        account_owner = await session.execute(
            select(User).join(
                User.accounts.and_(Account.id == data["account_id"])
            )
        )
        account_owner = account_owner.first()

        if not user or (
            account_owner is not None and user != account_owner.User
        ):
            return {"error": "invalid user id"}
    return None


@webhook.post("/webhook", name="webhook")
@retry_decorator
async def process_payment(request):
    data = request.json
    if not webhook_signature_valid(data):
        return json({"error": "invalid json data"}, HTTPStatus.BAD_REQUEST)
    errors = await check_entities(request.app.ctx.session, data)
    if errors is not None:
        return json(errors, HTTPStatus.CONFLICT)

    async with request.app.ctx.session(autoflush=False) as session:
        account = await session.get(Account, data["account_id"])
        if account is None:
            await session.execute(
                insert(Account).values(
                    id=int(data["account_id"]),
                    user_id=int(data["user_id"]),
                )
            )
            account = await session.get(Account, data["account_id"])
        trans = Transaction(
            id=data["transaction_id"],
            amount=float(data["amount"]),
            account_id=int(data["account_id"]),
            user_id=int(data["user_id"]),
        )
        session.add(trans)
        account.balance += data["amount"]
        await session.commit()

    return json({"message": "OK"}, HTTPStatus.OK)
