from database.models import User

import pytest

from server import create_app

from sqlalchemy import delete

from tests import testvars


@pytest.fixture(scope="session")
def app():
    return create_app()


# @pytest.fixture
# async def add_users(app):
#     async with app.ctx.session() as session:
#         session.execute()


@pytest.fixture
async def _delete_odd_users(app):
    yield
    default_emails = [testvars.TEST_ADMIN_MAIL, testvars.TEST_USER_MAIL]
    async with app.ctx.session() as session:
        com = delete(User).where(User.email.not_in(default_emails))
        session.execute(com)
        session.commit()
