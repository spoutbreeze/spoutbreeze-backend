"""change_user_id_to_uuid

Revision ID: dda8262a5257
Revises: 3b5514702f1a
Create Date: 2025-05-04 00:18:27.937509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision: str = 'dda8262a5257'
down_revision: Union[str, None] = '3b5514702f1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create temporary columns
    op.add_column('users', sa.Column('uuid_id', UUID(as_uuid=True), nullable=True))
    
    # Generate UUIDs for existing records
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM users"))
    for row in result:
        old_id = row[0]
        connection.execute(
            sa.text("UPDATE users SET uuid_id = :uuid WHERE id = :id"),
            {"uuid": uuid.uuid4(), "id": old_id}
        )
    
    # Make uuid_id NOT NULL
    op.alter_column('users', 'uuid_id', nullable=False)
    
    # Drop the primary key constraint
    op.drop_constraint('users_pkey', 'users', type_='primary')
    
    # Drop the integer id column
    op.drop_column('users', 'id')
    
    # Rename uuid_id to id
    op.alter_column('users', 'uuid_id', new_column_name='id')
    
    # Add the primary key constraint back
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    # Add the index back
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)


def downgrade():
    # This is complex and potentially lossy, so implement with caution
    op.add_column('users', sa.Column('int_id', sa.Integer(), nullable=True))
    
    # Generate sequential IDs
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM users"))
    counter = 1
    for row in result:
        uuid_id = row[0]
        connection.execute(
            sa.text("UPDATE users SET int_id = :int_id WHERE id = :uuid_id"),
            {"int_id": counter, "uuid_id": uuid_id}
        )
        counter += 1
    
    # Make int_id NOT NULL
    op.alter_column('users', 'int_id', nullable=False)
    
    # Drop the primary key constraint
    op.drop_constraint('users_pkey', 'users', type_='primary')
    
    # Drop the UUID id column
    op.drop_column('users', 'id')
    
    # Rename int_id to id
    op.alter_column('users', 'int_id', new_column_name='id')
    
    # Add the primary key constraint back
    op.create_primary_key('users_pkey', 'users', ['id'])
    
    # Add the index back
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)