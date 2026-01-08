"""Add personality memory isolation

Revision ID: 007_personality_isolation
Revises: 006_add_goals_tracking
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

# revision identifiers
revision = '007_personality_isolation'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Add personality-scoped memory isolation."""
    
    # ========================================
    # 1. MODIFY personality_profiles TABLE
    # ========================================
    
    # Add personality_name column
    op.add_column('personality_profiles', sa.Column('personality_name', sa.String(100), nullable=True))
    
    # Backfill personality_name from archetype for existing profiles
    op.execute("""
        UPDATE personality_profiles 
        SET personality_name = COALESCE(archetype, 'default')
        WHERE personality_name IS NULL
    """)
    
    # Make personality_name not null
    op.alter_column('personality_profiles', 'personality_name', nullable=False)
    
    # Drop old unique constraint on user_id (if it exists)
    try:
        op.drop_constraint('personality_profiles_user_id_key', 'personality_profiles', type_='unique')
    except Exception:
        pass  # Constraint might not exist
    
    # Create new unique constraint on (user_id, personality_name)
    op.create_index(
        'ix_personality_profiles_user_personality',
        'personality_profiles',
        ['user_id', 'personality_name'],
        unique=True
    )
    
    print("✅ Updated personality_profiles table")
    
    # ========================================
    # 2. MODIFY conversations TABLE
    # ========================================
    
    # Add personality_id column
    op.add_column('conversations', sa.Column('personality_id', UUID(as_uuid=True), nullable=True))
    
    # Backfill personality_id from user's personality profile
    op.execute("""
        UPDATE conversations 
        SET personality_id = personality_profiles.id 
        FROM personality_profiles 
        WHERE conversations.user_id = personality_profiles.user_id
    """)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_conversations_personality_id',
        'conversations',
        'personality_profiles',
        ['personality_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes
    op.create_index('ix_conversations_personality_id', 'conversations', ['personality_id'])
    op.create_index('ix_conversations_user_personality', 'conversations', ['user_id', 'personality_id'])
    
    print("✅ Updated conversations table")
    
    # ========================================
    # 3. MODIFY memories TABLE
    # ========================================
    
    # Add personality_id column
    op.add_column('memories', sa.Column('personality_id', UUID(as_uuid=True), nullable=True))
    
    # Add is_shared column
    op.add_column('memories', sa.Column('is_shared', sa.Boolean, nullable=False, server_default='false'))
    
    # Backfill personality_id from conversation's personality_id
    op.execute("""
        UPDATE memories 
        SET personality_id = conversations.personality_id 
        FROM conversations 
        WHERE memories.conversation_id = conversations.id
    """)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_memories_personality_id',
        'memories',
        'personality_profiles',
        ['personality_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes
    op.create_index('ix_memories_personality_id', 'memories', ['personality_id'])
    op.create_index('ix_memories_user_personality', 'memories', ['user_id', 'personality_id'])
    op.create_index('ix_memories_is_shared', 'memories', ['is_shared'])
    
    print("✅ Updated memories table")
    
    # ========================================
    # 4. MODIFY relationship_state TABLE
    # ========================================
    
    # Add personality_id column
    op.add_column('relationship_state', sa.Column('personality_id', UUID(as_uuid=True), nullable=True))
    
    # Backfill personality_id from user's personality profile
    op.execute("""
        UPDATE relationship_state 
        SET personality_id = personality_profiles.id 
        FROM personality_profiles 
        WHERE relationship_state.user_id = personality_profiles.user_id
    """)
    
    # Drop old unique constraint on user_id (if it exists)
    try:
        op.drop_constraint('relationship_state_user_id_key', 'relationship_state', type_='unique')
    except Exception:
        pass  # Constraint might not exist
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_relationship_state_personality_id',
        'relationship_state',
        'personality_profiles',
        ['personality_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes
    op.create_index('ix_relationship_state_personality_id', 'relationship_state', ['personality_id'])
    op.create_index(
        'ix_relationship_state_user_personality',
        'relationship_state',
        ['user_id', 'personality_id'],
        unique=True
    )
    
    print("✅ Updated relationship_state table")
    print("✅ Personality memory isolation migration complete!")


def downgrade():
    """Remove personality isolation."""
    
    # Drop relationship_state changes
    op.drop_index('ix_relationship_state_user_personality', table_name='relationship_state')
    op.drop_index('ix_relationship_state_personality_id', table_name='relationship_state')
    op.drop_constraint('fk_relationship_state_personality_id', 'relationship_state', type_='foreignkey')
    op.drop_column('relationship_state', 'personality_id')
    
    # Drop memories changes
    op.drop_index('ix_memories_is_shared', table_name='memories')
    op.drop_index('ix_memories_user_personality', table_name='memories')
    op.drop_index('ix_memories_personality_id', table_name='memories')
    op.drop_constraint('fk_memories_personality_id', 'memories', type_='foreignkey')
    op.drop_column('memories', 'is_shared')
    op.drop_column('memories', 'personality_id')
    
    # Drop conversations changes
    op.drop_index('ix_conversations_user_personality', table_name='conversations')
    op.drop_index('ix_conversations_personality_id', table_name='conversations')
    op.drop_constraint('fk_conversations_personality_id', 'conversations', type_='foreignkey')
    op.drop_column('conversations', 'personality_id')
    
    # Drop personality_profiles changes
    op.drop_index('ix_personality_profiles_user_personality', table_name='personality_profiles')
    op.drop_column('personality_profiles', 'personality_name')
    
    print("✅ Reverted personality isolation changes")

