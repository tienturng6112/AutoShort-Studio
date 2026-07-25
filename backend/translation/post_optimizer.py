import re
import logging
from typing import Dict, Any

logger = logging.getLogger("PostTranslationOptimizer")

class PostTranslationOptimizer:
    """Cleans up translated text to ensure optimal Subtitle and TTS formatting."""
    
    @staticmethod
    def optimize(segment: Dict[str, Any]) -> Dict[str, Any]:
        """Runs heuristics to clean up translation text."""
        text = segment.get("text", "")
        
        # 1. Strip repetitive punctuation often hallucinated by LLMs
        # Ex: "....." -> "..."
        text = re.sub(r'\.{4,}', '...', text)
        # Ex: "!!!" -> "!"
        text = re.sub(r'!{2,}', '!', text)
        # Ex: "???" -> "?"
        text = re.sub(r'\?{2,}', '?', text)
        
        # 2. Fix awkward spacing around punctuation
        text = re.sub(r'\s+([,.!?])', r'\1', text)
        
        # 3. Strip quotes at the very beginning and very end (LLM hallucination)
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
            
        # 4. Strip extra whitespace
        text = text.strip()
        
        # Optionally, could do basic number normalization here, e.g. "100" -> "một trăm" for TTS, 
        # but modern TTS engines usually handle numbers nicely.
        
        segment["text"] = text
        return segment
