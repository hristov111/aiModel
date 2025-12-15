"""Add users table and multi-tenancy support

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('external_user_id', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=True, unique=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_active', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True),
    )
    
    # Create indexes on users table
    op.create_index('ix_users_external_user_id', 'users', ['external_user_id'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Add user_id column to conversations (nullable first)
    op.add_column('conversations', 
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add title column to conversations
    op.add_column('conversations',
        sa.Column('title', sa.String(255), nullable=True)
    )
    
    # Create a default user for existing conversations
    op.execute("""
        INSERT INTO users (id, external_user_id, display_name, created_at, last_active)
        VALUES (
            'a0000000-0000-0000-0000-000000000001'::uuid,
            'default_user',
            'Default User (Migration)',
            now(),
            now()
        )
        ON CONFLICT (external_user_id) DO NOTHING;
    """)
    
    # Set all existing conversations to belong to the default user
    op.execute("""
        UPDATE conversations
        SET user_id = 'a0000000-0000-0000-0000-000000000001'::uuid
        WHERE user_id IS NULL;
    """)
    
    # Make user_id non-nullable
    op.alter_column('conversations', 'user_id', nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_conversations_user_id',
        'conversations',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes on conversations
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_updated_at', 'conversations', ['updated_at'])


def downgrade() -> None:
    # Drop indexes on conversations
    op.drop_index('ix_conversations_updated_at', table_name='conversations')
    op.drop_index('ix_conversations_user_id', table_name='conversations')
    
    # Drop foreign key
    op.drop_constraint('fk_conversations_user_id', 'conversations', type_='foreignkey')
    
    # Drop columns from conversations
    op.drop_column('conversations', 'title')
    op.drop_column('conversations', 'user_id')
    
    # Drop indexes on users
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_external_user_id', table_name='users')
    
    # Drop users table
    op.drop_table('users')

