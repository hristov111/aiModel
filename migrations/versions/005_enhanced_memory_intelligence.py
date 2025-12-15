"""Enhanced memory intelligence with categorization and tracking

Revision ID: 005_enhanced_memory
Revises: 004_personality_system
Create Date: 2024-01-15 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

# revision identifiers
revision = '005_enhanced_memory'
down_revision = '004_personality_system'
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced memory intelligence fields."""
    
    # Add new columns to memories table
    op.add_column('memories', sa.Column('user_id', UUID(as_uuid=True), nullable=True))
    op.add_column('memories', sa.Column('category', sa.String(50), nullable=True))
    op.add_column('memories', sa.Column('importance_scores', JSONB, nullable=True))
    op.add_column('memories', sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow, server_default=sa.func.now()))
    op.add_column('memories', sa.Column('last_accessed', sa.DateTime, nullable=True))
    op.add_column('memories', sa.Column('access_count', sa.Integer, nullable=False, default=0, server_default='0'))
    op.add_column('memories', sa.Column('decay_factor', sa.Float, nullable=False, default=1.0, server_default='1.0'))
    op.add_column('memories', sa.Column('is_active', sa.Boolean, nullable=False, default=True, server_default='true'))
    op.add_column('memories', sa.Column('consolidated_from', JSONB, nullable=True))
    op.add_column('memories', sa.Column('superseded_by', UUID(as_uuid=True), nullable=True))
    op.add_column('memories', sa.Column('related_entities', JSONB, nullable=True))
    
    # Populate user_id from conversations (data migration)
    op.execute("""
        UPDATE memories 
        SET user_id = conversations.user_id 
        FROM conversations 
        WHERE memories.conversation_id = conversations.id
    """)
    
    # Now make user_id not null
    op.alter_column('memories', 'user_id', nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_memories_user_id',
        'memories',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create new indexes
    op.create_index('ix_memories_user_id', 'memories', ['user_id'])
    op.create_index('ix_memories_category', 'memories', ['category'])
    op.create_index('ix_memories_is_active', 'memories', ['is_active'])
    op.create_index('ix_memories_last_accessed', 'memories', ['last_accessed'])
    
    print("✅ Enhanced memory intelligence fields added")


def downgrade():
    """Remove enhanced memory fields."""
    
    # Drop indexes
    op.drop_index('ix_memories_last_accessed', table_name='memories')
    op.drop_index('ix_memories_is_active', table_name='memories')
    op.drop_index('ix_memories_category', table_name='memories')
    op.drop_index('ix_memories_user_id', table_name='memories')
    
    # Drop foreign key
    op.drop_constraint('fk_memories_user_id', 'memories', type_='foreignkey')
    
    # Drop columns
    op.drop_column('memories', 'related_entities')
    op.drop_column('memories', 'superseded_by')
    op.drop_column('memories', 'consolidated_from')
    op.drop_column('memories', 'is_active')
    op.drop_column('memories', 'decay_factor')
    op.drop_column('memories', 'access_count')
    op.drop_column('memories', 'last_accessed')
    op.drop_column('memories', 'updated_at')
    op.drop_column('memories', 'importance_scores')
    op.drop_column('memories', 'category')
    op.drop_column('memories', 'user_id')
    
    print("✅ Removed enhanced memory fields")

