"""Add personality system and relationship tracking

Revision ID: 004_personality_system
Revises: 003_emotion_detection
Create Date: 2024-01-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

# revision identifiers
revision = '004_personality_system'
down_revision = '003_emotion_detection'
branch_labels = None
depends_on = None


def upgrade():
    """Add personality_profiles and relationship_state tables."""
    
    # Create personality_profiles table
    op.create_table(
        'personality_profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, unique=True),
        
        # Core Identity
        sa.Column('archetype', sa.String(50), nullable=True),
        sa.Column('relationship_type', sa.String(50), nullable=True),
        
        # Personality Traits (0-10 scales)
        sa.Column('humor_level', sa.Integer, nullable=True, default=5),
        sa.Column('formality_level', sa.Integer, nullable=True, default=5),
        sa.Column('enthusiasm_level', sa.Integer, nullable=True, default=5),
        sa.Column('empathy_level', sa.Integer, nullable=True, default=7),
        sa.Column('directness_level', sa.Integer, nullable=True, default=5),
        sa.Column('curiosity_level', sa.Integer, nullable=True, default=5),
        sa.Column('supportiveness_level', sa.Integer, nullable=True, default=7),
        sa.Column('playfulness_level', sa.Integer, nullable=True, default=5),
        
        # Advanced Configuration
        sa.Column('backstory', sa.Text, nullable=True),
        sa.Column('custom_instructions', sa.Text, nullable=True),
        sa.Column('speaking_style', sa.Text, nullable=True),
        
        # Behavioral Preferences
        sa.Column('asks_questions', sa.Boolean, nullable=True, default=True),
        sa.Column('uses_examples', sa.Boolean, nullable=True, default=True),
        sa.Column('shares_opinions', sa.Boolean, nullable=True, default=True),
        sa.Column('challenges_user', sa.Boolean, nullable=True, default=False),
        sa.Column('celebrates_wins', sa.Boolean, nullable=True, default=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('version', sa.Integer, nullable=False, default=1),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create index
    op.create_index('ix_personality_profiles_user_id', 'personality_profiles', ['user_id'])
    
    print("✅ Created personality_profiles table")
    
    # Create relationship_state table
    op.create_table(
        'relationship_state',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, unique=True),
        
        # Relationship Metrics
        sa.Column('total_messages', sa.Integer, nullable=False, default=0),
        sa.Column('relationship_depth_score', sa.Float, nullable=False, default=0.0),
        sa.Column('trust_level', sa.Float, nullable=False, default=5.0),
        
        # Timeline
        sa.Column('first_interaction', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('last_interaction', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('days_known', sa.Integer, nullable=False, default=0),
        
        # Milestones
        sa.Column('milestones', JSONB, nullable=True, default=[]),
        
        # User Feedback
        sa.Column('positive_reactions', sa.Integer, nullable=False, default=0),
        sa.Column('negative_reactions', sa.Integer, nullable=False, default=0),
        
        # Metadata
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create index
    op.create_index('ix_relationship_state_user_id', 'relationship_state', ['user_id'])
    
    print("✅ Created relationship_state table")


def downgrade():
    """Remove personality system tables."""
    
    # Drop indexes
    op.drop_index('ix_relationship_state_user_id', table_name='relationship_state')
    op.drop_index('ix_personality_profiles_user_id', table_name='personality_profiles')
    
    # Drop tables
    op.drop_table('relationship_state')
    op.drop_table('personality_profiles')
    
    print("✅ Removed personality system tables")

