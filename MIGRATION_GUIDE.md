# Migration Guide: Adding Multi-User Support

This guide explains the changes made to add multi-user authentication and how to migrate.

## What Changed

### 1. Database Schema

**Added:**
- `users` table with external_user_id, email, display_name
- `user_id` foreign key in `conversations` table
- `title` field in `conversations` table
- Indexes for performance

**Migration:** `migrations/versions/002_add_users_and_multi_tenancy.py`

### 2. Authentication Layer

**New file:** `app/core/auth.py`

Provides:
- `get_current_user_id()` - Extract user from headers
- `verify_conversation_ownership()` - Security check
- `ensure_user_exists()` - Auto-create users
- API key validation helpers

### 3. API Changes

**All endpoints now require authentication:**
- `POST /chat` - Requires X-User-Id (or API key/JWT)
- `POST /conversation/reset` - Requires authentication + ownership verification
- `POST /memory/clear` - Requires authentication + ownership verification

**New endpoint:**
- `GET /conversations` - List all conversations for user

### 4. Service Layer Updates

**chat_service.py:**
- Added `user_id` parameter to `stream_chat()`
- User context passed through to memory layer

**vector_store.py:**
- Added `user_db_id` parameter for conversation creation
- Added `user_external_id` for security checks in queries
- Ownership verification in search operations

## Migration Steps

### Step 1: Backup Database

```bash
pg_dump ai_companion > backup_before_migration.sql
```

### Step 2: Update Code

```bash
cd "/home/bean12/Desktop/AI Service"
git pull  # or download updated files
```

### Step 3: Run Migration

```bash
# Apply migration
alembic upgrade head

# Verify migration
psql ai_companion -c "SELECT * FROM users;"
psql ai_companion -c "\d conversations"
```

Expected output:
- New `users` table exists
- `conversations` table has `user_id` and `title` columns
- Default user `'default_user'` created
- All existing conversations assigned to default user

### Step 4: Update Configuration

Add to `.env`:
```env
# Authentication
REQUIRE_AUTHENTICATION=true
JWT_SECRET_KEY=change-this-in-production-use-long-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Step 5: Test Authentication

```bash
# Test without auth (should fail)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
# Expected: 401 Unauthorized

# Test with auth (should succeed)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: testuser" \
  -d '{"message": "test"}'
# Expected: Streaming response
```

### Step 6: Update Client Applications

Update all API calls to include authentication header:

**Before:**
```python
response = requests.post(
    'http://localhost:8000/chat',
    json={'message': 'Hello'}
)
```

**After:**
```python
response = requests.post(
    'http://localhost:8000/chat',
    json={'message': 'Hello'},
    headers={'X-User-Id': 'alice'}  # Add this
)
```

## Rollback Plan

If you need to rollback:

```bash
# Rollback migration
alembic downgrade -1

# Restore from backup
psql ai_companion < backup_before_migration.sql
```

## Handling Existing Data

### Scenario 1: Single User System

If you've been testing with a single user:

```sql
-- Update default user to your actual user
UPDATE users 
SET external_user_id = 'your_actual_user_id',
    display_name = 'Your Name'
WHERE external_user_id = 'default_user';
```

### Scenario 2: Multiple Users (Manual Assignment)

If you need to assign conversations to specific users:

```sql
-- Create user
INSERT INTO users (id, external_user_id, display_name, created_at, last_active)
VALUES (
    gen_random_uuid(),
    'alice',
    'Alice Smith',
    now(),
    now()
);

-- Assign conversations
UPDATE conversations
SET user_id = (SELECT id FROM users WHERE external_user_id = 'alice')
WHERE id IN ('conv-id-1', 'conv-id-2', ...);
```

### Scenario 3: Clean Start

If you want to start fresh:

```sql
-- Clear all data
TRUNCATE TABLE messages, memories, conversations, users CASCADE;

-- Restart with new users
-- They will be created automatically on first API call
```

## Testing Checklist

- [ ] Migration completed successfully
- [ ] New tables created
- [ ] Existing conversations preserved
- [ ] Authentication required for all endpoints
- [ ] Users can only see their own conversations
- [ ] Users cannot access other users' conversations
- [ ] New conversations auto-create users
- [ ] List conversations endpoint works
- [ ] Memory retrieval filtered by user
- [ ] Client applications updated

## Common Issues

### Issue: Authentication always fails

**Solution:**
```bash
# Check auth is enabled
grep REQUIRE_AUTHENTICATION .env

# Test with simple user ID
curl -H "X-User-Id: test" http://localhost:8000/health
```

### Issue: Can't access old conversations

**Problem:** Conversations assigned to wrong user

**Solution:**
```sql
-- Check conversation ownership
SELECT c.id, c.user_id, u.external_user_id 
FROM conversations c 
JOIN users u ON c.user_id = u.id;

-- Reassign if needed
UPDATE conversations 
SET user_id = (SELECT id FROM users WHERE external_user_id = 'correct_user')
WHERE id = 'your-conversation-id';
```

### Issue: Migration fails

**Error:** "Column user_id already exists"

**Solution:**
```bash
# Check current migration status
alembic current

# If stuck, manually set to revision 001
alembic stamp 001

# Try upgrade again
alembic upgrade head
```

## Performance Considerations

New indexes added for performance:
- `ix_users_external_user_id` - User lookup
- `ix_conversations_user_id` - User's conversations
- `ix_conversations_updated_at` - Recent conversations

Monitor query performance:
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE schemaname = 'public';

-- Analyze query plans
EXPLAIN ANALYZE 
SELECT * FROM conversations 
WHERE user_id = (SELECT id FROM users WHERE external_user_id = 'alice');
```

## Security Notes

- Default authentication uses simple `X-User-Id` header for development
- **Do not use in production** without proper JWT implementation
- Consider adding:
  - Rate limiting per user
  - API key management
  - User registration/verification
  - Password hashing if using password auth
  - Session management
  - Audit logging

## Support

If you encounter issues:

1. Check logs: `docker-compose logs -f ai-companion`
2. Verify migration: `alembic current`
3. Test database: `psql ai_companion -c "\dt"`
4. Review this guide and AUTHENTICATION.md

## Next Steps

After successful migration:

1. Update all client applications
2. Test multi-user isolation
3. Implement production authentication (JWT)
4. Add user management endpoints
5. Setup monitoring per user
6. Document authentication for your users

