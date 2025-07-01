"""
Google Text-to-Speech (gTTS) provider implementation.
Free, reliable, good quality for most content.
"""

import os
import tempfile
from typing import Dict
from pathlib import Path

from ..tts_engine import BaseTTSProvider, TTSRequest, TTSResult, TTSProvider


class GTTSProvider(BaseTTSProvider):
    """Google Text-to-Speech provider using gTTS library."""
    
    def __init__(self):
        super().__init__("Google TTS")
        self._gtts = None
        self._pygame = None
    
    def is_available(self) -> bool:
        """Check if gTTS is available."""
        if self._is_available is not None:
            return self._is_available
        
        try:
            import gtts
            self._gtts = gtts
            self._is_available = True
            self.logger.info("gTTS is available")
        except ImportError:
            self.logger.warning("gTTS not installed. Install with: pip install gtts")
            self._is_available = False
        
        return self._is_available
    
    def get_voices(self) -> Dict[str, str]:
        """Get available voices/languages for gTTS."""
        if not self.is_available():
            return {}
        
        # Common languages for TikTok content
        return {
            "en": "English (US)",
            "en-uk": "English (UK)", 
            "en-au": "English (Australia)",
            "en-ca": "English (Canada)",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese (Mandarin)"
        }
    
    def get_quality_score(self) -> float:
        """gTTS quality score."""
        return 0.75  # Good quality, natural sounding
    
    def get_max_text_length(self) -> int:
        """gTTS can handle long texts."""
        return 5000
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for gTTS."""
        # gTTS handles most text well, just basic cleanup
        processed = text.strip()
        
        # Remove excessive whitespace
        processed = " ".join(processed.split())
        
        # Ensure text ends with punctuation for better speech rhythm
        if processed and processed[-1] not in ".!?":
            processed += "."
        
        return processed
    
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Generate speech using gTTS."""
        if not self.is_available():
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.GTTS,
                duration=0.0,
                quality_score=0.0,
                error_message="gTTS not available"
            )
        
        if not self.validate_request(request):
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.GTTS,
                duration=0.0,
                quality_score=0.0,
                error_message="Invalid request parameters"
            )
        
        try:
            # Preprocess text
            processed_text = self.preprocess_text(request.text)
            
            # Set language/voice (default to English)
            lang = request.voice if request.voice in self.get_voices() else "en"
            
            # Create gTTS object
            tts = self._gtts.gTTS(
                text=processed_text,
                lang=lang,
                slow=False if request.speed >= 1.0 else True
            )
            
            # Generate output path
            if request.output_path:
                output_path = request.output_path
            else:
                # Create temporary file
                temp_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_tts"
                temp_dir.mkdir(exist_ok=True)
                output_path = temp_dir / f"gtts_{hash(processed_text)}.mp3"
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate audio
            tts.save(str(output_path))
            
            # Estimate duration
            duration = self.estimate_duration(processed_text, request.speed)
            
            # Apply speed adjustment if needed (would require additional processing)
            if request.speed != 1.0:
                output_path = self._adjust_speed(output_path, request.speed)
            
            return TTSResult(
                success=True,
                audio_path=output_path,
                provider_used=TTSProvider.GTTS,
                duration=duration,
                quality_score=self.get_quality_score(),
                metadata={
                    "language": lang,
                    "text_length": len(processed_text),
                    "original_text": request.text
                }
            )
            
        except Exception as e:
            self.logger.error(f"gTTS synthesis failed: {e}")
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.GTTS,
                duration=0.0,
                quality_score=0.0,
                error_message=str(e)
            )
    
    def _adjust_speed(self, audio_path: Path, speed: float) -> Path:
        """Adjust audio speed using ffmpeg or similar."""
        if speed == 1.0:
            return audio_path
        
        try:
            # Try to use ffmpeg for speed adjustment
            import subprocess
            
            output_path = audio_path.parent / f"{audio_path.stem}_speed_{speed}{audio_path.suffix}"
            
            cmd = [
                "ffmpeg", "-i", str(audio_path),
                "-filter:a", f"atempo={speed}",
                "-y", str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Remove original file
                audio_path.unlink()
                return output_path
            else:
                self.logger.warning(f"Speed adjustment failed: {result.stderr}")
                return audio_path
                
        except Exception as e:
            self.logger.warning(f"Could not adjust speed: {e}")
            return audio_path
    
    def get_language_from_voice(self, voice: str) -> str:
        """Map voice selection to gTTS language code."""
        voice_mapping = {
            "alloy": "en",
            "echo": "en-uk", 
            "fable": "en-au",
            "onyx": "en",
            "nova": "en-ca",
            "shimmer": "en"
        }
        return voice_mapping.get(voice, "en")