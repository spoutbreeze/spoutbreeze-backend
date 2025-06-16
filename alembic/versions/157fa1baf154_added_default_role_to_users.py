"""added default role to users

Revision ID: 157fa1baf154
Revises: ca9de0bd4a34
Create Date: 2025-06-16 13:44:14.697286

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "157fa1baf154"
down_revision: Union[str, None] = "ca9de0bd4a34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Update existing NULL or empty roles to default value
    connection = op.get_bind()
    connection.execute(
        sa.text("""
        UPDATE users 
        SET roles = 'moderator' 
        WHERE roles IS NULL OR roles = '' OR roles = '[]'
    """)
    )

    # Add NOT NULL constraint and default value
    op.alter_column("users", "roles", nullable=False, server_default="moderator")


def downgrade():
    # Remove NOT NULL constraint and default
    op.alter_column("users", "roles", nullable=True, server_default=None)
