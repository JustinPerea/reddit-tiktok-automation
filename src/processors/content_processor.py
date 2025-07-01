"""
Main content processing engine for Reddit stories.
Handles validation, cleaning, and quality assessment.
"""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

from config.settings import get_settings
from .quality_scorer import QualityScorer
from .reddit_formatter import RedditFormatter


@dataclass
class ContentValidation:
    """Content validation results."""
    is_valid: bool
    quality_score: float
    word_count: int
    issues: list[str]
    recommendations: list[str]


@dataclass
class ProcessedContent:
    """Processed content with metadata."""
    original_text: str
    cleaned_text: str
    tts_optimized_text: str
    validation: ContentValidation
    metadata: Dict[str, Any]
    estimated_duration: int  # seconds


class ContentProcessor:
    """Main content processing engine."""
    
    def __init__(self):
        self.settings = get_settings()
        self.quality_scorer = QualityScorer()
        self.reddit_formatter = RedditFormatter()
        self.logger = logger.bind(name="ContentProcessor")
        
    def process(self, raw_text: str, source_url: str = None) -> Optional[ProcessedContent]:
        """
        Process raw Reddit content into optimized format.
        
        Args:
            raw_text: Raw text from Reddit post
            source_url: Optional source URL for attribution
            
        Returns:
            ProcessedContent object or None if validation fails
        """
        self.logger.info(f"Processing content ({len(raw_text)} characters)")
        
        try:
            # Step 1: Basic validation
            if not self._basic_validation(raw_text):
                self.logger.warning("Content failed basic validation")
                return None
            
            # Step 2: Clean and format
            cleaned_text = self.reddit_formatter.clean_reddit_formatting(raw_text)
            
            # Step 3: Quality assessment
            validation = self.validate_content(cleaned_text)
            
            if not validation.is_valid:
                self.logger.warning(f"Content failed quality validation: {validation.issues}")
                return None
            
            # Step 4: TTS optimization
            tts_optimized_text = self.reddit_formatter.optimize_for_tts(cleaned_text)
            
            # Step 5: Generate metadata
            metadata = self._extract_metadata(cleaned_text, source_url)
            
            # Step 6: Estimate video duration
            estimated_duration = self._estimate_duration(tts_optimized_text)
            
            processed_content = ProcessedContent(
                original_text=raw_text,
                cleaned_text=cleaned_text,
                tts_optimized_text=tts_optimized_text,
                validation=validation,
                metadata=metadata,
                estimated_duration=estimated_duration
            )
            
            self.logger.info(f"Content processed successfully (score: {validation.quality_score:.2f})")
            return processed_content
            
        except Exception as e:
            self.logger.error(f"Error processing content: {e}")
            return None
    
    def validate_content(self, text: str) -> ContentValidation:
        """
        Validate content quality and suitability.
        
        Args:
            text: Cleaned text to validate
            
        Returns:
            ContentValidation object with results
        """
        issues = []
        recommendations = []
        
        # Word count validation
        word_count = len(text.split())
        min_words = self.settings.MIN_WORD_COUNT
        max_words = self.settings.MAX_WORD_COUNT
        
        if word_count < min_words:
            issues.append(f"Content too short ({word_count} words, minimum {min_words})")
        elif word_count > max_words:
            issues.append(f"Content too long ({word_count} words, maximum {max_words})")
        elif word_count < min_words + 50:
            recommendations.append("Consider adding more detail for better engagement")
        
        # Quality score calculation
        quality_score = self.quality_scorer.calculate_score(text)
        
        if quality_score < self.settings.QUALITY_THRESHOLD:
            issues.append(f"Quality score too low ({quality_score:.2f}, minimum {self.settings.QUALITY_THRESHOLD})")
        
        # Content structure validation
        if not self._has_narrative_structure(text):
            issues.append("Content lacks clear narrative structure")
            recommendations.append("Ensure story has beginning, conflict, and resolution")
        
        # Appropriateness check
        if self._contains_inappropriate_content(text):
            issues.append("Content contains inappropriate material")
        
        # TTS suitability
        if not self._is_tts_friendly(text):
            recommendations.append("Content may need adjustment for text-to-speech")
        
        is_valid = len(issues) == 0 and quality_score >= self.settings.QUALITY_THRESHOLD
        
        return ContentValidation(
            is_valid=is_valid,
            quality_score=quality_score,
            word_count=word_count,
            issues=issues,
            recommendations=recommendations
        )
    
    def _basic_validation(self, text: str) -> bool:
        """Basic text validation checks."""
        if not text or not text.strip():
            return False
        
        if len(text.strip()) < 50:  # Too short to be meaningful
            return False
        
        # Check for excessive special characters
        special_char_ratio = len(re.findall(r'[^\w\s]', text)) / len(text)
        if special_char_ratio > 0.3:  # More than 30% special characters
            return False
        
        return True
    
    def _has_narrative_structure(self, text: str) -> bool:
        """Check if text has basic narrative structure."""
        # Look for common story indicators
        story_indicators = [
            # Time indicators
            r'\b(yesterday|today|last week|last month|ago|when|after|before)\b',
            # Emotional indicators
            r'\b(felt|thought|realized|decided|angry|sad|happy|confused)\b',
            # Action indicators
            r'\b(went|did|said|told|asked|happened|occurred)\b',
            # Relationship indicators
            r'\b(boyfriend|girlfriend|husband|wife|friend|family|coworker)\b'
        ]
        
        found_indicators = 0
        for pattern in story_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                found_indicators += 1
        
        # Need at least 2 different types of indicators for narrative structure
        return found_indicators >= 2
    
    def _contains_inappropriate_content(self, text: str) -> bool:
        """Check for inappropriate content."""
        # Basic inappropriate content patterns
        inappropriate_patterns = [
            r'\b(suicide|kill myself|end it all)\b',
            r'\b(detailed violence|graphic)\b',
            r'\b(illegal drugs|drug dealing)\b'
        ]
        
        for pattern in inappropriate_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _is_tts_friendly(self, text: str) -> bool:
        """Check if text is suitable for text-to-speech."""
        # Check for excessive abbreviations
        abbrev_count = len(re.findall(r'\b[A-Z]{2,}\b', text))
        word_count = len(text.split())
        
        if word_count > 0 and abbrev_count / word_count > 0.1:  # More than 10% abbreviations
            return False
        
        # Check for excessive numbers/symbols
        symbol_count = len(re.findall(r'[^\w\s.,!?]', text))
        if symbol_count / len(text) > 0.05:  # More than 5% symbols
            return False
        
        return True
    
    def _extract_metadata(self, text: str, source_url: str = None) -> Dict[str, Any]:
        """Extract metadata from content."""
        metadata = {
            "source_url": source_url,
            "character_count": len(text),
            "word_count": len(text.split()),
            "sentence_count": len(re.findall(r'[.!?]+', text)),
            "processing_timestamp": None,  # Will be set when processing
            "emotional_tone": None,  # Will be set by emotional analyzer
            "suggested_voice": None,  # Will be determined based on content
        }
        
        # Detect story type
        story_type = self._detect_story_type(text)
        metadata["story_type"] = story_type
        
        # Suggest optimal voice based on content
        metadata["suggested_voice"] = self._suggest_voice(text, story_type)
        
        return metadata
    
    def _detect_story_type(self, text: str) -> str:
        """Detect the type of story for optimization."""
        text_lower = text.lower()
        
        # AITA stories
        if any(phrase in text_lower for phrase in ["am i the asshole", "aita", "am i wrong"]):
            return "aita"
        
        # Relationship stories
        if any(phrase in text_lower for phrase in ["boyfriend", "girlfriend", "relationship", "dating"]):
            return "relationship"
        
        # Work stories
        if any(phrase in text_lower for phrase in ["work", "boss", "coworker", "office", "job"]):
            return "workplace"
        
        # Family stories
        if any(phrase in text_lower for phrase in ["family", "mom", "dad", "sister", "brother", "parent"]):
            return "family"
        
        # TIFU stories
        if any(phrase in text_lower for phrase in ["tifu", "today i fucked up", "messed up"]):
            return "tifu"
        
        return "general"
    
    def _suggest_voice(self, text: str, story_type: str) -> str:
        """Suggest optimal voice based on content and type."""
        # Default voice mappings based on story type and content
        voice_mappings = {
            "aita": "alloy",  # Neutral, authoritative
            "relationship": "nova",  # Warm, empathetic
            "workplace": "echo",  # Professional
            "family": "shimmer",  # Friendly
            "tifu": "fable",  # Casual, humorous
            "general": "alloy"
        }
        
        return voice_mappings.get(story_type, "alloy")
    
    def _estimate_duration(self, text: str) -> int:
        """Estimate video duration based on text length."""
        # Average speaking rate: ~150 words per minute
        # TikTok optimal: 60-90 seconds
        word_count = len(text.split())
        estimated_seconds = (word_count / 150) * 60
        
        # Add buffer for pauses and emphasis
        estimated_seconds *= 1.2
        
        return int(estimated_seconds)