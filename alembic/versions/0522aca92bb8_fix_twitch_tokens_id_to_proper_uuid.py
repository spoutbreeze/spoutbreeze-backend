"""fix_twitch_tokens_id_to_proper_uuid

Revision ID: 0522aca92bb8
Revises: 29930bad7d40
Create Date: 2025-06-09 16:35:45.823075

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "0522aca92bb8"
down_revision: Union[str, None] = "29930bad7d40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Drop the sequence and default
    op.execute("ALTER TABLE twitch_tokens ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS twitch_tokens_id_seq")

    # Step 2: Delete all existing data (since we can't convert integer IDs to UUIDs)
    op.execute("DELETE FROM twitch_tokens")

    # Step 3: Change column type to UUID with proper conversion
    op.alter_column(
        "twitch_tokens",
        "id",
        existing_type=sa.VARCHAR(),
        type_=UUID(as_uuid=True),
        existing_nullable=False,
        postgresql_using="gen_random_uuid()",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # This is a destructive migration, so downgrade will also clear data
    op.execute("DELETE FROM twitch_tokens")

    # Recreate the sequence
    op.execute("CREATE SEQUENCE twitch_tokens_id_seq")

    # Change back to VARCHAR (since we deleted data, this is safe)
    op.alter_column(
        "twitch_tokens",
        "id",
        existing_type=UUID(as_uuid=True),
        type_=sa.VARCHAR(),
        existing_nullable=False,
    )

    # Set the default back
    op.execute(
        "ALTER TABLE twitch_tokens ALTER COLUMN id SET DEFAULT nextval('twitch_tokens_id_seq'::regclass)"
    )
