"""Domain models for memory management."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID


class MemoryType(str, Enum):
    """Types of memories that can be stored."""
    FACT = "fact"
    PREFERENCE = "preference"
    EVENT = "event"
    CONTEXT = "context"


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


@dataclass
class Memory:
    """Represents a long-term memory entry."""
    id: Optional[UUID]
    conversation_id: UUID
    content: str
    embedding: Optional[List[float]]
    memory_type: MemoryType
    importance: float  # 0.0 to 1.0
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    similarity_score: Optional[float] = None  # Set during retrieval


@dataclass
class ConversationSummary:
    """Represents a summary of a conversation."""
    conversation_id: UUID
    summary: str
    created_at: datetime
    updated_at: datetime

