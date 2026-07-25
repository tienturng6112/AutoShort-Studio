from typing import Dict, List, Optional

class Conversation:
    """Domain model representing a multi-turn chat session with role-based messages."""
    
    def __init__(self, system_message: Optional[str] = None) -> None:
        self.system_message: Optional[str] = system_message
        self._history: List[Dict[str, str]] = []
        if system_message:
            self._history.append({"role": "system", "content": system_message})

    def add_user_message(self, content: str) -> None:
        """Adds a user query message to the chat history.
        
        Args:
            content (str): User query text.
        """
        self._history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Adds an AI assistant completion message to the chat history.
        
        Args:
            content (str): Assistant completion text.
        """
        self._history.append({"role": "assistant", "content": content})

    def add_message(self, role: str, content: str) -> None:
        """Adds an arbitrary role message to the chat history.
        
        Args:
            role (str): Role identifier (e.g., user, assistant, system).
            content (str): Message content.
        """
        self._history.append({"role": role, "content": content})

    def get_history(self) -> List[Dict[str, str]]:
        """Returns the chronological list of messages in this conversation.
        
        Returns:
            List[Dict[str, str]]: List of role/content dictionaries.
        """
        return self._history

    def reset(self) -> None:
        """Clears all conversation messages, retaining only the system message if set."""
        self._history.clear()
        if self.system_message:
            self._history.append({"role": "system", "content": self.system_message})
