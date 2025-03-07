"""update PostgreSQL SERIAL

Revision ID: 9067dbc59cdd
Revises: a0cdb30aa455
Create Date: 2025-03-07 12:42:07.426313

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9067dbc59cdd"
down_revision: Union[str, None] = "a0cdb30aa455"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "SELECT setval('user_id_seq', (SELECT MAX(id) FROM public.user));"
    )
    op.execute(
        "SELECT setval('account_id_seq', (SELECT MAX(id) FROM public.account));"
    )


def downgrade() -> None:
    pass
