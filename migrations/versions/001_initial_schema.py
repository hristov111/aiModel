"""Initial schema with pgvector support

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create memory type enum using raw SQL (PostgreSQL doesn't support IF NOT EXISTS for types before version 9.5, so we use DO block)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE memorytypeenum AS ENUM ('fact', 'preference', 'event', 'context');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Define the enum for use in table creation (but don't create it again)
    memory_type_enum = postgresql.ENUM(
        'fact', 'preference', 'event', 'context',
        name='memorytypeenum',
        create_type=False  # Don't try to create it again
    )
    
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_summary', sa.Text(), nullable=True),
    )
    
    # Create memories table with vector column
    op.create_table(
        'memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=False),
        sa.Column('memory_type', memory_type_enum, nullable=False),
        sa.Column('importance', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_memories_conversation_id', 'memories', ['conversation_id'])
    op.create_index('ix_memories_created_at', 'memories', ['created_at'])
    op.create_index('ix_memories_importance', 'memories', ['importance'])
    
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_timestamp', 'messages', ['timestamp'])
    
    # Create vector index for cosine similarity search
    op.execute(
        'CREATE INDEX ix_memories_embedding_cosine ON memories '
        'USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )


def downgrade() -> None:
    op.drop_index('ix_memories_embedding_cosine', table_name='memories')
    op.drop_index('ix_messages_timestamp', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_index('ix_memories_importance', table_name='memories')
    op.drop_index('ix_memories_created_at', table_name='memories')
    op.drop_index('ix_memories_conversation_id', table_name='memories')
    
    op.drop_table('messages')
    op.drop_table('memories')
    op.drop_table('conversations')
    
    # Drop enum type
    op.execute('DROP TYPE memorytypeenum')
    
    # Optionally drop vector extension (commented out for safety)
    # op.execute('DROP EXTENSION IF EXISTS vector')

