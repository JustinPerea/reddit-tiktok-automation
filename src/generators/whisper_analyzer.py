"""
Regular OpenAI Whisper Audio Analyzer for Word-Level Timing

This module provides audio analysis using regular OpenAI Whisper when WhisperX is unavailable.
While not as precise as WhisperX forced alignment, it provides much better timing than estimation.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class WhisperTiming:
    """Word timing information from Whisper transcription."""
    word: str
    start: float
    end: float
    confidence: float = 1.0


class WhisperAnalyzer:
    """
    Audio analyzer using regular OpenAI Whisper for word-level timestamps.
    
    Provides better timing accuracy than estimation while being more compatible
    than WhisperX with modern NumPy versions.
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper analyzer.
        
        Args:
            model_size: Size of Whisper model ("tiny", "base", "small", "medium", "large")
        """
        self.model_size = model_size
        self.model = None
        self._model_loaded = False
        
        if not WHISPER_AVAILABLE:
            logger.warning("OpenAI Whisper not available - install with: pip install openai-whisper")
    
    def is_available(self) -> bool:
        """Check if Whisper is available and working."""
        return WHISPER_AVAILABLE
    
    def _load_model(self) -> None:
        """Load Whisper model for transcription."""
        if self._model_loaded or not WHISPER_AVAILABLE:
            return
        
        try:
            logger.info(f"Loading Whisper {self.model_size} model...")
            start_time = time.time()
            
            self.model = whisper.load_model(self.model_size)
            
            load_time = time.time() - start_time
            logger.info(f"Whisper model loaded in {load_time:.2f}s")
            self._model_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def analyze_audio(self, audio_path: Path, expected_text: Optional[str] = None) -> List[WhisperTiming]:
        """
        Analyze audio file and extract word-level timestamps.
        
        Args:
            audio_path: Path to audio file
            expected_text: Expected text content (optional, for verification)
            
        Returns:
            List of WhisperTiming objects with word timestamps
        """
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available for audio analysis")
            return []
        
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return []
        
        self._load_model()
        
        try:
            logger.info(f"Analyzing audio with Whisper: {audio_path}")
            start_time = time.time()
            
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                str(audio_path),
                word_timestamps=True,
                verbose=False
            )
            
            analysis_time = time.time() - start_time
            logger.info(f"Whisper analysis completed in {analysis_time:.2f}s")
            
            # Extract word timings
            word_timings = []
            
            if 'segments' in result:
                for segment in result['segments']:
                    if 'words' in segment:
                        for word_info in segment['words']:
                            # Extract word timing information
                            word = word_info.get('word', '').strip()
                            start = word_info.get('start', 0.0)
                            end = word_info.get('end', 0.0)
                            
                            if word and start is not None and end is not None:
                                timing = WhisperTiming(
                                    word=word,
                                    start=start,
                                    end=end,
                                    confidence=1.0  # Whisper doesn't provide word-level confidence
                                )
                                word_timings.append(timing)
            
            logger.info(f"Extracted {len(word_timings)} word timings from Whisper")
            
            # Log quality comparison if expected text provided
            if expected_text and word_timings:
                transcribed_text = ' '.join([wt.word for wt in word_timings])
                self._log_quality_comparison(expected_text, transcribed_text)
            
            return word_timings
            
        except Exception as e:
            logger.error(f"Whisper audio analysis failed: {e}")
            return []
    
    def _log_quality_comparison(self, expected: str, transcribed: str) -> None:
        """Log quality comparison between expected and transcribed text."""
        expected_words = set(expected.lower().split())
        transcribed_words = set(transcribed.lower().split())
        
        if expected_words:
            overlap = len(expected_words & transcribed_words)
            accuracy = overlap / len(expected_words)
            logger.info(f"Whisper transcription accuracy: {accuracy:.1%} ({overlap}/{len(expected_words)} words)")
        
        # Log first 100 characters for comparison
        logger.debug(f"Expected: {expected[:100]}...")
        logger.debug(f"Transcribed: {transcribed[:100]}...")
    
    def convert_to_word_timings(self, whisper_timings: List[WhisperTiming]) -> List[Tuple[str, float, float]]:
        """
        Convert WhisperTiming objects to simple tuples for compatibility.
        
        Args:
            whisper_timings: List of WhisperTiming objects
            
        Returns:
            List of (word, start_time, end_time) tuples
        """
        return [(wt.word, wt.start, wt.end) for wt in whisper_timings]


def create_whisper_analyzer(model_size: str = "base") -> WhisperAnalyzer:
    """Factory function to create a Whisper analyzer instance."""
    return WhisperAnalyzer(model_size=model_size)