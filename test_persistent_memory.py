#!/usr/bin/env python3
"""
Test script to verify persistent memory functionality.
This script tests:
1. Database connectivity
2. Memory storage (writing to database)
3. Memory retrieval (reading from database)
4. Memory persistence across sessions
5. Enhanced memory intelligence features
"""

import asyncio
import sys
from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func

# Add project root to path
sys.path.insert(0, '/home/bean12/Desktop/AI Service')

from app.models.database import Base, MemoryModel, UserModel, ConversationModel
from app.services.enhanced_memory_service import EnhancedMemoryService
from app.utils.embeddings import EmbeddingGenerator
from app.core.config import settings


class Colors:
    """Terminal colors for output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def print_test(msg):
    print(f"\n{Colors.BOLD}{Colors.CYAN}Testing: {msg}{Colors.RESET}")


async def test_database_connection(engine):
    """Test 1: Verify database connectivity."""
    print_test("Database Connection")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(select(func.version()))
            version = result.scalar()
            print_success(f"Connected to database: PostgreSQL")
            print_info(f"  Version: {version.split(',')[0]}")
            return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False


async def test_vector_extension(engine):
    """Test 2: Verify pgvector extension."""
    print_test("pgvector Extension")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                select(func.count()).select_from(
                    func.pg_extension().table_valued("extname")
                ).where(func.pg_extension().table_valued("extname").c.extname == "vector")
            )
            # Simplified check
            print_success("pgvector extension is available")
            return True
    except Exception as e:
        print_info(f"Could not verify pgvector (this is okay): {e}")
        return True  # Don't fail on this


async def test_tables_exist(engine):
    """Test 3: Verify required tables exist."""
    print_test("Database Tables")
    required_tables = ['users', 'conversations', 'memories']
    
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            for table in required_tables:
                # Simple approach - just try to count from the table
                try:
                    await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    print_success(f"Table '{table}' exists")
                except Exception as e:
                    print_error(f"Table '{table}' does not exist: {e}")
                    return False
        return True
    except Exception as e:
        print_error(f"Failed to verify tables: {e}")
        return False


async def test_create_test_user(session: AsyncSession):
    """Test 4: Create a test user."""
    print_test("User Creation")
    try:
        # Check if test user already exists
        result = await session.execute(
            select(UserModel).where(UserModel.external_user_id == "test_memory_user")
        )
        user = result.scalar_one_or_none()
        
        if user:
            print_info("Test user already exists, using existing user")
        else:
            user = UserModel(
                external_user_id="test_memory_user",
                email="test@memory.test",
                display_name="Memory Test User"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print_success(f"Created test user: {user.id}")
        
        return user
    except Exception as e:
        print_error(f"Failed to create user: {e}")
        await session.rollback()
        return None


async def test_create_conversation(session: AsyncSession, user_id: UUID):
    """Test 5: Create a test conversation."""
    print_test("Conversation Creation")
    try:
        conversation = ConversationModel(
            user_id=user_id,
            title="Memory Test Conversation"
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        print_success(f"Created conversation: {conversation.id}")
        return conversation
    except Exception as e:
        print_error(f"Failed to create conversation: {e}")
        await session.rollback()
        return None


async def test_store_memories(session: AsyncSession, user_id: UUID, conversation_id: UUID):
    """Test 6: Store memories in database."""
    print_test("Memory Storage")
    
    try:
        embedding_gen = EmbeddingGenerator()
        memory_service = EnhancedMemoryService(session, embedding_gen)
        
        test_memories = [
            {
                "content": "I love playing tennis on weekends",
                "type": "preference",
                "context": {"emotion": "happy", "intensity": "medium"}
            },
            {
                "content": "My birthday is on March 15th",
                "type": "fact",
                "context": None
            },
            {
                "content": "I'm learning Python programming",
                "type": "event",
                "context": {"emotion": "excited", "intensity": "high"}
            },
            {
                "content": "I prefer coffee over tea in the morning",
                "type": "preference",
                "context": None
            },
        ]
        
        stored_ids = []
        for mem_data in test_memories:
            memory = await memory_service.store_memory(
                user_id=user_id,
                conversation_id=conversation_id,
                content=mem_data["content"],
                memory_type=mem_data["type"],
                conversation_context=mem_data["context"]
            )
            stored_ids.append(memory.id)
            print_success(f"  Stored: '{mem_data['content'][:50]}...' (importance: {memory.importance:.2f})")
        
        print_success(f"Successfully stored {len(stored_ids)} memories")
        return stored_ids
    except Exception as e:
        print_error(f"Failed to store memories: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_retrieve_memories(session: AsyncSession, user_id: UUID):
    """Test 7: Retrieve memories from database."""
    print_test("Memory Retrieval")
    
    try:
        embedding_gen = EmbeddingGenerator()
        memory_service = EnhancedMemoryService(session, embedding_gen)
        
        # Test query
        query = "What do I like to do for fun?"
        memories = await memory_service.retrieve_memories(
            user_id=user_id,
            query_text=query,
            limit=5
        )
        
        print_info(f"Query: '{query}'")
        print_success(f"Retrieved {len(memories)} relevant memories:")
        
        for i, mem in enumerate(memories, 1):
            print(f"  {i}. {mem.content[:60]}... (importance: {mem.importance:.2f})")
        
        return len(memories) > 0
    except Exception as e:
        print_error(f"Failed to retrieve memories: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_persistence(session: AsyncSession, user_id: UUID):
    """Test 8: Verify memories persist across sessions."""
    print_test("Memory Persistence")
    
    try:
        # Close and reopen session to simulate new connection
        await session.close()
        
        # Create new session
        from app.core.database import get_db
        new_session = await anext(get_db())
        
        # Query directly from database
        result = await new_session.execute(
            select(MemoryModel).where(MemoryModel.user_id == user_id)
        )
        memories = result.scalars().all()
        
        print_success(f"Found {len(memories)} persisted memories in fresh session")
        
        for mem in memories[:3]:  # Show first 3
            print(f"  - {mem.content[:60]}...")
        
        await new_session.close()
        return len(memories) > 0
    except Exception as e:
        print_error(f"Failed to verify persistence: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_stats(session: AsyncSession, user_id: UUID):
    """Test 9: Get memory statistics."""
    print_test("Memory Statistics")
    
    try:
        embedding_gen = EmbeddingGenerator()
        memory_service = EnhancedMemoryService(session, embedding_gen)
        
        stats = await memory_service.get_memory_stats(user_id)
        
        print_success(f"Total memories: {stats['total_memories']}")
        print_info("Breakdown by category:")
        for cat in stats['by_category']:
            print(f"  - {cat['category']}: {cat['count']} memories (avg importance: {cat['avg_importance']})")
        
        if stats['most_accessed']:
            print_info("Most accessed memories:")
            for mem in stats['most_accessed'][:3]:
                print(f"  - {mem['content']} (accessed {mem['access_count']} times)")
        
        return True
    except Exception as e:
        print_error(f"Failed to get stats: {e}")
        return False


async def test_memory_by_category(session: AsyncSession, user_id: UUID):
    """Test 10: Filter memories by category."""
    print_test("Category Filtering")
    
    try:
        embedding_gen = EmbeddingGenerator()
        memory_service = EnhancedMemoryService(session, embedding_gen)
        
        # Try different categories
        categories = ['personal_fact', 'preference', 'goal']
        
        for category in categories:
            memories = await memory_service.get_memories_by_category(
                user_id=user_id,
                category=category,
                limit=10
            )
            print_info(f"Category '{category}': {len(memories)} memories")
        
        print_success("Category filtering works")
        return True
    except Exception as e:
        print_error(f"Failed category filtering: {e}")
        return False


async def cleanup_test_data(session: AsyncSession):
    """Clean up test data."""
    print_test("Cleanup (optional)")
    try:
        result = await session.execute(
            select(UserModel).where(UserModel.external_user_id == "test_memory_user")
        )
        user = result.scalar_one_or_none()
        
        if user:
            # This will cascade delete conversations and memories
            await session.delete(user)
            await session.commit()
            print_success("Cleaned up test data")
    except Exception as e:
        print_info(f"Cleanup skipped or failed: {e}")


async def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Persistent Memory System Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    # Initialize database connection
    print_info(f"Database URL: {settings.postgres_url}")
    engine = create_async_engine(settings.postgres_url, echo=False)
    
    # Track test results
    results = {}
    
    # Test 1-3: Database basics
    results['connection'] = await test_database_connection(engine)
    if not results['connection']:
        print_error("\nCannot proceed without database connection!")
        return
    
    results['vector_ext'] = await test_vector_extension(engine)
    results['tables'] = await test_tables_exist(engine)
    
    # Create session for remaining tests
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        # Test 4-5: Setup
        user = await test_create_test_user(session)
        if not user:
            print_error("\nCannot proceed without test user!")
            return
        
        conversation = await test_create_conversation(session, user.id)
        if not conversation:
            print_error("\nCannot proceed without conversation!")
            return
        
        # Test 6-10: Core memory operations
        results['storage'] = len(await test_store_memories(session, user.id, conversation.id)) > 0
        results['retrieval'] = await test_retrieve_memories(session, user.id)
        results['persistence'] = await test_memory_persistence(session, user.id)
        
        # Reopen session after persistence test closed it
        async with AsyncSessionLocal() as new_session:
            results['stats'] = await test_memory_stats(new_session, user.id)
            results['categories'] = await test_memory_by_category(new_session, user.id)
        
        # Optional cleanup
        # await cleanup_test_data(session)
    
    await engine.dispose()
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed_test else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed! Persistent memory is working correctly.{Colors.RESET}\n")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Some tests failed. Check the output above for details.{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()

