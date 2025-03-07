import uuid

from database.models import Transaction

import pytest

from tests import testvars


@pytest.fixture(scope="module")
async def _add_test_transactions(app):
    async with app.ctx.session() as session:
        trans = []
        for _ in range(3):
            trans.append(
                Transaction(
                    id=str(uuid.uuid4()),
                    amount=2000.54,
                    account_id=testvars.ACCOUNT_ID,
                    user_id=testvars.USER_ID,
                )
            )
        session.add_all(trans)
        await session.commit()
    return
