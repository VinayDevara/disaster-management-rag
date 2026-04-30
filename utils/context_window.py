"""
context_window.py - 10-Message Conversation Context Manager

Manages a fixed-size conversation context window for LLM interactions.
Features:
- FIFO eviction policy (oldest messages removed first)
- Thread-safe operations with fine-grained locking
- Optional persistence to JSON file
- Metadata tracking (timestamps, tokens, etc.)
"""

from collections import deque
from typing import Dict, List, Optional
from datetime import datetime
import threading
import json
import os


class ContextWindow:
    """
    Manages a fixed-size conversation context window for LLM interactions.
    
    Features:
    - FIFO eviction policy (oldest messages removed first)
    - Thread-safe operations with fine-grained locking
    - Optional persistence to JSON file
    - Metadata tracking (timestamps, tokens, etc.)
    """
    
    def __init__(
        self, 
        max_size: int = 10, 
        persist_path: Optional[str] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize context window.
        
        Args:
            max_size: Maximum number of messages (default 10)
            persist_path: Path to JSON file for persistence (optional)
            system_prompt: Custom system prompt (optional)
        """
        if max_size < 2:
            raise ValueError("max_size must be at least 2")
        
        self.max_size = max_size
        self.persist_path = persist_path
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Thread-safe message storage
        self.messages = deque(maxlen=max_size)
        self.lock = threading.Lock()
        
        # Load persisted history
        if persist_path and os.path.exists(persist_path):
            self._load_from_disk()
    
    def add_message(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a message to the context window.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata dictionary
        
        Raises:
            ValueError: If role is not 'user' or 'assistant'
        """
        if role not in ['user', 'assistant']:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        with self.lock:
            self.messages.append(message)
        
        # Persist asynchronously (non-blocking)
        if self.persist_path:
            self._save_to_disk()
    
    def get_messages(
        self, 
        include_system: bool = True,
        max_messages: Optional[int] = None
    ) -> List[Dict]:
        """
        Get messages formatted for LLM API.
        
        Args:
            include_system: Whether to prepend system prompt
            max_messages: Limit number of messages (default: all)
        
        Returns:
            List of message dictionaries in LLM API format
        """
        with self.lock:
            # Get copy to avoid holding lock during formatting
            messages = list(self.messages)
        
        # Limit messages if requested
        if max_messages:
            messages = messages[-max_messages:]
        
        # Format for LLM (remove timestamps/metadata)
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Prepend system prompt
        if include_system:
            system_msg = {
                "role": "system",
                "content": self.system_prompt
            }
            formatted.insert(0, system_msg)
        
        return formatted
    
    def get_raw_messages(self) -> List[Dict]:
        """
        Get raw messages with all metadata.
        
        Returns:
            List of complete message dictionaries
        """
        with self.lock:
            return list(self.messages)
    
    def clear(self) -> None:
        """Clear all messages from context window."""
        with self.lock:
            self.messages.clear()
        
        if self.persist_path:
            self._save_to_disk()
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of context window.
        
        Returns:
            Dictionary with statistics
        """
        with self.lock:
            messages = list(self.messages)
        
        if not messages:
            return {
                "message_count": 0,
                "max_size": self.max_size,
                "user_messages": 0,
                "assistant_messages": 0,
                "oldest_message": None,
                "newest_message": None,
                "estimated_tokens": 0
            }
        
        user_count = sum(1 for m in messages if m["role"] == "user")
        assistant_count = sum(1 for m in messages if m["role"] == "assistant")
        
        # Rough token estimation (4 chars per token)
        total_chars = sum(len(m["content"]) for m in messages)
        estimated_tokens = total_chars // 4
        
        return {
            "message_count": len(messages),
            "max_size": self.max_size,
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "oldest_message": messages[0]["timestamp"],
            "newest_message": messages[-1]["timestamp"],
            "estimated_tokens": estimated_tokens
        }
    
    def _default_system_prompt(self) -> str:
        """Generate default system prompt."""
        return """You are an intelligent assistant for a disaster management system.

You have access to:
- Aircraft tracking data (ADS-B)
- Weather event information
- Natural disaster data

Provide accurate, contextual responses based on the conversation history.
Reference previous queries and answers when relevant.
Be concise but thorough."""
    
    def _save_to_disk(self) -> None:
        """
        Persist conversation to disk (non-blocking).
        
        Note: Errors are logged but not raised to avoid disrupting operations.
        """
        if not self.persist_path:
            return
        
        try:
            # Get snapshot without holding lock
            with self.lock:
                snapshot = list(self.messages)
            
            # Write to disk
            os.makedirs(os.path.dirname(self.persist_path) or '.', exist_ok=True)
            with open(self.persist_path, 'w') as f:
                json.dump(snapshot, f, indent=2)
        
        except Exception as e:
            print(f"Warning: Failed to persist context to {self.persist_path}: {e}")
    
    def _load_from_disk(self) -> None:
        """
        Load persisted conversation from disk.
        
        Note: Silently ignores missing or corrupted files.
        """
        if not self.persist_path or not os.path.exists(self.persist_path):
            return
        
        try:
            with open(self.persist_path, 'r') as f:
                messages = json.load(f)
            
            # Validate and load messages
            with self.lock:
                for msg in messages[-self.max_size:]:
                    if self._validate_message(msg):
                        self.messages.append(msg)
        
        except Exception as e:
            print(f"Warning: Failed to load context from {self.persist_path}: {e}")
    
    def _validate_message(self, msg: Dict) -> bool:
        """
        Validate message structure.
        
        Args:
            msg: Message dictionary to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = {"role", "content", "timestamp"}
        return (
            isinstance(msg, dict) and
            required_keys.issubset(msg.keys()) and
            msg["role"] in ["user", "assistant"]
        )


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    
    Args:
        text: Input text
    
    Returns:
        Estimated token count
    """
    # Rough estimation: ~4 characters per token
    return len(text) // 4


def format_conversation_for_display(messages: List[Dict]) -> str:
    """
    Format conversation for human-readable display.
    
    Args:
        messages: List of message dictionaries
    
    Returns:
        Formatted conversation string
    """
    lines = []
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]
        timestamp = msg.get("timestamp", "")
        
        lines.append(f"[{timestamp}] {role}:")
        lines.append(f"  {content}")
        lines.append("")
    
    return "\n".join(lines)


def truncate_message(content: str, max_length: int = 500) -> str:
    """
    Truncate message content if too long.
    
    Args:
        content: Original content
        max_length: Maximum length
    
    Returns:
        Truncated content with ellipsis if needed
    """
    if len(content) <= max_length:
        return content
    
    return content[:max_length-3] + "..."
