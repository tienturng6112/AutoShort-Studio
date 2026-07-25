from typing import Dict, List, Union

class TokenCounter:
    """Calculates OpenAI-compatible token counts for input strings and conversation lists."""

    @classmethod
    def count_string_tokens(cls, text: str, model_name: str = "gpt-3.5-turbo") -> int:
        """Counts tokens in a text string.
        
        Args:
            text (str): Input text payload.
            model_name (str): OpenAI target model identifier.
            
        Returns:
            int: Measured token count.
        """
        if not text:
            return 0
        try:
            import tiktoken
            try:
                encoding = tiktoken.encoding_for_model(model_name)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            # Fallback estimation: 1 token ≈ 4 characters or 0.75 words
            char_count = len(text)
            word_count = len(text.split())
            return max(int(char_count / 4.0), int(word_count / 0.75), 1)

    @classmethod
    def count_conversation_tokens(cls, messages: List[Dict[str, str]], model_name: str = "gpt-3.5-turbo") -> int:
        """Counts tokens for a list of conversation messages formatted for chat completions.
        
        Args:
            messages (List[Dict[str, str]]): List of role/content dictionaries.
            model_name (str): OpenAI model identifier.
            
        Returns:
            int: Measured token count.
        """
        # OpenAI chat completions structure adds framing tokens per message
        tokens_per_message = 3
        tokens_per_name = 1
        
        total_tokens = 0
        for msg in messages:
            total_tokens += tokens_per_message
            for key, val in msg.items():
                total_tokens += cls.count_string_tokens(val, model_name)
                if key == "name":
                    total_tokens += tokens_per_name
        total_tokens += 3  # Assistant reply framing tokens
        return total_tokens
