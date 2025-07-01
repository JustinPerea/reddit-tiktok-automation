"""
Base TTS engine and provider interfaces for the hybrid system.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from loguru import logger


class TTSProvider(Enum):
    """Available TTS providers."""
    GTTS = "gtts"
    COQUI = "coqui"
    PYTTSX3 = "pyttsx3"
    EDGE_TTS = "edge_tts"
    FESTIVAL = "festival"


@dataclass
class TTSRequest:
    """TTS generation request."""
    text: str
    voice: str
    speed: float = 1.0
    pitch: float = 1.0
    emotion: str = "neutral"
    output_path: Path = None
    provider_preferences: list[TTSProvider] = None


@dataclass
class TTSResult:
    """TTS generation result."""
    success: bool
    audio_path: Optional[Path]
    provider_used: TTSProvider
    duration: float
    quality_score: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class BaseTTSProvider(ABC):
    """Base class for all TTS providers."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logger.bind(name=f"TTS_{name}")
        self._is_available = None
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available on the system."""
        pass
    
    @abstractmethod
    def get_voices(self) -> Dict[str, str]:
        """Get available voices for this provider."""
        pass
    
    @abstractmethod
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech from text."""
        pass
    
    @abstractmethod
    def get_quality_score(self) -> float:
        """Get quality rating for this provider (0.0-1.0)."""
        pass
    
    def validate_request(self, request: TTSRequest) -> bool:
        """Validate TTS request parameters."""
        if not request.text or not request.text.strip():
            return False
        
        if len(request.text) > self.get_max_text_length():
            return False
        
        available_voices = self.get_voices()
        if request.voice and request.voice not in available_voices:
            return False
        
        return True
    
    def get_max_text_length(self) -> int:
        """Get maximum text length supported by this provider."""
        return 5000  # Default limit
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for this specific provider."""
        # Basic preprocessing - can be overridden
        return text.strip()
    
    def estimate_duration(self, text: str, speed: float = 1.0) -> float:
        """Estimate audio duration in seconds."""
        # Rough estimation: ~150 words per minute at normal speed
        word_count = len(text.split())
        base_duration = (word_count / 150) * 60
        return base_duration / speed


class TTSEngine:
    """Main TTS engine that coordinates providers."""
    
    def __init__(self):
        self.providers: Dict[TTSProvider, BaseTTSProvider] = {}
        self.logger = logger.bind(name="TTSEngine")
        self._load_providers()
    
    def _load_providers(self):
        """Load and initialize all available TTS providers."""
        from .providers.gtts_provider import GTTSProvider
        from .providers.coqui_provider import CoquiProvider
        from .providers.pyttsx3_provider import PyTTSx3Provider
        from .providers.edge_tts_provider import EdgeTTSProvider
        
        # Initialize providers
        potential_providers = [
            (TTSProvider.GTTS, GTTSProvider),
            (TTSProvider.COQUI, CoquiProvider),
            (TTSProvider.PYTTSX3, PyTTSx3Provider),
            (TTSProvider.EDGE_TTS, EdgeTTSProvider),
        ]
        
        for provider_enum, provider_class in potential_providers:
            try:
                provider = provider_class()
                if provider.is_available():
                    self.providers[provider_enum] = provider
                    self.logger.info(f"Loaded TTS provider: {provider_enum.value}")
                else:
                    self.logger.warning(f"TTS provider not available: {provider_enum.value}")
            except Exception as e:
                self.logger.error(f"Failed to load TTS provider {provider_enum.value}: {e}")
    
    def get_available_providers(self) -> list[TTSProvider]:
        """Get list of currently available providers."""
        return list(self.providers.keys())
    
    def get_provider_info(self) -> Dict[TTSProvider, Dict[str, Any]]:
        """Get information about all available providers."""
        info = {}
        for provider_enum, provider in self.providers.items():
            info[provider_enum] = {
                "name": provider.name,
                "quality_score": provider.get_quality_score(),
                "voices": provider.get_voices(),
                "max_text_length": provider.get_max_text_length(),
                "available": provider.is_available()
            }
        return info
    
    def select_best_provider(self, request: TTSRequest) -> Optional[TTSProvider]:
        """Select the best provider for a given request."""
        if request.provider_preferences:
            # Try preferred providers first
            for preferred in request.provider_preferences:
                if preferred in self.providers:
                    provider = self.providers[preferred]
                    if provider.validate_request(request):
                        return preferred
        
        # Fallback to best available provider
        available_providers = [
            (provider_enum, provider) 
            for provider_enum, provider in self.providers.items()
            if provider.validate_request(request)
        ]
        
        if not available_providers:
            return None
        
        # Sort by quality score (descending)
        available_providers.sort(key=lambda x: x[1].get_quality_score(), reverse=True)
        return available_providers[0][0]
    
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Generate speech using the best available provider."""
        if not self.providers:
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=None,
                duration=0.0,
                quality_score=0.0,
                error_message="No TTS providers available"
            )
        
        # Select provider
        selected_provider_enum = self.select_best_provider(request)
        if not selected_provider_enum:
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=None,
                duration=0.0,
                quality_score=0.0,
                error_message="No suitable provider found for request"
            )
        
        # Generate speech
        provider = self.providers[selected_provider_enum]
        self.logger.info(f"Using TTS provider: {selected_provider_enum.value}")
        
        try:
            result = provider.synthesize(request)
            self.logger.info(f"TTS generation {'succeeded' if result.success else 'failed'}")
            return result
        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}")
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=selected_provider_enum,
                duration=0.0,
                quality_score=0.0,
                error_message=str(e)
            )
    
    def test_providers(self, test_text: str = "Hello, this is a test.") -> Dict[TTSProvider, TTSResult]:
        """Test all available providers with sample text."""
        results = {}
        
        for provider_enum, provider in self.providers.items():
            self.logger.info(f"Testing provider: {provider_enum.value}")
            
            test_request = TTSRequest(
                text=test_text,
                voice=list(provider.get_voices().keys())[0] if provider.get_voices() else "default"
            )
            
            try:
                result = provider.synthesize(test_request)
                results[provider_enum] = result
            except Exception as e:
                results[provider_enum] = TTSResult(
                    success=False,
                    audio_path=None,
                    provider_used=provider_enum,
                    duration=0.0,
                    quality_score=0.0,
                    error_message=str(e)
                )
        
        return results