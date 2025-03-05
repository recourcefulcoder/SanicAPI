import pytest

from server import create_app


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.mark.parametrize(
    "data",
    [
        {
            "email": "default@example.com",
            "password": "Harmonica52!"
        },
        {
            "email": "admin@example.com",
            "password": "admin"
        },
    ]
)
@pytest.mark.asyncio
async def auth_on_valid_data(app, data):
    pass
