"""add_on_delete_cascade_to_events_channel_id

Revision ID: 5ed5a218e585
Revises: a33befb4dba0
Create Date: 2025-05-19 16:46:51.218702

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5ed5a218e585"
down_revision: Union[str, None] = "a33befb4dba0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop existing foreign key constraint
    op.drop_constraint("events_channel_id_fkey", "events", type_="foreignkey")

    # Re-create with ON DELETE CASCADE
    op.create_foreign_key(
        "events_channel_id_fkey",
        "events",
        "channels",
        ["channel_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove CASCADE delete constraint
    op.drop_constraint("events_channel_id_fkey", "events", type_="foreignkey")

    # Re-create without ON DELETE CASCADE
    op.create_foreign_key(
        "events_channel_id_fkey", "events", "channels", ["channel_id"], ["id"]
    )
