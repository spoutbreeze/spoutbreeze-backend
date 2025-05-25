"""Add event status and actual times

Revision ID: a4eb7a98409b
Revises: 676044f9a641
Create Date: 2025-05-23 17:31:34.787222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a4eb7a98409b'
down_revision: Union[str, None] = '676044f9a641'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type first
    eventstatus_enum = postgresql.ENUM('SCHEDULED', 'LIVE', 'ENDED', 'CANCELLED', name='eventstatus')
    eventstatus_enum.create(op.get_bind())
    
    # Add columns with proper enum type
    op.add_column('events', sa.Column('status', eventstatus_enum, nullable=False, server_default='SCHEDULED'))
    op.add_column('events', sa.Column('actual_start_time', sa.DateTime(timezone=True), nullable=True))
    op.add_column('events', sa.Column('actual_end_time', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop columns
    op.drop_column('events', 'actual_end_time')
    op.drop_column('events', 'actual_start_time')
    op.drop_column('events', 'status')
    
    # Drop the enum type
    eventstatus_enum = postgresql.ENUM('SCHEDULED', 'LIVE', 'ENDED', 'CANCELLED', name='eventstatus')
    eventstatus_enum.drop(op.get_bind())
