from http import HTTPStatus

from app.admin_routes import admin_bp
from app.utils import generate_jwt_token

from database.models import User

import pytest

from sanic_testing.testing import SanicASGITestClient

from tests import testvars


@pytest.fixture
def admin_token(app):
    return generate_jwt_token(testvars.TEST_ADMIN_MAIL, app.config.SECRET)


@pytest.mark.parametrize(
    "data",
    [
        {"email": "invalid_email", "password": "valid_password"},
        {"email": "invalid_email@", "password": "valid_password"},
        {"email": "invalid_email@dodo", "password": "valid_password"},
        {"email": "invalid_email@dodo.c", "password": "valid_password"},
        {"email": "valid@gmail.com", "password": "Invаlid"},
        {"email": "valid@gmail.com", "password": "Invаlidå"},
        {"email": "valid@gmail.com", "password": "Unusal😁symbol"},
        {
            "email": "valid@dodo.com",
            "password": "valid_password",
            "full_name": "На русском!",
        },
        {
            "email": "valid@dodo.com",
            "password": "valid_password",
            "full_name": "hyggelig å møte deg",
        },
        {
            "email": "valid@dodo.com",
            "password": "valid_password",
            "full_name": "Kind Of COrrect Y1t",
        },
        {"email": "no_pass@gmail.com"},
        {"password": "no_email"},
        {},
        {"key1": "val1"},
    ],
)
@pytest.mark.asyncio
async def test_invalid_user_creation_data(app, admin_token, data):
    test_client = SanicASGITestClient(app)
    _, response = await test_client.post(
        app.url_for(f"{admin_bp.name}.create_user"),
        headers={"Authorization": f"Bearer {admin_token}"},
        json=data,
    )
    assert response.status == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(
    "data",
    [
        {"email": "invalid_email", "password": "valid_password"},
        {"email": "invalid_email@", "password": "valid_password"},
        {"email": "invalid_email@dodo", "password": "valid_password"},
        {"email": "invalid_email@dodo.c", "password": "valid_password"},
        {"email": "valid@gmail.com", "password": "Invаlid"},
        {"email": "valid@gmail.com", "password": "Invаlidå"},
        {"email": "valid@gmail.com", "password": "Unusal😁symbol"},
        {
            "email": "valid@dodo.com",
            "password": "valid_password",
            "full_name": "На русском!",
        },
        {
            "email": "valid@dodo.com",
            "password": "valid_password",
            "full_name": "hyggelig å møte deg",
        },
        {
            "email": "valid@dodo.com",
            "password": "valid_password",
            "full_name": "Kind Of COrrect Y1t",
        },
        {"email": "no_pass@gmail.com"},
        {"password": "no_email"},
        {},
        {"key1": "val1"},
    ],
)
@pytest.mark.asyncio
async def test_invalid_user_edit_data(app, admin_token, data):
    test_client = SanicASGITestClient(app)
    _, response = await test_client.put(
        app.url_for(
            f"{admin_bp.name}.UserManipulationView", id=testvars.USER_ID
        ),
        headers={"Authorization": f"Bearer {admin_token}"},
        json=data,
    )
    assert response.status == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(
    "data",
    [
        {"email": "valid@gmail.com", "password": "valid_password"},
        {
            "email": "valid1@gmail.com",
            "password": "valid_password",
            "is_admin": "True",
        },
        {
            "email": "valid2@gmail.com",
            "password": "valid_password",
            "full_name": "Absolute Nonsence",
        },
        {
            "email": "valid3@gmail.com",
            "password": "valid_password",
            "full_name": "  Still valid name  ",
        },
    ],
)
@pytest.mark.usefixtures("_delete_odd_users")
@pytest.mark.asyncio
async def test_valid_user_creation_data(app, admin_token, data):
    test_client = SanicASGITestClient(app)
    _, response = await test_client.post(
        app.url_for(f"{admin_bp.name}.create_user"),
        headers={"Authorization": f"Bearer {admin_token}"},
        json=data,
    )
    assert response.status == HTTPStatus.CREATED


@pytest.mark.asyncio
async def test_users_endpoint(app, admin_token):
    test_client = SanicASGITestClient(app)
    _, response = await test_client.get(
        app.url_for(f"{admin_bp.name}.user_list"),
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status == HTTPStatus.OK
    assert bool(response.json)  # checking that is not empty


@pytest.mark.asyncio
async def test_accounts_endpoint(app, admin_token):
    test_client = SanicASGITestClient(app)
    _, response = await test_client.get(
        app.url_for(f"{admin_bp.name}.user_accounts", id=testvars.USER_ID),
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status == HTTPStatus.OK
    assert bool(response.json)  # checking that is not empty


@pytest.mark.usefixtures("_delete_odd_users")
@pytest.mark.asyncio
async def test_user_deletion(app, admin_token):
    async with app.ctx.session() as session:
        user = User(email="valid@gmail.com", is_admin=False)
        user.set_password("valid_password")
        session.add(user)
        await session.flush()
        user_id = user.id
        await session.commit()

    test_client = SanicASGITestClient(app)
    _, response = await test_client.delete(
        app.url_for(f"{admin_bp.name}.UserManipulationView", id=user_id),
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status == HTTPStatus.OK
    assert bool(response.json)  # checking that is not empty
