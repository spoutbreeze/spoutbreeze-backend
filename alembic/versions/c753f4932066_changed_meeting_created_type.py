"""Changed_meeting_created_type

Revision ID: c753f4932066
Revises: 88f952262c32
Create Date: 2025-05-16 02:53:04.258306

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c753f4932066"
down_revision: Union[str, None] = "88f952262c32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events", sa.Column("meeting_created_bool", sa.Boolean(), nullable=True)
    )

    op.execute(
        "UPDATE events SET meeting_created_bool = (meeting_created = 'true' OR meeting_created = 'True' OR meeting_created = 't')"
    )

    op.drop_column("events", "meeting_created")

    op.alter_column("events", "meeting_created_bool", new_column_name="meeting_created")

    op.alter_column(
        "events", "meeting_created", nullable=False, server_default=sa.text("false")
    )


def downgrade() -> None:
    op.add_column(
        "events", sa.Column("meeting_created_str", sa.String(), nullable=True)
    )
    op.execute(
        "UPDATE events SET meeting_created_str = CASE WHEN meeting_created THEN 'true' ELSE 'false' END"
    )
    op.drop_column("events", "meeting_created")
    op.alter_column("events", "meeting_created_str", new_column_name="meeting_created")
    op.alter_column(
        "events", "meeting_created", nullable=False, server_default=sa.text("'false'")
    )
