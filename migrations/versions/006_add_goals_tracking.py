"""Add goals and progress tracking tables

Revision ID: 006
Revises: 005_enhanced_memory
Create Date: 2025-12-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005_enhanced_memory'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add goals and goal_progress tables."""
    
    # Create goals table
    op.create_table(
        'goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, server_default='personal'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('target_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_mentioned_at', sa.DateTime(), nullable=True),
        sa.Column('mention_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('check_in_frequency', sa.String(20), nullable=True),
        sa.Column('last_check_in', sa.DateTime(), nullable=True),
        sa.Column('milestones', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('progress_notes', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('motivation', sa.Text(), nullable=True),
        sa.Column('obstacles', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for goals
    op.create_index('ix_goals_user_id', 'goals', ['user_id'])
    op.create_index('ix_goals_status', 'goals', ['status'])
    op.create_index('ix_goals_category', 'goals', ['category'])
    op.create_index('ix_goals_target_date', 'goals', ['target_date'])
    op.create_index('ix_goals_last_mentioned_at', 'goals', ['last_mentioned_at'])
    
    # Create goal_progress table
    op.create_table(
        'goal_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('progress_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('progress_delta', sa.Float(), nullable=True),
        sa.Column('sentiment', sa.String(20), nullable=True),
        sa.Column('emotion', sa.String(50), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('detected_automatically', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for goal_progress
    op.create_index('ix_goal_progress_goal_id', 'goal_progress', ['goal_id'])
    op.create_index('ix_goal_progress_user_id', 'goal_progress', ['user_id'])
    op.create_index('ix_goal_progress_created_at', 'goal_progress', ['created_at'])
    op.create_index('ix_goal_progress_progress_type', 'goal_progress', ['progress_type'])


def downgrade() -> None:
    """Drop goals and goal_progress tables."""
    
    # Drop indexes
    op.drop_index('ix_goal_progress_progress_type', table_name='goal_progress')
    op.drop_index('ix_goal_progress_created_at', table_name='goal_progress')
    op.drop_index('ix_goal_progress_user_id', table_name='goal_progress')
    op.drop_index('ix_goal_progress_goal_id', table_name='goal_progress')
    
    op.drop_index('ix_goals_last_mentioned_at', table_name='goals')
    op.drop_index('ix_goals_target_date', table_name='goals')
    op.drop_index('ix_goals_category', table_name='goals')
    op.drop_index('ix_goals_status', table_name='goals')
    op.drop_index('ix_goals_user_id', table_name='goals')
    
    # Drop tables
    op.drop_table('goal_progress')
    op.drop_table('goals')

