#!/usr/bin/env python3
"""Final comprehensive memory test for myuser123"""

import asyncio
import sys
sys.path.insert(0, '/home/bean12/Desktop/AI Service')

from sqlalchemy import select, text
from uuid import UUID
from app.core.database import AsyncSessionLocal
from app.models.database import UserModel, MemoryModel, ConversationModel
from app.utils.embeddings import EmbeddingGenerator
from app.repositories.vector_store import VectorStoreRepository
from app.core.config import settings

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

async def main():
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Final Memory System Test for myuser123{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    async with AsyncSessionLocal() as session:
        # 1. Find user
        print(f"{Colors.CYAN}1. Finding user...{Colors.RESET}")
        result = await session.execute(
            select(UserModel).where(UserModel.external_user_id == 'myuser123')
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"{Colors.RED}✗ User not found!{Colors.RESET}")
            return
        
        print(f"{Colors.GREEN}✓ Found user: {user.id}{Colors.RESET}")
        
        # 2. Count memories
        print(f"\n{Colors.CYAN}2. Counting memories...{Colors.RESET}")
        result = await session.execute(
            select(MemoryModel).where(MemoryModel.user_id == user.id)
        )
        memories = result.scalars().all()
        print(f"{Colors.GREEN}✓ User has {len(memories)} memories stored{Colors.RESET}")
        
        # Show sample memories
        if memories:
            print(f"{Colors.BLUE}Sample memories:{Colors.RESET}")
            for i, mem in enumerate(memories[:3], 1):
                print(f"  {i}. [{mem.importance:.2f}] {mem.content[:60]}...")
        
        # 3. Get conversation
        print(f"\n{Colors.CYAN}3. Finding conversation...{Colors.RESET}")
        if memories:
            conv_id = memories[0].conversation_id
            print(f"{Colors.GREEN}✓ Using conversation: {conv_id}{Colors.RESET}")
        else:
            print(f"{Colors.RED}✗ No memories to test with!{Colors.RESET}")
            return
        
        # 4. Test memory retrieval
        print(f"\n{Colors.CYAN}4. Testing memory retrieval...{Colors.RESET}")
        print(f"{Colors.BLUE}Config threshold: {settings.memory_similarity_threshold}{Colors.RESET}")
        
        # Generate embedding for test query
        embed_gen = EmbeddingGenerator()
        test_queries = [
            "What is my name?",
            "What do I like to do?",
            "Tell me about my job",
        ]
        
        vector_store = VectorStoreRepository(session)
        
        for query in test_queries:
            print(f"\n{Colors.YELLOW}Query: '{query}'{Colors.RESET}")
            query_embedding = embed_gen.generate_embedding(query)
            
            # Test with config threshold
            retrieved = await vector_store.search_similar(
                conversation_id=conv_id,
                query_embedding=query_embedding,
                top_k=5,
                min_similarity=settings.memory_similarity_threshold  # Use config value
            )
            
            if retrieved:
                print(f"{Colors.GREEN}✓ Retrieved {len(retrieved)} memories:{Colors.RESET}")
                for mem in retrieved:
                    print(f"    [{mem.similarity_score:.3f}] {mem.content[:50]}...")
            else:
                print(f"{Colors.RED}✗ No memories retrieved!{Colors.RESET}")
                
                # Try with lower threshold to see what's available
                retrieved_low = await vector_store.search_similar(
                    conversation_id=conv_id,
                    query_embedding=query_embedding,
                    top_k=5,
                    min_similarity=0.0
                )
                
                if retrieved_low:
                    print(f"{Colors.YELLOW}  (With threshold 0.0, would get {len(retrieved_low)} memories){Colors.RESET}")
                    best_score = max([m.similarity_score for m in retrieved_low])
                    print(f"{Colors.YELLOW}  Best similarity score: {best_score:.3f}{Colors.RESET}")
                    print(f"{Colors.YELLOW}  Config threshold: {settings.memory_similarity_threshold}{Colors.RESET}")
                    if best_score < settings.memory_similarity_threshold:
                        print(f"{Colors.RED}  → Threshold too high! Consider lowering to ~{best_score:.2f}{Colors.RESET}")
        
        # 5. Summary
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"Total Memories: {len(memories)}")
        print(f"Config Threshold: {settings.memory_similarity_threshold}")
        
        if retrieved:
            print(f"{Colors.GREEN}✓ Memory retrieval working!{Colors.RESET}\n")
        else:
            print(f"{Colors.RED}✗ Memory retrieval not working properly{Colors.RESET}")
            print(f"{Colors.YELLOW}Recommendation: Lower similarity threshold or improve embeddings{Colors.RESET}\n")

if __name__ == "__main__":
    asyncio.run(main())

