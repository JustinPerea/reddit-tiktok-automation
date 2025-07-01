"""
pyttsx3 provider implementation.
Offline TTS using system voices - fastest fallback option.
"""

import tempfile
from typing import Dict
from pathlib import Path

from ..tts_engine import BaseTTSProvider, TTSRequest, TTSResult, TTSProvider


class PyTTSx3Provider(BaseTTSProvider):
    """System TTS provider using pyttsx3."""
    
    def __init__(self):
        super().__init__("System TTS")
        self._pyttsx3 = None
        self._engine = None
    
    def is_available(self) -> bool:
        """Check if pyttsx3 is available."""
        if self._is_available is not None:
            return self._is_available
        
        try:
            import pyttsx3
            self._pyttsx3 = pyttsx3
            
            # Test engine initialization
            engine = pyttsx3.init()
            engine.stop()
            
            self._is_available = True
            self.logger.info("pyttsx3 is available")
        except Exception as e:
            self.logger.warning(f"pyttsx3 not available: {e}")
            self._is_available = False
        
        return self._is_available
    
    def get_voices(self) -> Dict[str, str]:
        """Get available system voices."""
        if not self.is_available():
            return {}
        
        try:
            engine = self._pyttsx3.init()
            voices = engine.getProperty('voices')
            
            voice_dict = {}
            for i, voice in enumerate(voices):
                # Use voice ID or name
                voice_id = voice.id if hasattr(voice, 'id') else f"voice_{i}"
                voice_name = voice.name if hasattr(voice, 'name') else f"Voice {i}"
                voice_dict[voice_id] = voice_name
            
            engine.stop()
            return voice_dict
            
        except Exception as e:
            self.logger.error(f"Could not get voices: {e}")
            return {"default": "Default Voice"}
    
    def get_quality_score(self) -> float:
        """pyttsx3 quality score."""
        return 0.5  # Basic quality, robotic but functional
    
    def get_max_text_length(self) -> int:
        """pyttsx3 can handle reasonable text lengths."""
        return 3000
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for pyttsx3."""
        processed = text.strip()
        
        # Remove excessive punctuation that might confuse system TTS
        processed = processed.replace("...", " pause ")
        processed = processed.replace("—", " - ")
        
        # Ensure proper sentence endings
        if processed and processed[-1] not in ".!?":
            processed += "."
        
        return processed
    
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Generate speech using pyttsx3."""
        if not self.is_available():
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.PYTTSX3,
                duration=0.0,
                quality_score=0.0,
                error_message="pyttsx3 not available"
            )
        
        if not self.validate_request(request):
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.PYTTSX3,
                duration=0.0,
                quality_score=0.0,
                error_message="Invalid request parameters"
            )
        
        try:
            # Initialize engine
            engine = self._pyttsx3.init()
            
            # Set properties
            if request.speed != 1.0:
                # pyttsx3 rate is words per minute, adjust accordingly
                current_rate = engine.getProperty('rate')
                new_rate = int(current_rate * request.speed)
                engine.setProperty('rate', new_rate)
            
            # Set voice if specified
            available_voices = self.get_voices()
            if request.voice and request.voice in available_voices:
                engine.setProperty('voice', request.voice)
            
            # Preprocess text
            processed_text = self.preprocess_text(request.text)
            
            # Generate output path
            if request.output_path:
                output_path = request.output_path
            else:
                temp_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_tts"
                temp_dir.mkdir(exist_ok=True)
                output_path = temp_dir / f"pyttsx3_{hash(processed_text)}.wav"
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            engine.save_to_file(processed_text, str(output_path))
            engine.runAndWait()
            engine.stop()
            
            # Estimate duration
            duration = self.estimate_duration(processed_text, request.speed)
            
            return TTSResult(
                success=True,
                audio_path=output_path,
                provider_used=TTSProvider.PYTTSX3,
                duration=duration,
                quality_score=self.get_quality_score(),
                metadata={
                    "voice_used": request.voice,
                    "text_length": len(processed_text),
                    "original_text": request.text,
                    "speed": request.speed
                }
            )
            
        except Exception as e:
            self.logger.error(f"pyttsx3 synthesis failed: {e}")
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.PYTTSX3,
                duration=0.0,
                quality_score=0.0,
                error_message=str(e)
            )
    
    def get_voice_by_gender(self, gender: str = "female") -> str:
        """Get a voice by gender preference."""
        voices = self.get_voices()
        
        # Simple heuristic - look for gender indicators in voice names
        for voice_id, voice_name in voices.items():
            name_lower = voice_name.lower()
            if gender.lower() == "female" and any(word in name_lower for word in ["female", "woman", "zira", "hazel"]):
                return voice_id
            elif gender.lower() == "male" and any(word in name_lower for word in ["male", "man", "david", "mark"]):
                return voice_id
        
        # Return first available voice as fallback
        return list(voices.keys())[0] if voices else "default"