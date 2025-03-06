import pytest

from server import create_app


@pytest.fixture(scope="session")
def app():
    return create_app()


# @pytest.fixture(scope="session", autouse=True)
# async def add_users():
#     pass
#
#
# @pytest.fixture(scope="session", autouse=True)
# async def delete_users():
#     pass
