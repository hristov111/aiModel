"""Add global personalities for multi-user character system

Revision ID: 008_global_personalities
Revises: 007_personality_isolation
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

# revision identifiers
revision = '008_global_personalities'
down_revision = '007_personality_isolation'
branch_labels = None
depends_on = None


def upgrade():
    """Add system user and 8 global personalities."""
    
    # Generate UUIDs for system user and personalities
    system_user_id = str(uuid.uuid4())
    
    personality_ids = {
        'elara': str(uuid.uuid4()),
        'seraphina': str(uuid.uuid4()),
        'isla': str(uuid.uuid4()),
        'lyra': str(uuid.uuid4()),
        'aria': str(uuid.uuid4()),
        'nova': str(uuid.uuid4()),
        'juniper': str(uuid.uuid4()),
        'sloane': str(uuid.uuid4())
    }
    
    # Create system user for global personalities
    op.execute(f"""
        INSERT INTO users (id, external_user_id, display_name, created_at, last_active)
        VALUES (
            '{system_user_id}',
            'system',
            'System User (Global Personalities)',
            NOW(),
            NOW()
        )
        ON CONFLICT (external_user_id) DO NOTHING
    """)
    
    print("✅ Created system user for global personalities")
    
    # Create 8 global personality placeholders
    # These are minimal records - the actual persona comes from Supabase
    personalities = [
        {
            'name': 'elara',
            'id': personality_ids['elara'],
            'archetype': 'wise_mentor',
            'description': 'Art enthusiast from Paris'
        },
        {
            'name': 'seraphina',
            'id': personality_ids['seraphina'],
            'archetype': 'supportive_friend',
            'description': 'Warm and caring companion'
        },
        {
            'name': 'isla',
            'id': personality_ids['isla'],
            'archetype': 'calm_therapist',
            'description': 'Patient and understanding listener'
        },
        {
            'name': 'lyra',
            'id': personality_ids['lyra'],
            'archetype': 'creative_partner',
            'description': 'Imaginative creative collaborator'
        },
        {
            'name': 'aria',
            'id': personality_ids['aria'],
            'archetype': 'enthusiastic_cheerleader',
            'description': 'Energetic and encouraging supporter'
        },
        {
            'name': 'nova',
            'id': personality_ids['nova'],
            'archetype': 'pragmatic_advisor',
            'description': 'Practical and straightforward advisor'
        },
        {
            'name': 'juniper',
            'id': personality_ids['juniper'],
            'archetype': 'curious_student',
            'description': 'Eager and inquisitive learner'
        },
        {
            'name': 'sloane',
            'id': personality_ids['sloane'],
            'archetype': 'professional_coach',
            'description': 'Results-focused professional coach'
        }
    ]
    
    for p in personalities:
        op.execute(f"""
            INSERT INTO personality_profiles (
                id, user_id, personality_name, archetype, relationship_type,
                humor_level, formality_level, enthusiasm_level, empathy_level,
                directness_level, curiosity_level, supportiveness_level, playfulness_level,
                custom_instructions, created_at, updated_at, version
            )
            VALUES (
                '{p['id']}',
                '{system_user_id}',
                '{p['name']}',
                '{p['archetype']}',
                'friend',
                5, 5, 7, 8, 5, 7, 8, 6,
                'Global character - persona defined in Supabase',
                NOW(),
                NOW(),
                1
            )
            ON CONFLICT (user_id, personality_name) DO NOTHING
        """)
        
        print(f"✅ Created global personality: {p['name']} ({p['description']})")
    
    print("✅ All 8 global personalities created successfully!")


def downgrade():
    """Remove global personalities and system user."""
    
    # Delete global personalities
    op.execute("""
        DELETE FROM personality_profiles
        WHERE user_id IN (
            SELECT id FROM users WHERE external_user_id = 'system'
        )
    """)
    
    # Delete system user
    op.execute("""
        DELETE FROM users WHERE external_user_id = 'system'
    """)
    
    print("✅ Removed global personalities and system user")

