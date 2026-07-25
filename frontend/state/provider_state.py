from PySide6.QtCore import QObject, Signal

class ProviderState(QObject):
    """Single source of truth for all provider state across the application."""
    
    # Signals
    llm_provider_changed = Signal(str)
    translation_provider_changed = Signal(str)
    speech_provider_changed = Signal(str)
    model_changed = Signal(str, str)      # (domain, model_name)
    voice_changed = Signal(str)
    capabilities_changed = Signal(str)    # provider_id
    connection_status_changed = Signal(str, dict)  # (provider_id, status_dict)
    
    def __init__(self):
        super().__init__()
        self._llm_provider = ""
        self._translation_provider = "chatanywhere"
        self._speech_provider = "edge"
        self._models = {}           # {"llm": "gpt-4o-mini", "translation": "gpt-4o-mini", "speech": ""}
        self._voice = ""
        self._capabilities = {}     # {provider_id: {feature: bool}}
        self._connection_status = {}  # {provider_id: {"connected": bool, "latency_ms": int, ...}}
    
    # -- LLM --
    @property
    def llm_provider(self): 
        return self._llm_provider
        
    @llm_provider.setter
    def llm_provider(self, v):
        if self._llm_provider != v:
            self._llm_provider = v
            self.llm_provider_changed.emit(v)
    
    # -- Translation --
    @property
    def translation_provider(self): 
        return self._translation_provider
        
    @translation_provider.setter
    def translation_provider(self, v):
        if self._translation_provider != v:
            self._translation_provider = v
            self.translation_provider_changed.emit(v)
    
    # -- Speech --
    @property
    def speech_provider(self): 
        return self._speech_provider
        
    @speech_provider.setter
    def speech_provider(self, v):
        if self._speech_provider != v:
            self._speech_provider = v
            self.speech_provider_changed.emit(v)
    
    # -- Models --
    def set_model(self, domain: str, model: str):
        self._models[domain] = model
        self.model_changed.emit(domain, model)
        
    def get_model(self, domain: str) -> str:
        return self._models.get(domain, "")
    
    # -- Voice --
    @property
    def voice(self): 
        return self._voice
        
    @voice.setter
    def voice(self, v):
        if self._voice != v:
            self._voice = v
            self.voice_changed.emit(v)
    
    # -- Capabilities --
    def set_capabilities(self, provider_id: str, caps: dict):
        self._capabilities[provider_id] = caps
        self.capabilities_changed.emit(provider_id)
        
    def get_capabilities(self, provider_id: str) -> dict:
        return self._capabilities.get(provider_id, {})
    
    # -- Connection Status --
    def set_connection_status(self, provider_id: str, status: dict):
        self._connection_status[provider_id] = status
        self.connection_status_changed.emit(provider_id, status)
        
    def get_connection_status(self, provider_id: str) -> dict:
        return self._connection_status.get(provider_id, {})
