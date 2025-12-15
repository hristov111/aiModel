"""Add emotion detection and history tracking

Revision ID: 003_emotion_detection
Revises: 002_add_users_and_multi_tenancy
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

# revision identifiers
revision = '003_emotion_detection'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Add emotion_history table for tracking detected emotions."""
    
    # Create emotion_history table
    op.create_table(
        'emotion_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=True),
        sa.Column('emotion', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('intensity', sa.String(20), nullable=False),
        sa.Column('indicators', JSONB, nullable=True),
        sa.Column('message_snippet', sa.Text, nullable=True),
        sa.Column('detected_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE')
    )
    
    # Create indexes for performance
    op.create_index('ix_emotion_history_user_id', 'emotion_history', ['user_id'])
    op.create_index('ix_emotion_history_detected_at', 'emotion_history', ['detected_at'])
    op.create_index('ix_emotion_history_emotion', 'emotion_history', ['emotion'])
    
    print("✅ Created emotion_history table with indexes")


def downgrade():
    """Remove emotion detection tables."""
    
    # Drop indexes
    op.drop_index('ix_emotion_history_emotion', table_name='emotion_history')
    op.drop_index('ix_emotion_history_detected_at', table_name='emotion_history')
    op.drop_index('ix_emotion_history_user_id', table_name='emotion_history')
    
    # Drop table
    op.drop_table('emotion_history')
    
    print("✅ Removed emotion_history table")

