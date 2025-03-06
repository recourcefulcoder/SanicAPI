from http import HTTPStatus

from app.auth import admin_only
from app.utils import validate_user_creation_data

from database.models import Account, User

from sanic import Blueprint, json
from sanic.views import HTTPMethodView

import sqlalchemy.exc
from sqlalchemy import false, select, update

admin_bp = Blueprint("admin", url_prefix="/admin")


@admin_bp.post("/create-user", name="create_user")
@admin_only
@validate_user_creation_data
async def create_user(request):
    """
    Accepts user credentials; on valid returns json with created user's data
    """
    user_data = request.json
    keys = user_data.keys()
    if "is_admin" not in keys:
        user_data["is_admin"] = False
    if "full_name" not in keys:
        user_data["full_name"] = None
    else:
        user_data["full_name"] = user_data["full_name"].strip()
    user_data["is_admin"] = str(user_data["is_admin"]).lower() in [
        "true",
        "1",
        "yes",
        "y",
    ]

    try:
        async with request.app.ctx.session() as session:
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                is_admin=user_data["is_admin"],
            )
            user.set_password(user_data["password"])
            session.add(user)
            await session.commit()
            user = await session.scalar(
                select(User).where(User.email == user_data["email"])
            )
            return json(user.serialize(), status=HTTPStatus.CREATED)
    except sqlalchemy.exc.IntegrityError:
        return json(
            {"error": "user with provided credentials already exists"},
            HTTPStatus.CONFLICT,
        )


@admin_bp.get("/users", name="user_list")
@admin_only
async def get_user_list(request):
    async with request.app.ctx.session() as session:
        users = await session.scalars(
            select(User).order_by(User.is_admin, User.id)
        )
    response_data = []
    for user in users:
        response_data.append(user.serialize())

    return json(response_data, status=HTTPStatus.OK)


@admin_bp.get("/user-accounts/<id:int>", name="user_accounts")
@admin_only
async def get_user_accounts(request, id: int):
    async with request.app.ctx.session() as session:
        accounts = await session.scalars(
            select(Account).where(Account.user_id == id)
        )
    data = []
    for acc in accounts:
        data.append(acc.serialize())
    return json(data, HTTPStatus.OK)


class UserManipulationView(HTTPMethodView):
    decorators = [admin_only]

    async def delete(self, request, id: int):
        async with request.app.ctx.session() as session:
            user = await session.scalar(select(User).where(User.id == id))
            if user is None:
                return json(
                    {"error": "user with given id doesn't exist"},
                    status=HTTPStatus.CONFLICT,
                )
            await session.delete(user)
            await session.commit()
            return json(user.serialize(), HTTPStatus.OK)

    @validate_user_creation_data
    async def put(self, request, id: int):
        """Accepts update credentials,
        returns updated user data on valid input"""
        data = request.json
        keys = data.keys()
        checkup_fields = {"password", "full_name", "email", "is_admin"}
        if not any([field in keys for field in checkup_fields]):
            return json(
                {"error": "no update credentials were provided"},
                status=HTTPStatus.BAD_REQUEST,
            )
        update_data = dict()
        for field in keys:
            if field in checkup_fields:
                update_data[field] = data[field]
        if "password" in keys:
            update_data["password"] = User.hash_password(
                update_data["password"]
            )

        async with request.app.ctx.session() as session:
            async with session.begin():
                user = await session.get(User, id)
                if user is None:
                    return json(
                        {"error": "user with given id doesn't exist"},
                        HTTPStatus.BAD_REQUEST,
                    )

                st = update(User).where(User.id == id).values(**update_data)
                await session.execute(st)
                return json(user.serialize(), HTTPStatus.OK)


@admin_bp.get("/users-with-accounts", name="users_accounts_info")
@admin_only
async def get_users_info(request):
    query = (
        select(User, Account)
        .join(User.accounts, isouter=True)
        .where(User.is_admin == false())
        .order_by(User.id, Account.id)
    )
    data = []
    async with request.app.ctx.session() as session:
        results = await session.execute(query)
        results = results.all()
        prev_row = results[0]
        account_list = []
        for row in results:
            prev_user = prev_row.User
            if row.User == prev_user:
                account_list.append(row.Account.serialize())
            else:
                user_info = prev_user.serialize()
                user_info["accounts"] = account_list
                data.append(user_info)
                account_list = []
                if row.Account is not None:
                    account_list.append(row.Account.serialize())
            prev_row = row
        user_info = prev_row.User.serialize()
        user_info["accounts"] = account_list
        data.append(user_info)
        return json(data, HTTPStatus.OK)


admin_bp.add_route(UserManipulationView.as_view(), "/user/<id:int>/")
