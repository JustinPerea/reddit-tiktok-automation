"""
Enhanced Edge TTS provider with word-level timing markers for perfect audio-subtitle synchronization.

This module provides perfect synchronization by capturing WordBoundary events from Edge TTS,
eliminating the need for transcription and solving all timing mismatch issues.
"""

import asyncio
import tempfile
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger("EdgeTTSTiming")


@dataclass
class WordTiming:
    """Word timing information from Edge TTS WordBoundary events."""
    word: str
    start: float  # seconds
    end: float    # seconds
    duration: float
    offset: int   # original offset from Edge TTS


class EdgeTTSTimingProvider:
    """
    Enhanced Edge TTS provider that captures word-level timing for perfect synchronization.
    
    This solves the fundamental synchronization problem by:
    1. Using the same TTS engine for both audio and timing
    2. Capturing exact WordBoundary events during synthesis
    3. Providing 100% text accuracy (no transcription mismatch)
    4. Delivering professional neural voice quality
    """
    
    def __init__(self):
        """Initialize the Edge TTS timing provider."""
        self.edge_tts = None
        self._is_available = None
        
    def is_available(self) -> bool:
        """Check if Edge TTS is available."""
        if self._is_available is not None:
            return self._is_available
            
        try:
            import edge_tts
            self.edge_tts = edge_tts
            self._is_available = True
            logger.info("Edge TTS with timing support is available")
        except ImportError:
            logger.warning("edge-tts not installed. Install with: pip install edge-tts")
            self._is_available = False
            
        return self._is_available
    
    async def generate_audio_with_timing(
        self, 
        text: str, 
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
        output_path: Optional[Path] = None
    ) -> Tuple[Path, List[WordTiming]]:
        """
        Generate audio with perfect word-level timing markers.
        
        Args:
            text: Text to synthesize
            voice: Edge TTS voice to use
            speed: Speech rate (1.0 = normal)
            output_path: Optional output path for audio file
            
        Returns:
            Tuple of (audio_file_path, word_timings)
        """
        if not self.is_available():
            raise RuntimeError("Edge TTS not available")
            
        # Prepare output path
        if output_path is None:
            temp_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_tts"
            temp_dir.mkdir(exist_ok=True)
            output_path = temp_dir / f"edge_tts_timing_{hash(text)}.mp3"
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Adjust rate if needed
        rate = "+0%"  # Default rate
        if speed != 1.0:
            if speed > 1.0:
                rate = f"+{int((speed - 1.0) * 100)}%"
            else:
                rate = f"-{int((1.0 - speed) * 100)}%"
        
        # Create TTS communicator
        communicate = self.edge_tts.Communicate(text, voice, rate=rate)
        
        # Collect audio data and word timings
        audio_data = b""
        word_timings = []
        
        logger.info(f"Generating audio with timing for {len(text)} characters")
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
            elif chunk["type"] == "WordBoundary":
                # Extract word timing information
                word_text = chunk.get("text", "").strip()
                offset = chunk.get("offset", 0)  # in 100-nanosecond units
                duration = chunk.get("duration", 0)  # in 100-nanosecond units
                
                if word_text:
                    # Convert from 100-nanosecond units to seconds
                    start_seconds = offset / 10_000_000
                    duration_seconds = duration / 10_000_000
                    end_seconds = start_seconds + duration_seconds
                    
                    word_timing = WordTiming(
                        word=word_text,
                        start=start_seconds,
                        end=end_seconds,
                        duration=duration_seconds,
                        offset=offset
                    )
                    word_timings.append(word_timing)
        
        # Save audio file
        with open(output_path, "wb") as f:
            f.write(audio_data)
        
        logger.info(f"Generated audio: {output_path}")
        logger.info(f"Captured {len(word_timings)} word timings")
        
        # Log first few timings for verification
        for i, timing in enumerate(word_timings[:5]):
            logger.debug(f"  {i+1}: '{timing.word}' ({timing.start:.3f}s - {timing.end:.3f}s)")
        
        return output_path, word_timings
    
    def generate_audio_with_timing_sync(
        self, 
        text: str, 
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
        output_path: Optional[Path] = None
    ) -> Tuple[Path, List[WordTiming]]:
        """
        Synchronous wrapper for generate_audio_with_timing.
        
        Args:
            text: Text to synthesize
            voice: Edge TTS voice to use
            speed: Speech rate (1.0 = normal)
            output_path: Optional output path for audio file
            
        Returns:
            Tuple of (audio_file_path, word_timings)
        """
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            # If we're in a loop, we need to use a different approach
            logger.warning("Already in event loop, Edge TTS timing may not work in this context")
            raise RuntimeError("Cannot run Edge TTS in existing event loop")
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(self.generate_audio_with_timing(text, voice, speed, output_path))
    
    def convert_to_subtitle_format(self, word_timings: List[WordTiming]) -> List[Tuple[str, float, float]]:
        """
        Convert WordTiming objects to the format expected by video generator.
        
        Args:
            word_timings: List of WordTiming objects
            
        Returns:
            List of (word, start_time, end_time) tuples
        """
        return [(wt.word, wt.start, wt.end) for wt in word_timings]
    
    def export_timing_data(self, word_timings: List[WordTiming], output_path: Path) -> None:
        """
        Export timing data as JSON for debugging or analysis.
        
        Args:
            word_timings: List of WordTiming objects
            output_path: Path to save JSON file
        """
        timing_data = {
            "total_words": len(word_timings),
            "total_duration": word_timings[-1].end if word_timings else 0,
            "words": [
                {
                    "word": wt.word,
                    "start": wt.start,
                    "end": wt.end,
                    "duration": wt.duration,
                    "offset": wt.offset
                }
                for wt in word_timings
            ]
        }
        
        output_path.write_text(json.dumps(timing_data, indent=2), encoding="utf-8")
        logger.info(f"Exported timing data: {output_path}")
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available Edge TTS voices."""
        if not self.is_available():
            return {}
            
        # Return default voices to avoid async complexity
        return {
            "en-US-AriaNeural": "Aria (English US, Female) - Natural",
            "en-US-DavisNeural": "Davis (English US, Male) - Professional", 
            "en-US-JennyNeural": "Jenny (English US, Female) - Friendly",
            "en-US-GuyNeural": "Guy (English US, Male) - Casual",
            "en-GB-SoniaNeural": "Sonia (English UK, Female) - Elegant",
            "en-GB-RyanNeural": "Ryan (English UK, Male) - Authoritative",
            "en-AU-NatashaNeural": "Natasha (English AU, Female) - Warm",
            "en-AU-WilliamNeural": "William (English AU, Male) - Clear",
        }


def create_edge_tts_timing_provider() -> EdgeTTSTimingProvider:
    """Factory function to create an Edge TTS timing provider."""
    return EdgeTTSTimingProvider()