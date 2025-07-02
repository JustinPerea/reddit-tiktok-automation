"""
Microsoft Edge TTS provider implementation.
High-quality free TTS using Microsoft's Edge browser voices.
"""

import asyncio
import tempfile
from typing import Dict
from pathlib import Path

from ..tts_engine import BaseTTSProvider, TTSRequest, TTSResult, TTSProvider


class EdgeTTSProvider(BaseTTSProvider):
    """Microsoft Edge TTS provider using edge-tts library."""
    
    def __init__(self):
        super().__init__("Microsoft Edge TTS")
        self._edge_tts = None
        self._voices_cache = None
    
    def is_available(self) -> bool:
        """Check if edge-tts is available."""
        if self._is_available is not None:
            return self._is_available
        
        try:
            import edge_tts
            self._edge_tts = edge_tts
            self._is_available = True
            self.logger.info("edge-tts is available")
        except ImportError:
            self.logger.warning("edge-tts not installed. Install with: pip install edge-tts")
            self._is_available = False
        
        return self._is_available
    
    def get_voices(self) -> Dict[str, str]:
        """Get available Edge TTS voices."""
        if not self.is_available():
            return {}
        
        if self._voices_cache is not None:
            return self._voices_cache
        
        try:
            # Get voices asynchronously - handle existing event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an event loop, skip voice fetching and use defaults
                self.logger.debug("Event loop detected, using default voices")
                return self._get_default_voices()
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                voices = asyncio.run(self._get_voices_async())
            
            # Filter to most common/useful voices for TikTok
            voice_dict = {}
            for voice in voices:
                # Focus on English voices and a few other popular languages
                if any(lang in voice.get('Locale', '').lower() for lang in ['en-us', 'en-gb', 'en-au', 'en-ca']):
                    voice_id = voice.get('ShortName', '')
                    voice_name = f"{voice.get('FriendlyName', '')} ({voice.get('Locale', '')})"
                    if voice_id:
                        voice_dict[voice_id] = voice_name
            
            # Add some popular non-English voices
            for voice in voices:
                locale = voice.get('Locale', '').lower()
                if locale.startswith(('es-', 'fr-', 'de-', 'it-', 'pt-', 'ja-', 'ko-', 'zh-')):
                    voice_id = voice.get('ShortName', '')
                    voice_name = f"{voice.get('FriendlyName', '')} ({voice.get('Locale', '')})"
                    if voice_id and len(voice_dict) < 30:  # Limit total voices
                        voice_dict[voice_id] = voice_name
            
            self._voices_cache = voice_dict
            return voice_dict
            
        except Exception as e:
            self.logger.error(f"Could not get Edge TTS voices: {e}")
            return self._get_default_voices()
    
    async def _get_voices_async(self):
        """Get voices asynchronously."""
        voices = await self._edge_tts.list_voices()
        return voices
    
    def _get_default_voices(self) -> Dict[str, str]:
        """Get default voice mapping when API fails."""
        return {
            "en-US-AriaNeural": "Aria (English US, Female)",
            "en-US-DavisNeural": "Davis (English US, Male)",
            "en-US-JennyNeural": "Jenny (English US, Female)",
            "en-US-GuyNeural": "Guy (English US, Male)",
            "en-GB-SoniaNeural": "Sonia (English UK, Female)",
            "en-GB-RyanNeural": "Ryan (English UK, Male)",
            "en-AU-NatashaNeural": "Natasha (English AU, Female)",
            "en-AU-WilliamNeural": "William (English AU, Male)",
        }
    
    def get_quality_score(self) -> float:
        """Edge TTS quality score."""
        return 0.9  # Very high quality, near premium
    
    def get_max_text_length(self) -> int:
        """Edge TTS can handle long texts."""
        return 10000
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for Edge TTS."""
        processed = text.strip()
        
        # Edge TTS handles SSML, so we can add some enhancements
        processed = processed.replace("...", '<break time="500ms"/>')
        
        # Wrap in SSML for better control
        processed = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">{processed}</speak>'
        
        return processed
    
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Generate speech using Edge TTS."""
        if not self.is_available():
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.EDGE_TTS,
                duration=0.0,
                quality_score=0.0,
                error_message="edge-tts not available"
            )
        
        if not self.validate_request(request):
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.EDGE_TTS,
                duration=0.0,
                quality_score=0.0,
                error_message="Invalid request parameters"
            )
        
        try:
            # Run async synthesis - handle existing event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an event loop, we can't use asyncio.run()
                self.logger.debug("Event loop detected, Edge TTS unavailable in this context")
                return TTSResult(
                    success=False,
                    audio_path=None,
                    provider_used=TTSProvider.EDGE_TTS,
                    duration=0.0,
                    quality_score=0.0,
                    error_message="Edge TTS not available in async context"
                )
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                result = asyncio.run(self._synthesize_async(request))
            return result
            
        except Exception as e:
            self.logger.error(f"Edge TTS synthesis failed: {e}")
            return TTSResult(
                success=False,
                audio_path=None,
                provider_used=TTSProvider.EDGE_TTS,
                duration=0.0,
                quality_score=0.0,
                error_message=str(e)
            )
    
    async def _synthesize_async(self, request: TTSRequest) -> TTSResult:
        """Async synthesis method."""
        # Preprocess text
        processed_text = self.preprocess_text(request.text)
        
        # Select voice
        available_voices = self.get_voices()
        voice = request.voice if request.voice in available_voices else "en-US-AriaNeural"
        
        # Generate output path
        if request.output_path:
            output_path = request.output_path
        else:
            temp_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_tts"
            temp_dir.mkdir(exist_ok=True)
            output_path = temp_dir / f"edge_tts_{hash(processed_text)}.mp3"
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create TTS communicator
        communicate = self._edge_tts.Communicate(processed_text, voice)
        
        # Adjust rate if needed
        if request.speed != 1.0:
            # Convert speed to Edge TTS rate format
            if request.speed > 1.0:
                rate = f"+{int((request.speed - 1.0) * 100)}%"
            else:
                rate = f"-{int((1.0 - request.speed) * 100)}%"
            communicate = self._edge_tts.Communicate(processed_text, voice, rate=rate)
        
        # Generate audio
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        # Save audio file
        with open(output_path, "wb") as f:
            f.write(audio_data)
        
        # Estimate duration
        duration = self.estimate_duration(request.text, request.speed)
        
        return TTSResult(
            success=True,
            audio_path=output_path,
            provider_used=TTSProvider.EDGE_TTS,
            duration=duration,
            quality_score=self.get_quality_score(),
            metadata={
                "voice_used": voice,
                "text_length": len(request.text),
                "original_text": request.text,
                "speed": request.speed,
                "rate_adjustment": f"{request.speed:.1f}x" if request.speed != 1.0 else "normal"
            }
        )
    
    def get_voice_by_style(self, style: str = "neutral") -> str:
        """Get voice by emotional style."""
        voices = self.get_voices()
        
        # Map styles to appropriate voices
        style_mapping = {
            "neutral": "en-US-AriaNeural",
            "friendly": "en-US-JennyNeural", 
            "professional": "en-US-DavisNeural",
            "casual": "en-US-GuyNeural",
            "authoritative": "en-GB-RyanNeural",
            "warm": "en-AU-NatashaNeural"
        }
        
        preferred_voice = style_mapping.get(style.lower(), "en-US-AriaNeural")
        
        # Return preferred voice if available, otherwise fallback
        if preferred_voice in voices:
            return preferred_voice
        
        # Return first available English voice
        for voice_id in voices.keys():
            if "en-US" in voice_id:
                return voice_id
        
        # Final fallback
        return list(voices.keys())[0] if voices else "en-US-AriaNeural"