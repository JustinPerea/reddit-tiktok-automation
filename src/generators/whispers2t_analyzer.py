"""
WhisperS2T Audio Analyzer for Word-Level Timing

This module provides fast audio analysis using WhisperS2T - 
a highly optimized pipeline that's 2.3x faster than WhisperX with better NumPy 2.x compatibility.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

try:
    from whisper_s2t import load_model
    WHISPERS2T_AVAILABLE = True
except ImportError:
    WHISPERS2T_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class WhisperS2TTiming:
    """Word timing information from WhisperS2T transcription."""
    word: str
    start: float
    end: float
    confidence: float = 1.0


class WhisperS2TAnalyzer:
    """
    Audio analyzer using WhisperS2T for word-level timestamps.
    
    Provides excellent timing accuracy with 2.3x speed improvement over WhisperX
    and better NumPy 2.x compatibility through CTranslate2 backend.
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize WhisperS2T analyzer.
        
        Args:
            model_size: Size of Whisper model ("tiny", "base", "small", "medium", "large-v3")
        """
        self.model_size = model_size
        self.model = None
        self._model_loaded = False
        
        if not WHISPERS2T_AVAILABLE:
            logger.warning("WhisperS2T not available - install with: pip install whisper-s2t")
    
    def is_available(self) -> bool:
        """Check if WhisperS2T is available and working."""
        return WHISPERS2T_AVAILABLE
    
    def _load_model(self) -> bool:
        """Load WhisperS2T model for transcription."""
        if self._model_loaded or not WHISPERS2T_AVAILABLE:
            return self._model_loaded
        
        try:
            logger.info(f"Loading WhisperS2T {self.model_size} model...")
            start_time = time.time()
            
            # Load WhisperS2T model with optimized settings
            self.model = load_model(
                model_identifier=self.model_size,  # Use model size directly
                backend="CTranslate2",  # Use CTranslate2 for better compatibility
                device="cpu",  # Use CPU for compatibility
                compute_type="int8",  # Use int8 for CPU compatibility
            )
            
            load_time = time.time() - start_time
            logger.info(f"WhisperS2T model loaded in {load_time:.2f}s")
            self._model_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load WhisperS2T model: {e}")
            self._model_loaded = False
            return False
    
    def analyze_audio(self, audio_path: Path, expected_text: Optional[str] = None) -> List[WhisperS2TTiming]:
        """
        Analyze audio file and extract word-level timestamps.
        
        Args:
            audio_path: Path to audio file
            expected_text: Expected text content (optional, for verification)
            
        Returns:
            List of WhisperS2TTiming objects with word timestamps
        """
        if not WHISPERS2T_AVAILABLE:
            logger.error("WhisperS2T not available for audio analysis")
            return []
        
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return []
        
        # Try to load models - if it fails, return empty list
        if not self._load_model():
            logger.warning("WhisperS2T models failed to load")
            return []
        
        try:
            logger.info(f"Analyzing audio with WhisperS2T: {audio_path}")
            start_time = time.time()
            
            # Transcribe with word-level timestamps using WhisperS2T API
            result = self.model.transcribe_with_vad(
                [str(audio_path)],  # WhisperS2T expects a list of audio files
                lang_codes=["en"],  # Force English for Reddit content
                tasks=["transcribe"],  # Transcription task
                initial_prompts=[None],  # No initial prompt
                batch_size=1,  # Process one file at a time
            )
            
            analysis_time = time.time() - start_time
            logger.info(f"WhisperS2T analysis completed in {analysis_time:.2f}s")
            
            # Extract word timings from WhisperS2T result (segment-level only)
            word_timings = []
            
            if result and len(result) > 0:
                file_result = result[0]  # Get result for first (and only) file
                
                # WhisperS2T returns segment-level timestamps, estimate word-level
                for segment in file_result:
                    text = segment.get('text', '').strip()
                    seg_start = segment.get('start_time', 0.0)
                    seg_end = segment.get('end_time', seg_start + 1.0)
                    
                    if text and seg_end > seg_start:
                        # Split into words and estimate natural timing
                        words = text.split()
                        if words:
                            # Use natural word timing instead of uniform distribution
                            word_timings_segment = self._estimate_natural_word_timing(
                                words, seg_start, seg_end
                            )
                            word_timings.extend(word_timings_segment)
            
            logger.info(f"Extracted {len(word_timings)} word timings from WhisperS2T")
            
            # Log quality comparison if expected text provided
            if expected_text and word_timings:
                transcribed_text = ' '.join([wt.word for wt in word_timings])
                self._log_quality_comparison(expected_text, transcribed_text)
            
            return word_timings
            
        except Exception as e:
            logger.error(f"WhisperS2T audio analysis failed: {e}")
            return []
    
    def _log_quality_comparison(self, expected: str, transcribed: str) -> None:
        """Log quality comparison between expected and transcribed text."""
        expected_words = set(expected.lower().split())
        transcribed_words = set(transcribed.lower().split())
        
        if expected_words:
            overlap = len(expected_words & transcribed_words)
            accuracy = overlap / len(expected_words)
            logger.info(f"WhisperS2T transcription accuracy: {accuracy:.1%} ({overlap}/{len(expected_words)} words)")
        
        # Log first 100 characters for comparison
        logger.debug(f"Expected: {expected[:100]}...")
        logger.debug(f"Transcribed: {transcribed[:100]}...")
    
    def _estimate_natural_word_timing(self, words: List[str], seg_start: float, seg_end: float) -> List[WhisperS2TTiming]:
        """
        Estimate natural word timing within a segment, accounting for word complexity and natural pauses.
        
        Args:
            words: List of words in the segment
            seg_start: Segment start time
            seg_end: Segment end time
            
        Returns:
            List of WhisperS2TTiming objects with natural timing
        """
        if not words:
            return []
            
        segment_duration = seg_end - seg_start
        
        # Calculate relative word weights based on complexity
        word_weights = []
        for word in words:
            # Base weight by syllable count
            syllables = self._estimate_syllables(word)
            
            # Adjust for word complexity
            complexity = 1.0
            if len(word) > 8:  # Long words take more time
                complexity += 0.3
            if any(c in word.lower() for c in 'xzvqj'):  # Difficult consonants
                complexity += 0.2
            if word.endswith(('tion', 'sion', 'ous', 'ment')):  # Complex endings
                complexity += 0.2
                
            # Adjust for word frequency (common words spoken faster)
            if word.lower() in {'i', 'a', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}:
                complexity *= 0.7
            elif word.lower() in {'am', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would'}:
                complexity *= 0.8
                
            # Add pause factors for punctuation context
            if word.endswith(('.', '!', '?')):
                complexity += 0.5  # Pause after sentence
            elif word.endswith(','):
                complexity += 0.2  # Small pause after comma
                
            word_weights.append(syllables * complexity)
        
        # Normalize weights to distribute across segment duration
        total_weight = sum(word_weights)
        if total_weight == 0:
            total_weight = len(words)  # Fallback
            
        # Distribute time proportionally
        timings = []
        current_time = seg_start
        
        for i, (word, weight) in enumerate(zip(words, word_weights)):
            # Calculate word duration based on weight
            word_duration = (weight / total_weight) * segment_duration
            
            # Ensure minimum duration
            word_duration = max(word_duration, 0.1)
            
            # Ensure we don't exceed segment end
            if current_time + word_duration > seg_end:
                word_duration = seg_end - current_time
                
            timing = WhisperS2TTiming(
                word=word,
                start=current_time,
                end=current_time + word_duration,
                confidence=0.9
            )
            timings.append(timing)
            
            current_time += word_duration
            
            # Break if we've reached the end
            if current_time >= seg_end:
                break
                
        return timings
    
    def _estimate_syllables(self, word: str) -> int:
        """
        Estimate the number of syllables in a word for timing calculation.
        
        Args:
            word: Word to analyze
            
        Returns:
            Estimated syllable count
        """
        import re
        
        # Convert to lowercase and remove punctuation
        word = re.sub(r'[^a-z]', '', word.lower())
        
        if not word:
            return 1
            
        # Remove common endings that don't add syllables
        word = re.sub(r'(ed|es|ing|ly|tion|sion)$', '', word)
        
        # Count vowel groups as syllables
        syllables = len(re.findall(r'[aeiouy]+', word))
        
        # Adjust for silent e
        if word.endswith('e') and syllables > 1:
            syllables -= 1
            
        # Minimum one syllable per word
        return max(1, syllables)
    
    def convert_to_word_timings(self, whispers2t_timings: List[WhisperS2TTiming]) -> List[Tuple[str, float, float]]:
        """
        Convert WhisperS2TTiming objects to simple tuples for compatibility.
        
        Args:
            whispers2t_timings: List of WhisperS2TTiming objects
            
        Returns:
            List of (word, start_time, end_time) tuples
        """
        return [(wt.word, wt.start, wt.end) for wt in whispers2t_timings]


def create_whispers2t_analyzer(model_size: str = "base") -> WhisperS2TAnalyzer:
    """Factory function to create a WhisperS2T analyzer instance."""
    return WhisperS2TAnalyzer(model_size=model_size)