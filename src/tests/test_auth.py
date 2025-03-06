import asyncio
from datetime import timedelta
from http import HTTPStatus

from app.admin_routes import admin_bp
from app.routes import auth as auth_bp, main as main_bp
from app.utils import generate_jwt_token

import pytest

from sanic_testing.testing import SanicASGITestClient

from tests import testvars


@pytest.mark.parametrize(
    "data",
    [
        {
            "email": testvars.TEST_USER_MAIL,
            "password": testvars.TEST_USER_PASS,
        },
        {
            "email": testvars.TEST_ADMIN_MAIL,
            "password": testvars.TEST_ADMIN_PASS,
        },
        {
            "email": "admin@example.com",
            "password": "admin",
            "random_key": "random_value",
        },
    ],
)
@pytest.mark.asyncio
async def test_200_on_valid_credentials(app, data):
    test_client = SanicASGITestClient(app)
    _, response = await test_client.post(
        app.url_for(f"{auth_bp.name}.login"), json=data
    )
    assert response.status == HTTPStatus.OK


@pytest.mark.parametrize(
    "data",
    [
        {"email": "invalid_email@example.com", "password": "any_password"},
        {"email": "admin@example.com", "password": "invalid_admin_password"},
    ],
)
@pytest.mark.asyncio
async def test_401_on_wrong_credentials(app, data):
    test_client = SanicASGITestClient(app)
    _, response = await test_client.post(
        app.url_for(f"{auth_bp.name}.login"), json=data
    )
    assert response.status == HTTPStatus.IM_A_TEAPOT


@pytest.mark.parametrize(
    "data",
    [
        {"without_email": "no_email", "password": "any_password"},
        {"email": "admin@example.com", "without_password": "no_password"},
        {},
        {"key1": "val1", "key2": "val2"},
    ],
)
@pytest.mark.asyncio
async def test_400_on_invalid_data(app, data):
    test_client = SanicASGITestClient(app)
    _, response = await test_client.post(
        app.url_for(f"{auth_bp.name}.login"), json=data
    )
    assert response.status == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(
    "endpoint,args,method",
    [
        (f"{main_bp.name}.personal_info", {}, "GET"),
        (f"{main_bp.name}.accounts_info", {}, "GET"),
        (f"{main_bp.name}.transactions_info", {}, "GET"),
        (f"{admin_bp.name}.user_list", {}, "GET"),
        (f"{admin_bp.name}.user_accounts", {"id": 1}, "GET"),
        (f"{admin_bp.name}.create_user", {}, "POST"),
    ],
)
@pytest.mark.asyncio
async def test_endpoints_protected(app, endpoint, args, method):
    """Passes invalid requests (without token/with invalid token) to
    protected endpoint and expects 401 status code"""
    test_client = SanicASGITestClient(app)
    no_token_request = asyncio.create_task(
        test_client.request(
            url=app.url_for(endpoint, **args),
            method=method,
            json={"any_valid_json": "json"},
        )
    )
    exp_token = generate_jwt_token(
        testvars.TEST_USER_MAIL,
        app.config.SECRET,
        exp_time=timedelta(minutes=-2),
    )
    exp_token_request = asyncio.create_task(
        test_client.request(
            url=app.url_for(endpoint, **args),
            method=method,
            headers={"Authorization": f"Bearer {exp_token}"},
            json={"any_valid_json": "json"},
        )
    )
    _, response1 = await no_token_request
    _, response2 = await exp_token_request
    assert response1.status == HTTPStatus.UNAUTHORIZED
    assert response2.status == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize(
    "endpoint,args,method",
    [
        (f"{admin_bp.name}.create_user", {}, "POST"),
        (f"{admin_bp.name}.user_list", {}, "GET"),
        (f"{admin_bp.name}.user_accounts", {"id": 1}, "GET"),
    ],
)
@pytest.mark.asyncio
async def test_admin_endpoints_protected(app, endpoint, args, method):
    test_client = SanicASGITestClient(app)
    usr_token = generate_jwt_token(
        testvars.TEST_USER_MAIL,
        app.config.SECRET,
    )
    _, response = await test_client.request(
        url=app.url_for(endpoint, **args),
        method=method,
        headers={"Authorization": f"Bearer {usr_token}"},
        json={"any_valid_json": "json"},
    )
    assert response.status == HTTPStatus.FORBIDDEN
