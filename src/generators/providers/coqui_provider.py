"""
Coqui TTS provider implementation.
High-quality open-source TTS with voice cloning capabilities.
"""

import tempfile
from typing import Dict, Optional
from pathlib import Path

from ..tts_engine import BaseTTSProvider, TTSRequest, TTSResult, TTSProvider


class CoquiProvider(BaseTTSProvider):
    """Coqui TTS provider for high-quality local synthesis."""
    
    def __init__(self):
        super().__init__("Coqui TTS")
        self._tts = None
        self._model_loaded = False
        self._current_model = None
    
    def is_available(self) -> bool:
        """Check if Coqui TTS is available."""
        if self._is_available is not None:
            return self._is_available
        
        try:
            from TTS.api import TTS
            self._tts_class = TTS
            self._is_available = True
            self.logger.info("Coqui TTS is available")
        except ImportError:
            self.logger.warning("Coqui TTS not installed. Install with: pip install TTS")
            self._is_available = False
        
        return self._is_available
    
    def get_voices(self) -> Dict[str, str]:
        """Get available Coqui TTS models/voices."""
        if not self.is_available():
            return {}
        
        # Return commonly available models
        # Note: In production, you might want to dynamically list available models
        return {
            "tts_models/en/ljspeech/tacotron2-DDC": "LJSpeech Tacotron2 (Female, English)",
            "tts_models/en/ljspeech/glow-tts": "LJSpeech GlowTTS (Female, English)",
            "tts_models/en/ljspeech/speedy-speech": "LJSpeech SpeedySpeech (Female, English)",
            "tts_models/en/vctk/vits": "VCTK VITS (Multi-speaker, English)",
            "tts_models/en/sam/tacotron-DDC": "SAM Tacotron (Male, English)",
            "tts_models/multilingual/multi-dataset/your_tts": "YourTTS (Multilingual)",
        }
    
    def get_quality_score(self) -> float:
        """Coqui TTS quality score."""
        return 0.85  # Very high quality, especially with proper models
    
    def get_max_text_length(self) -> int:
        """Coqui TTS can handle very long texts."""
        return 10000
    
    def _load_model(self, model_name: str) -> bool:
        """Load a specific TTS model."""
        if self._current_model == model_name and self._model_loaded:
            return True
        
        try:
            self.logger.info(f"Loading Coqui TTS model: {model_name}")
            self._tts = self._tts_class(model_name=model_name, progress_bar=False)
            self._current_model = model_name
            self._model_loaded = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for Coqui TTS."""
        processed = text.strip()
        
        # Clean up text for better synthesis
        processed = processed.replace("—", " - ")
        processed = processed.replace("...", " pause ")
        
        # Ensure proper sentence endings
        if processed and processed[-1] not in ".!?":
            processed += "."
        
        return processed
    
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Generate speech using Coqui TTS."""
        if not self.is_available():
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.COQUI,
                duration=0.0,
                quality_score=0.0,
                error_message="Coqui TTS not available"
            )
        
        if not self.validate_request(request):
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.COQUI,
                duration=0.0,
                quality_score=0.0,
                error_message="Invalid request parameters"
            )
        
        try:
            # Select model/voice
            available_voices = self.get_voices()
            if request.voice and request.voice in available_voices:
                model_name = request.voice
            else:
                # Default to a good quality English model
                model_name = "tts_models/en/ljspeech/glow-tts"
            
            # Load model
            if not self._load_model(model_name):
                return TTSResult(
                    success=False,
                    audio_path=None,
                    provider_used=TTSProvider.COQUI,
                    duration=0.0,
                    quality_score=0.0,
                    error_message=f"Could not load model: {model_name}"
                )
            
            # Preprocess text
            processed_text = self.preprocess_text(request.text)
            
            # Generate output path
            if request.output_path:
                output_path = request.output_path
            else:
                temp_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_tts"
                temp_dir.mkdir(exist_ok=True)
                output_path = temp_dir / f"coqui_{hash(processed_text)}.wav"
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate speech
            if "multi-speaker" in model_name or "vctk" in model_name:
                # Multi-speaker model - use speaker selection
                speaker_name = self._get_speaker_for_emotion(request.emotion)
                self._tts.tts_to_file(
                    text=processed_text,
                    file_path=str(output_path),
                    speaker=speaker_name
                )
            else:
                # Single speaker model
                self._tts.tts_to_file(
                    text=processed_text,
                    file_path=str(output_path)
                )
            
            # Post-process for speed if needed
            if request.speed != 1.0:
                output_path = self._adjust_speed(output_path, request.speed)
            
            # Estimate duration
            duration = self.estimate_duration(processed_text, request.speed)
            
            return TTSResult(
                success=True,
                audio_path=output_path,
                provider_used=TTSProvider.COQUI,
                duration=duration,
                quality_score=self.get_quality_score(),
                metadata={
                    "model_used": model_name,
                    "text_length": len(processed_text),
                    "original_text": request.text,
                    "speed": request.speed,
                    "emotion": request.emotion
                }
            )
            
        except Exception as e:
            self.logger.error(f"Coqui TTS synthesis failed: {e}")
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.COQUI,
                duration=0.0,
                quality_score=0.0,
                error_message=str(e)
            )
    
    def _get_speaker_for_emotion(self, emotion: str) -> Optional[str]:
        """Select appropriate speaker for emotional content."""
        # This would be customized based on the specific multi-speaker model
        emotion_mapping = {
            "neutral": "p225",  # Clear female voice
            "happy": "p226",    # Cheerful voice
            "sad": "p227",      # Deeper, more somber
            "angry": "p228",    # More assertive
            "surprised": "p229", # Expressive
        }
        return emotion_mapping.get(emotion.lower(), "p225")
    
    def _adjust_speed(self, audio_path: Path, speed: float) -> Path:
        """Adjust audio speed using audio processing."""
        if speed == 1.0:
            return audio_path
        
        try:
            # Try using librosa for speed adjustment
            import librosa
            import soundfile as sf
            
            # Load audio
            y, sr = librosa.load(str(audio_path))
            
            # Adjust speed
            y_stretched = librosa.effects.time_stretch(y, rate=speed)
            
            # Save adjusted audio
            output_path = audio_path.parent / f"{audio_path.stem}_speed_{speed}.wav"
            sf.write(str(output_path), y_stretched, sr)
            
            # Remove original
            audio_path.unlink()
            return output_path
            
        except ImportError:
            self.logger.warning("librosa not available for speed adjustment")
            return audio_path
        except Exception as e:
            self.logger.warning(f"Speed adjustment failed: {e}")
            return audio_path
    
    def clone_voice(self, reference_audio: Path, text: str, output_path: Path) -> TTSResult:
        """Clone a voice from reference audio (advanced feature)."""
        if not self.is_available():
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.COQUI,
                duration=0.0,
                quality_score=0.0,
                error_message="Coqui TTS not available"
            )
        
        try:
            # Load YourTTS model for voice cloning
            if not self._load_model("tts_models/multilingual/multi-dataset/your_tts"):
                raise Exception("Could not load voice cloning model")
            
            # Clone voice
            self._tts.tts_to_file(
                text=text,
                file_path=str(output_path),
                speaker_wav=str(reference_audio)
            )
            
            duration = self.estimate_duration(text)
            
            return TTSResult(
                success=True,
                audio_path=output_path,
                provider_used=TTSProvider.COQUI,
                duration=duration,
                quality_score=0.9,  # High quality for voice cloning
                metadata={
                    "model_used": "your_tts",
                    "reference_audio": str(reference_audio),
                    "cloned_voice": True
                }
            )
            
        except Exception as e:
            self.logger.error(f"Voice cloning failed: {e}")
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.COQUI,
                duration=0.0,
                quality_score=0.0,
                error_message=str(e)
            )