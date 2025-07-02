"""
Insanely Fast Whisper Audio Analyzer for Word-Level Timing

This module provides fast audio analysis using Insanely Fast Whisper - 
a highly optimized version of Whisper with modern NumPy 2.x compatibility.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

try:
    import torch
    from transformers import pipeline
    FAST_WHISPER_AVAILABLE = True
except ImportError:
    FAST_WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class FastWhisperTiming:
    """Word timing information from Fast Whisper transcription."""
    word: str
    start: float
    end: float
    confidence: float = 1.0


class FastWhisperAnalyzer:
    """
    Audio analyzer using Insanely Fast Whisper for word-level timestamps.
    
    Provides excellent timing accuracy with 70x speed improvement over regular Whisper
    and modern NumPy 2.x compatibility.
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Fast Whisper analyzer.
        
        Args:
            model_size: Size of Whisper model ("tiny", "base", "small", "medium", "large-v3")
        """
        self.model_size = model_size
        self.pipeline = None
        self._model_loaded = False
        
        # Map model sizes to Hugging Face model names
        self.model_map = {
            "tiny": "openai/whisper-tiny",
            "base": "openai/whisper-base", 
            "small": "openai/whisper-small",
            "medium": "openai/whisper-medium",
            "large": "openai/whisper-large-v3",
            "large-v3": "openai/whisper-large-v3"
        }
        
        if not FAST_WHISPER_AVAILABLE:
            logger.warning("Insanely Fast Whisper not available - install with: pip install insanely-fast-whisper")
    
    def is_available(self) -> bool:
        """Check if Fast Whisper is available and working."""
        return FAST_WHISPER_AVAILABLE
    
    def _load_model(self) -> bool:
        """Load Fast Whisper model for transcription."""
        if self._model_loaded or not FAST_WHISPER_AVAILABLE:
            return self._model_loaded
        
        try:
            logger.info(f"Loading Fast Whisper {self.model_size} model...")
            start_time = time.time()
            
            model_name = self.model_map.get(self.model_size, "openai/whisper-base")
            
            # Determine device and dtype
            device = "cpu"  # Start with CPU for compatibility
            torch_dtype = torch.float32
            
            if torch.cuda.is_available():
                device = "cuda:0"
                torch_dtype = torch.float16
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "mps"
                torch_dtype = torch.float32  # MPS doesn't support float16 well
            
            # Create optimized pipeline
            self.pipeline = pipeline(
                "automatic-speech-recognition",
                model=model_name,
                torch_dtype=torch_dtype,
                device=device,
                return_timestamps=True  # Critical for word-level timing
            )
            
            load_time = time.time() - start_time
            logger.info(f"Fast Whisper model loaded in {load_time:.2f}s on device: {device}")
            self._model_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Fast Whisper model: {e}")
            self._model_loaded = False
            return False
    
    def analyze_audio(self, audio_path: Path, expected_text: Optional[str] = None) -> List[FastWhisperTiming]:
        """
        Analyze audio file and extract word-level timestamps.
        
        Args:
            audio_path: Path to audio file
            expected_text: Expected text content (optional, for verification)
            
        Returns:
            List of FastWhisperTiming objects with word timestamps
        """
        if not FAST_WHISPER_AVAILABLE:
            logger.error("Fast Whisper not available for audio analysis")
            return []
        
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return []
        
        # Try to load models - if it fails, return empty list
        if not self._load_model():
            logger.warning("Fast Whisper models failed to load")
            return []
        
        try:
            logger.info(f"Analyzing audio with Fast Whisper: {audio_path}")
            start_time = time.time()
            
            # Transcribe with word-level timestamps
            # Use optimized settings for speed and accuracy
            result = self.pipeline(
                str(audio_path),
                chunk_length_s=30,  # Process in 30-second chunks
                batch_size=8,       # Batch processing for speed
                return_timestamps="word",  # Word-level timestamps
                generate_kwargs={
                    "task": "transcribe",
                    "language": "en"  # Force English for Reddit content
                }
            )
            
            analysis_time = time.time() - start_time
            logger.info(f"Fast Whisper analysis completed in {analysis_time:.2f}s")
            
            # Extract word timings
            word_timings = []
            
            if 'chunks' in result:
                for chunk in result['chunks']:
                    if 'timestamp' in chunk and chunk['timestamp']:
                        start, end = chunk['timestamp']
                        word = chunk.get('text', '').strip()
                        
                        if word and start is not None and end is not None:
                            timing = FastWhisperTiming(
                                word=word,
                                start=float(start),
                                end=float(end),
                                confidence=1.0  # Fast Whisper doesn't provide confidence scores
                            )
                            word_timings.append(timing)
            
            # Fallback: if no chunks, try to extract from segments
            elif 'segments' in result:
                for segment in result['segments']:
                    # Split segment text into words and estimate timing
                    words = segment.get('text', '').strip().split()
                    seg_start = segment.get('start', 0.0)
                    seg_end = segment.get('end', seg_start + 1.0)
                    
                    if words and seg_end > seg_start:
                        word_duration = (seg_end - seg_start) / len(words)
                        
                        for i, word in enumerate(words):
                            word_start = seg_start + (i * word_duration)
                            word_end = word_start + word_duration
                            
                            timing = FastWhisperTiming(
                                word=word,
                                start=word_start,
                                end=word_end,
                                confidence=0.8  # Lower confidence for estimated timing
                            )
                            word_timings.append(timing)
            
            logger.info(f"Extracted {len(word_timings)} word timings from Fast Whisper")
            
            # Log quality comparison if expected text provided
            if expected_text and word_timings:
                transcribed_text = ' '.join([wt.word for wt in word_timings])
                self._log_quality_comparison(expected_text, transcribed_text)
            
            return word_timings
            
        except Exception as e:
            logger.error(f"Fast Whisper audio analysis failed: {e}")
            return []
    
    def _log_quality_comparison(self, expected: str, transcribed: str) -> None:
        """Log quality comparison between expected and transcribed text."""
        expected_words = set(expected.lower().split())
        transcribed_words = set(transcribed.lower().split())
        
        if expected_words:
            overlap = len(expected_words & transcribed_words)
            accuracy = overlap / len(expected_words)
            logger.info(f"Fast Whisper transcription accuracy: {accuracy:.1%} ({overlap}/{len(expected_words)} words)")
        
        # Log first 100 characters for comparison
        logger.debug(f"Expected: {expected[:100]}...")
        logger.debug(f"Transcribed: {transcribed[:100]}...")
    
    def convert_to_word_timings(self, fast_whisper_timings: List[FastWhisperTiming]) -> List[Tuple[str, float, float]]:
        """
        Convert FastWhisperTiming objects to simple tuples for compatibility.
        
        Args:
            fast_whisper_timings: List of FastWhisperTiming objects
            
        Returns:
            List of (word, start_time, end_time) tuples
        """
        return [(wt.word, wt.start, wt.end) for wt in fast_whisper_timings]


def create_fast_whisper_analyzer(model_size: str = "base") -> FastWhisperAnalyzer:
    """Factory function to create a Fast Whisper analyzer instance."""
    return FastWhisperAnalyzer(model_size=model_size)