from config import load_environ

from database.models import User

import pytest

from server import create_app

from sqlalchemy import delete

from tests import testvars


@pytest.fixture(scope="session", autouse=True)
def _load_dotenv():
    load_environ()
    return


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture
async def _delete_odd_users(app):
    yield
    default_emails = [testvars.TEST_ADMIN_MAIL, testvars.TEST_USER_MAIL]
    async with app.ctx.session() as session:
        com = delete(User).where(User.email.not_in(default_emails))
        await session.execute(com)
        await session.commit()
