"""add default data

Revision ID: a0cdb30aa455
Revises: 960b953c8637
Create Date: 2025-03-05 10:14:39.213276

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from database.models import Account, User


# revision identifiers, used by Alembic.
revision: str = "a0cdb30aa455"
down_revision: Union[str, None] = "960b953c8637"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ADMIN_ID = 1
ACCOUNT_ID = 1
USER_TABLE_NAME = User.__tablename__
ACCOUNT_TABLE_NAME = Account.__tablename__


def upgrade() -> None:
    """Adding default user, default user's account and default admin"""
    user_table = table(
        USER_TABLE_NAME,
        column("id", sa.Integer),
        column("full_name", sa.String),
        column("email", sa.String),
        column("password", sa.String),
        column("is_admin", sa.Boolean),
    )

    account_table = table(
        ACCOUNT_TABLE_NAME,
        column("id", sa.Integer),
        column("balance", sa.Numeric(12, 2)),
        column("user_id", sa.Integer),
    )

    op.bulk_insert(
        user_table,
        [
            {
                "id": ADMIN_ID,
                "email": "admin@example.com",
                "password": User.hash_password("admin"),
                "is_admin": True,
            },
            {
                "id": ADMIN_ID + 1,
                "email": "default@example.com",
                "full_name": "John Doe",
                "password": User.hash_password("Harmonica52!"),
                "is_admin": False,
            },
        ],
    )
    op.bulk_insert(
        account_table,
        [
            {"id": ACCOUNT_ID, "balance": 0.0, "user_id": ADMIN_ID + 1},
        ],
    )


def downgrade() -> None:
    op.execute(
        f"DELETE FROM {USER_TABLE_NAME} WHERE id IN ({ADMIN_ID}, {ADMIN_ID + 1})"
    )
    op.execute(f"DELETE FROM {ACCOUNT_TABLE_NAME} WHERE id = {ACCOUNT_ID}")
