"""
Reddit-specific text formatting and TTS optimization.
"""

import re
from typing import Dict, List
from loguru import logger


class RedditFormatter:
    """Handles Reddit-specific formatting cleanup and TTS optimization."""
    
    def __init__(self):
        self.logger = logger.bind(name="RedditFormatter")
        
        # Reddit-specific patterns to clean
        self.reddit_patterns = {
            # Common Reddit abbreviations
            "AITA": "Am I the jerk",
            "NTA": "Not the jerk", 
            "YTA": "You're the jerk",
            "ESH": "Everyone sucks here",
            "NAH": "No jerks here",
            "INFO": "I need more information",
            "TIFU": "Today I messed up",
            "TL;DR": "Too long, didn't read",
            "TLDR": "Too long, didn't read",
            "ETA": "Edit to add",
            "SO": "significant other",
            "BF": "boyfriend",
            "GF": "girlfriend",
            "DH": "dear husband",
            "DW": "dear wife",
            "MIL": "mother-in-law",
            "FIL": "father-in-law",
            "SIL": "sister-in-law",
            "BIL": "brother-in-law"
        }
        
        # Patterns for edit/update removal
        self.edit_patterns = [
            r'\n\n?Edit:.*?(?=\n\n|\Z)',
            r'\n\n?UPDATE:.*?(?=\n\n|\Z)',
            r'\n\n?Edit \d+:.*?(?=\n\n|\Z)',
            r'\n\n?EDIT:.*?(?=\n\n|\Z)',
            r'\(Edit:.*?\)',
            r'\[Edit:.*?\]'
        ]
        
        # TTS pronunciation fixes
        self.pronunciation_fixes = {
            # Numbers and special characters
            r'&': ' and ',
            r'\$(\d+)': r'\1 dollars',
            r'(\d+)%': r'\1 percent',
            r'(\d+)k\b': r'\1 thousand',
            r'(\d+)M\b': r'\1 million',
            r'(\d+)/(\d+)': r'\1 out of \2',
            r'(\d{1,2}):(\d{2})': r'\1 \2',  # Time format
            
            # Common abbreviations
            r'\bvs\b': 'versus',
            r'\betc\b': 'et cetera',
            r'\bie\b': 'that is',
            r'\beg\b': 'for example',
            r'\bwrt\b': 'with regard to',
            r'\btbh\b': 'to be honest',
            r'\bimo\b': 'in my opinion',
            r'\bimho\b': 'in my humble opinion',
            
            # Internet slang
            r'\bomg\b': 'oh my god',
            r'\bwtf\b': 'what the heck',
            r'\bffs\b': 'for crying out loud',
            r'\bsmh\b': 'shaking my head',
            r'\blol\b': 'laughing out loud',
            r'\blmao\b': 'laughing my butt off',
            r'\brofl\b': 'rolling on the floor laughing'
        }
    
    def clean_reddit_formatting(self, text: str) -> str:
        """
        Clean Reddit-specific formatting and markup.
        
        Args:
            text: Raw Reddit post text
            
        Returns:
            Cleaned text suitable for processing
        """
        self.logger.debug("Cleaning Reddit formatting")
        
        try:
            cleaned = text
            
            # Remove edit sections
            for pattern in self.edit_patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
            
            # Remove Reddit markup
            cleaned = self._remove_markdown(cleaned)
            
            # Replace Reddit abbreviations
            cleaned = self._replace_reddit_abbreviations(cleaned)
            
            # Clean up spacing and formatting
            cleaned = self._normalize_spacing(cleaned)
            
            # Remove meta content
            cleaned = self._remove_meta_content(cleaned)
            
            self.logger.debug(f"Cleaned text from {len(text)} to {len(cleaned)} characters")
            return cleaned.strip()
            
        except Exception as e:
            self.logger.error(f"Error cleaning Reddit formatting: {e}")
            return text
    
    def optimize_for_tts(self, text: str) -> str:
        """
        Optimize text for text-to-speech generation.
        
        Args:
            text: Cleaned text
            
        Returns:
            TTS-optimized text
        """
        self.logger.debug("Optimizing text for TTS")
        
        try:
            optimized = text
            
            # Apply pronunciation fixes
            for pattern, replacement in self.pronunciation_fixes.items():
                optimized = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)
            
            # Add natural pauses
            optimized = self._add_natural_pauses(optimized)
            
            # Fix contractions for clarity
            optimized = self._expand_contractions(optimized)
            
            # Normalize punctuation for better speech rhythm
            optimized = self._normalize_punctuation(optimized)
            
            # Add emphasis markers for emotional content
            optimized = self._add_emphasis_markers(optimized)
            
            self.logger.debug("Text optimized for TTS")
            return optimized.strip()
            
        except Exception as e:
            self.logger.error(f"Error optimizing for TTS: {e}")
            return text
    
    def _remove_markdown(self, text: str) -> str:
        """Remove Reddit markdown formatting."""
        # Bold/italic formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'__(.*?)__', r'\1', text)      # __bold__
        text = re.sub(r'_(.*?)_', r'\1', text)        # _italic_
        
        # Links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url)
        text = re.sub(r'https?://[^\s]+', '', text)           # Direct URLs
        
        # Code blocks
        text = re.sub(r'`([^`]+)`', r'\1', text)      # `code`
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # ```code blocks```
        
        # Quotes
        text = re.sub(r'^&gt;.*?$', '', text, flags=re.MULTILINE)  # > quotes
        text = re.sub(r'^>.*?$', '', text, flags=re.MULTILINE)     # > quotes
        
        # Lists
        text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)  # - lists
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # 1. numbered lists
        
        return text
    
    def _replace_reddit_abbreviations(self, text: str) -> str:
        """Replace Reddit-specific abbreviations with full phrases."""
        for abbrev, expansion in self.reddit_patterns.items():
            # Replace as whole words only
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)
        
        return text
    
    def _normalize_spacing(self, text: str) -> str:
        """Normalize spacing and line breaks."""
        # Multiple newlines to single newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Multiple spaces to single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Clean up paragraph breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text
    
    def _remove_meta_content(self, text: str) -> str:
        """Remove meta content that doesn't belong in videos."""
        # Remove throwaway account mentions
        text = re.sub(r'using a throwaway.*?\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'this is a throwaway.*?\n', '', text, flags=re.IGNORECASE)
        
        # Remove references to posting/Reddit
        text = re.sub(r'first time posting.*?\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'posting on mobile.*?\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'obligatory mobile.*?\n', '', text, flags=re.IGNORECASE)
        
        # Remove character count apologies
        text = re.sub(r'sorry for the long post.*?\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'wall of text.*?\n', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural pauses for better speech rhythm."""
        # Add pause after introductory phrases
        intro_phrases = [
            r'(So basically,)',
            r'(Here\'s what happened,)',
            r'(Long story short,)',
            r'(To give you some context,)'
        ]
        
        for phrase in intro_phrases:
            text = re.sub(phrase, r'\1... ', text, flags=re.IGNORECASE)
        
        # Add pauses before emotional peaks
        emotional_transitions = [
            r'(\bBut then\b)',
            r'(\bSuddenly\b)',
            r'(\bThat\'s when\b)',
            r'(\bI couldn\'t believe\b)'
        ]
        
        for transition in emotional_transitions:
            text = re.sub(transition, r'... \1', text, flags=re.IGNORECASE)
        
        return text
    
    def _expand_contractions(self, text: str) -> str:
        """Expand contractions for clearer TTS pronunciation."""
        contractions = {
            r'\bcan\'t\b': 'cannot',
            r'\bwon\'t\b': 'will not',
            r'\bdon\'t\b': 'do not',
            r'\bdidn\'t\b': 'did not',
            r'\bwouldn\'t\b': 'would not',
            r'\bcouldn\'t\b': 'could not',
            r'\bshouldn\'t\b': 'should not',
            r'\bisn\'t\b': 'is not',
            r'\baren\'t\b': 'are not',
            r'\bwasn\'t\b': 'was not',
            r'\bweren\'t\b': 'were not',
            r'\bhaven\'t\b': 'have not',
            r'\bhasn\'t\b': 'has not',
            r'\bhadn\'t\b': 'had not',
            r'\bi\'m\b': 'I am',
            r'\byou\'re\b': 'you are',
            r'\bhe\'s\b': 'he is',
            r'\bshe\'s\b': 'she is',
            r'\bit\'s\b': 'it is',
            r'\bwe\'re\b': 'we are',
            r'\bthey\'re\b': 'they are',
            r'\bi\'ve\b': 'I have',
            r'\byou\'ve\b': 'you have',
            r'\bwe\'ve\b': 'we have',
            r'\bthey\'ve\b': 'they have',
            r'\bi\'ll\b': 'I will',
            r'\byou\'ll\b': 'you will',
            r'\bhe\'ll\b': 'he will',
            r'\bshe\'ll\b': 'she will',
            r'\bwe\'ll\b': 'we will',
            r'\bthey\'ll\b': 'they will'
        }
        
        for contraction, expansion in contractions.items():
            text = re.sub(contraction, expansion, text, flags=re.IGNORECASE)
        
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation for better speech rhythm."""
        # Ensure sentences end with proper punctuation
        text = re.sub(r'([a-zA-Z])\s*$', r'\1.', text)
        
        # Fix multiple punctuation marks
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{3,}', '...', text)
        
        # Add proper spacing after punctuation
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Normalize ellipses
        text = re.sub(r'\.{2,}', '...', text)
        
        return text
    
    def _add_emphasis_markers(self, text: str) -> str:
        """Add emphasis markers for emotional content."""
        # Mark emotional words for emphasis
        emotional_words = [
            r'\b(incredible|unbelievable|shocking|amazing)\b',
            r'\b(terrible|horrible|awful|devastating)\b',
            r'\b(furious|livid|angry|outraged)\b'
        ]
        
        for pattern in emotional_words:
            # Add slight pause before emotional words
            text = re.sub(pattern, r'... \1', text, flags=re.IGNORECASE)
        
        return text
    
    def get_processing_stats(self, original: str, cleaned: str, optimized: str) -> Dict[str, any]:
        """Get statistics about the processing changes."""
        return {
            "original_length": len(original),
            "cleaned_length": len(cleaned),
            "optimized_length": len(optimized),
            "reduction_percentage": ((len(original) - len(cleaned)) / len(original)) * 100,
            "optimization_change": len(optimized) - len(cleaned),
            "original_word_count": len(original.split()),
            "final_word_count": len(optimized.split())
        }