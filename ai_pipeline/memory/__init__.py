"""
Shared Memory System for LangChain Multi-Agent Architecture

This module provides persistent, shared memory capabilities for multi-agent
coordination, enabling agents to:

- Share state and context across workflows
- Persist important information between sessions
- Subscribe to memory events for real-time coordination
- Search and filter memories by various criteria

The memory system is designed for production use with:
- Thread-safe operations
- Automatic cleanup of expired memories
- Event-based notifications
- Persistent storage
"""

from .shared_memory import SharedAgentMemory, MemoryEntry

__all__ = [
    'SharedAgentMemory',
    'MemoryEntry'
]
