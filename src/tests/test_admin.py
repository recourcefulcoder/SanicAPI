from http import HTTPStatus

from app.admin_routes import admin_bp
from app.utils import generate_jwt_token

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
