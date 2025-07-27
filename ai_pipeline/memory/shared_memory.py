"""
Shared Memory System for LangChain Multi-Agent Architecture
Enables communication and state sharing between specialized agents.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class MemoryEntry:
    """Individual memory entry with metadata"""
    id: str
    agent_id: str
    content: Dict[str, Any]
    memory_type: str
    timestamp: datetime
    expires_at: Optional[datetime] = None
    tags: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'content': self.content,
            'memory_type': self.memory_type,
            'timestamp': self.timestamp.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'tags': self.tags or []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            agent_id=data['agent_id'],
            content=data['content'],
            memory_type=data['memory_type'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
            tags=data.get('tags', [])
        )

class SharedAgentMemory:
    """
    Shared memory system for multi-agent coordination
    
    Features:
    - Cross-agent state sharing
    - Persistent memory storage
    - Memory expiration and cleanup
    - Event-based notifications
    - Memory search and filtering
    """
    
    def __init__(self, memory_file: str = "shared_agent_memory.json"):
        self.logger = logging.getLogger(__name__)
        self.memory_file = Path(memory_file)
        self.memories: Dict[str, MemoryEntry] = {}
        self.subscribers: Dict[str, List[callable]] = {}
        self._lock = asyncio.Lock()
        
        # Load existing memories
        self._load_memories()
        
        self.logger.info("SharedAgentMemory initialized")
    
    async def initialize(self):
        """Initialize method for test compatibility - initialization already done in __init__"""
        # Memory system is already initialized in __init__, this is just for test compatibility
        pass
    
    def _load_memories(self):
        """Load memories from persistent storage"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    
                for memory_data in data.get('memories', []):
                    memory = MemoryEntry.from_dict(memory_data)
                    # Skip expired memories
                    if memory.expires_at and memory.expires_at < datetime.now():
                        continue
                    self.memories[memory.id] = memory
                
                self.logger.info(f"Loaded {len(self.memories)} memories from storage")
        except Exception as e:
            self.logger.error(f"Failed to load memories: {str(e)}")
    
    async def save_state(self):
        """Save current memory state to persistent storage"""
        try:
            async with self._lock:
                # Clean up expired memories first
                await self._cleanup_expired_memories()
                
                data = {
                    'memories': [memory.to_dict() for memory in self.memories.values()],
                    'saved_at': datetime.now().isoformat()
                }
                
                with open(self.memory_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.logger.info(f"Saved {len(self.memories)} memories to storage")
        except Exception as e:
            self.logger.error(f"Failed to save memories: {str(e)}")
    
    async def store_memory(
        self,
        agent_id: str,
        content: Dict[str, Any],
        memory_type: str,
        memory_id: Optional[str] = None,
        expires_in: Optional[timedelta] = None,
        tags: List[str] = None
    ) -> str:
        """
        Store a memory entry
        
        Args:
            agent_id: ID of the agent storing the memory
            content: Memory content
            memory_type: Type of memory (e.g., 'data_collection', 'analysis_result')
            memory_id: Optional custom memory ID
            expires_in: Optional expiration time
            tags: Optional tags for categorization
        
        Returns:
            Memory ID
        """
        async with self._lock:
            if not memory_id:
                memory_id = f"{agent_id}_{memory_type}_{datetime.now().timestamp()}"
            
            expires_at = None
            if expires_in:
                expires_at = datetime.now() + expires_in
            
            memory = MemoryEntry(
                id=memory_id,
                agent_id=agent_id,
                content=content,
                memory_type=memory_type,
                timestamp=datetime.now(),
                expires_at=expires_at,
                tags=tags or []
            )
            
            self.memories[memory_id] = memory
            
            # Notify subscribers
            await self._notify_subscribers('memory_stored', memory)
            
            self.logger.info(f"Stored memory {memory_id} from agent {agent_id}")
            return memory_id
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory by ID"""
        async with self._lock:
            memory = self.memories.get(memory_id)
            if memory and memory.expires_at and memory.expires_at < datetime.now():
                # Memory has expired
                del self.memories[memory_id]
                return None
            return memory
    
    async def get_memories_by_agent(self, agent_id: str) -> List[MemoryEntry]:
        """Get all memories from a specific agent"""
        async with self._lock:
            return [
                memory for memory in self.memories.values()
                if memory.agent_id == agent_id and (
                    not memory.expires_at or memory.expires_at > datetime.now()
                )
            ]
    
    async def get_memories_by_type(self, memory_type: str) -> List[MemoryEntry]:
        """Get all memories of a specific type"""
        async with self._lock:
            return [
                memory for memory in self.memories.values()
                if memory.memory_type == memory_type and (
                    not memory.expires_at or memory.expires_at > datetime.now()
                )
            ]
    
    async def search_memories(
        self,
        query: str = None,
        agent_id: str = None,
        memory_type: str = None,
        tags: List[str] = None,
        since: datetime = None
    ) -> List[MemoryEntry]:
        """
        Search memories with various filters
        
        Args:
            query: Text search in memory content
            agent_id: Filter by agent ID
            memory_type: Filter by memory type
            tags: Filter by tags (any match)
            since: Filter by timestamp
        
        Returns:
            List of matching memories
        """
        async with self._lock:
            results = []
            
            for memory in self.memories.values():
                # Skip expired memories
                if memory.expires_at and memory.expires_at < datetime.now():
                    continue
                
                # Apply filters
                if agent_id and memory.agent_id != agent_id:
                    continue
                
                if memory_type and memory.memory_type != memory_type:
                    continue
                
                if since and memory.timestamp < since:
                    continue
                
                if tags and not any(tag in (memory.tags or []) for tag in tags):
                    continue
                
                if query:
                    # Simple text search in content
                    content_str = json.dumps(memory.content).lower()
                    if query.lower() not in content_str:
                        continue
                
                results.append(memory)
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda m: m.timestamp, reverse=True)
            return results
    
    async def update_memory(self, memory_id: str, content: Dict[str, Any]) -> bool:
        """Update existing memory content"""
        async with self._lock:
            if memory_id in self.memories:
                self.memories[memory_id].content.update(content)
                self.memories[memory_id].timestamp = datetime.now()
                
                # Notify subscribers
                await self._notify_subscribers('memory_updated', self.memories[memory_id])
                
                self.logger.info(f"Updated memory {memory_id}")
                return True
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry"""
        async with self._lock:
            if memory_id in self.memories:
                memory = self.memories.pop(memory_id)
                
                # Notify subscribers
                await self._notify_subscribers('memory_deleted', memory)
                
                self.logger.info(f"Deleted memory {memory_id}")
                return True
            return False
    
    def subscribe(self, event_type: str, callback: callable):
        """Subscribe to memory events"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    async def _notify_subscribers(self, event_type: str, memory: MemoryEntry):
        """Notify subscribers of memory events"""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, memory)
                    else:
                        callback(event_type, memory)
                except Exception as e:
                    self.logger.error(f"Error in memory subscriber callback: {str(e)}")
    
    async def _cleanup_expired_memories(self):
        """Remove expired memories"""
        now = datetime.now()
        expired_ids = [
            memory_id for memory_id, memory in self.memories.items()
            if memory.expires_at and memory.expires_at < now
        ]
        
        for memory_id in expired_ids:
            del self.memories[memory_id]
        
        if expired_ids:
            self.logger.info(f"Cleaned up {len(expired_ids)} expired memories")
    
    def get_all_memories(self) -> List[MemoryEntry]:
        """Get all non-expired memories"""
        now = datetime.now()
        return [
            memory for memory in self.memories.values()
            if not memory.expires_at or memory.expires_at > now
        ]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        now = datetime.now()
        active_memories = [
            memory for memory in self.memories.values()
            if not memory.expires_at or memory.expires_at > now
        ]
        
        agent_counts = {}
        type_counts = {}
        
        for memory in active_memories:
            agent_counts[memory.agent_id] = agent_counts.get(memory.agent_id, 0) + 1
            type_counts[memory.memory_type] = type_counts.get(memory.memory_type, 0) + 1
        
        return {
            'total_memories': len(active_memories),
            'memories_by_agent': agent_counts,
            'memories_by_type': type_counts,
            'oldest_memory': min((m.timestamp for m in active_memories), default=None),
            'newest_memory': max((m.timestamp for m in active_memories), default=None)
        }
