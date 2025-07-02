"""
Bidirectional Text Normalization System

This module provides bidirectional mapping between original text and TTS-optimized text,
ensuring that subtitles match what's actually spoken in the audio.

Key Features:
- Maintains character-level alignment between original and processed text
- Context-aware transformations (e.g., "(28F)" → "28 female" in age contexts)
- Preserves original text for subtitles while optimizing for TTS
- Supports word-level mapping for synchronized subtitles
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TransformationType(Enum):
    """Types of text transformations."""
    AGE_GENDER = "age_gender"  # (25M) → 25 male
    CURRENCY = "currency"  # $50 → 50 dollars
    ABBREVIATION = "abbreviation"  # AITA → Am I the asshole
    CONTRACTION = "contraction"  # I'm → I am
    NUMBER = "number"  # 1st → first
    PUNCTUATION = "punctuation"  # ... → pause
    REDDIT_TERM = "reddit_term"  # TL;DR → Too long didn't read


@dataclass
class TextMapping:
    """Represents a mapping between original and TTS text."""
    original_text: str
    tts_text: str
    original_start: int
    original_end: int
    tts_start: int
    tts_end: int
    transformation_type: TransformationType


@dataclass
class NormalizedText:
    """Result of bidirectional text normalization."""
    original_text: str
    tts_text: str
    word_mappings: List[TextMapping]
    transformation_log: List[Dict[str, str]]


class BidirectionalTextNormalizer:
    """
    Normalizes text for TTS while maintaining bidirectional mappings.
    
    This ensures that:
    1. TTS receives properly formatted text for natural speech
    2. Subtitles can show either original or TTS-optimized text
    3. Word-level synchronization remains accurate
    """
    
    def __init__(self):
        """Initialize the text normalizer with transformation rules."""
        self.logger = logger
        
        # Common Reddit abbreviations
        self.reddit_abbreviations = {
            "AITA": "Am I the asshole",
            "YTA": "You're the asshole",
            "NTA": "Not the asshole",
            "ESH": "Everyone sucks here",
            "NAH": "No assholes here",
            "TIFU": "Today I fucked up",
            "TL;DR": "Too long didn't read",
            "ETA": "Edited to add",
            "IIRC": "If I recall correctly",
            "AFAIK": "As far as I know",
            "IMO": "In my opinion",
            "IMHO": "In my humble opinion",
            "TBH": "To be honest",
            "IDK": "I don't know",
            "IRL": "In real life",
            "DM": "Direct message",
            "PM": "Private message",
            "OP": "Original poster",
            "SO": "Significant other",
            "BF": "Boyfriend",
            "GF": "Girlfriend",
            "MIL": "Mother in law",
            "FIL": "Father in law",
            "SIL": "Sister in law",
            "BIL": "Brother in law"
        }
        
        # Contractions for expansion
        self.contractions = {
            "I'm": "I am",
            "I've": "I have",
            "I'll": "I will",
            "I'd": "I would",
            "you're": "you are",
            "you've": "you have",
            "you'll": "you will",
            "you'd": "you would",
            "he's": "he is",
            "he'll": "he will",
            "he'd": "he would",
            "she's": "she is",
            "she'll": "she will",
            "she'd": "she would",
            "it's": "it is",
            "it'll": "it will",
            "we're": "we are",
            "we've": "we have",
            "we'll": "we will",
            "we'd": "we would",
            "they're": "they are",
            "they've": "they have",
            "they'll": "they will",
            "they'd": "they would",
            "won't": "will not",
            "can't": "cannot",
            "couldn't": "could not",
            "wouldn't": "would not",
            "shouldn't": "should not",
            "didn't": "did not",
            "doesn't": "does not",
            "don't": "do not",
            "hasn't": "has not",
            "haven't": "have not",
            "hadn't": "had not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not"
        }
    
    def process_for_sync(self, original_text: str) -> NormalizedText:
        """
        Process text for synchronized TTS and subtitles.
        
        Args:
            original_text: The original Reddit text
            
        Returns:
            NormalizedText object with bidirectional mappings
        """
        self.logger.info(f"Processing text for sync: {len(original_text)} characters")
        
        # Initialize tracking
        tts_text = original_text
        mappings = []
        transformations = []
        
        # Apply transformations in order of priority
        
        # 1. Age/Gender patterns (highest priority for Reddit content)
        tts_text, age_mappings = self._transform_age_gender(tts_text, original_text)
        mappings.extend(age_mappings)
        if age_mappings:
            transformations.append({
                "type": "age_gender",
                "count": len(age_mappings),
                "examples": [f"{m.original_text} → {m.tts_text}" for m in age_mappings[:2]]
            })
        
        # 2. Currency
        tts_text, currency_mappings = self._transform_currency(tts_text, original_text)
        mappings.extend(currency_mappings)
        if currency_mappings:
            transformations.append({
                "type": "currency",
                "count": len(currency_mappings),
                "examples": [f"{m.original_text} → {m.tts_text}" for m in currency_mappings[:2]]
            })
        
        # 3. Reddit abbreviations
        tts_text, abbrev_mappings = self._transform_abbreviations(tts_text, original_text)
        mappings.extend(abbrev_mappings)
        if abbrev_mappings:
            transformations.append({
                "type": "abbreviations",
                "count": len(abbrev_mappings),
                "examples": [f"{m.original_text} → {m.tts_text}" for m in abbrev_mappings[:2]]
            })
        
        # 4. Numbers (ordinals, etc.)
        tts_text, number_mappings = self._transform_numbers(tts_text, original_text)
        mappings.extend(number_mappings)
        if number_mappings:
            transformations.append({
                "type": "numbers",
                "count": len(number_mappings),
                "examples": [f"{m.original_text} → {m.tts_text}" for m in number_mappings[:2]]
            })
        
        # 5. Contractions (optional - may want to keep for natural speech)
        # Commented out by default as contractions often sound more natural
        # tts_text, contraction_mappings = self._expand_contractions(tts_text, original_text)
        # mappings.extend(contraction_mappings)
        
        # Create word-level mappings for unchanged words
        word_mappings = self._create_word_mappings(original_text, tts_text, mappings)
        
        result = NormalizedText(
            original_text=original_text,
            tts_text=tts_text,
            word_mappings=word_mappings,
            transformation_log=transformations
        )
        
        self.logger.info(f"Text normalization complete: {len(transformations)} transformation types, {len(word_mappings)} word mappings")
        
        return result
    
    def _transform_age_gender(self, text: str, original: str) -> Tuple[str, List[TextMapping]]:
        """Transform age/gender patterns like (28F) to '28 female'."""
        mappings = []
        
        # Pattern for age/gender: (25M), (30F), etc.
        pattern = r'\((\d{1,2}[MFmf])\)'
        
        def replace_age_gender(match):
            age_gender = match.group(1)
            age = age_gender[:-1]
            gender = age_gender[-1].upper()
            
            if gender == 'M':
                replacement = f"{age} male"
            else:
                replacement = f"{age} female"
            
            # Track the mapping
            mapping = TextMapping(
                original_text=match.group(0),
                tts_text=replacement,
                original_start=match.start(),
                original_end=match.end(),
                tts_start=match.start(),  # Will be adjusted
                tts_end=match.start() + len(replacement),  # Will be adjusted
                transformation_type=TransformationType.AGE_GENDER
            )
            mappings.append(mapping)
            
            return replacement
        
        # Only transform if in appropriate context (not in URLs, etc.)
        if self._is_age_context(text):
            transformed = re.sub(pattern, replace_age_gender, text)
            
            # Adjust TTS positions based on cumulative length changes
            offset = 0
            for mapping in mappings:
                mapping.tts_start += offset
                mapping.tts_end = mapping.tts_start + len(mapping.tts_text)
                offset += len(mapping.tts_text) - len(mapping.original_text)
            
            return transformed, mappings
        
        return text, []
    
    def _transform_currency(self, text: str, original: str) -> Tuple[str, List[TextMapping]]:
        """Transform currency patterns like $50 to '50 dollars'."""
        mappings = []
        
        # Pattern for currency
        pattern = r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        
        def replace_currency(match):
            amount = match.group(1)
            replacement = f"{amount} dollars"
            
            mapping = TextMapping(
                original_text=match.group(0),
                tts_text=replacement,
                original_start=match.start(),
                original_end=match.end(),
                tts_start=match.start(),
                tts_end=match.start() + len(replacement),
                transformation_type=TransformationType.CURRENCY
            )
            mappings.append(mapping)
            
            return replacement
        
        transformed = re.sub(pattern, replace_currency, text)
        
        # Adjust positions
        offset = 0
        for mapping in mappings:
            mapping.tts_start += offset
            mapping.tts_end = mapping.tts_start + len(mapping.tts_text)
            offset += len(mapping.tts_text) - len(mapping.original_text)
        
        return transformed, mappings
    
    def _transform_abbreviations(self, text: str, original: str) -> Tuple[str, List[TextMapping]]:
        """Transform Reddit abbreviations to full forms."""
        mappings = []
        transformed = text
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_abbrevs = sorted(self.reddit_abbreviations.items(), 
                               key=lambda x: len(x[0]), reverse=True)
        
        for abbrev, full_form in sorted_abbrevs:
            # Use word boundaries to avoid partial matches
            pattern = rf'\b{re.escape(abbrev)}\b'
            
            matches = list(re.finditer(pattern, transformed))
            
            # Replace from end to beginning to maintain positions
            for match in reversed(matches):
                mapping = TextMapping(
                    original_text=abbrev,
                    tts_text=full_form,
                    original_start=match.start(),
                    original_end=match.end(),
                    tts_start=match.start(),
                    tts_end=match.start() + len(full_form),
                    transformation_type=TransformationType.ABBREVIATION
                )
                mappings.append(mapping)
                
                # Perform replacement
                transformed = (transformed[:match.start()] + 
                             full_form + 
                             transformed[match.end():])
        
        return transformed, mappings
    
    def _transform_numbers(self, text: str, original: str) -> Tuple[str, List[TextMapping]]:
        """Transform number patterns like 1st to 'first'."""
        mappings = []
        
        ordinals = {
            '1st': 'first', '2nd': 'second', '3rd': 'third',
            '4th': 'fourth', '5th': 'fifth', '6th': 'sixth',
            '7th': 'seventh', '8th': 'eighth', '9th': 'ninth',
            '10th': 'tenth', '11th': 'eleventh', '12th': 'twelfth',
            '13th': 'thirteenth', '14th': 'fourteenth', '15th': 'fifteenth',
            '16th': 'sixteenth', '17th': 'seventeenth', '18th': 'eighteenth',
            '19th': 'nineteenth', '20th': 'twentieth',
            '21st': 'twenty-first', '22nd': 'twenty-second', '23rd': 'twenty-third',
            '24th': 'twenty-fourth', '25th': 'twenty-fifth', '30th': 'thirtieth'
        }
        
        transformed = text
        
        for ordinal, word in ordinals.items():
            pattern = rf'\b{re.escape(ordinal)}\b'
            matches = list(re.finditer(pattern, transformed))
            
            for match in reversed(matches):
                mapping = TextMapping(
                    original_text=ordinal,
                    tts_text=word,
                    original_start=match.start(),
                    original_end=match.end(),
                    tts_start=match.start(),
                    tts_end=match.start() + len(word),
                    transformation_type=TransformationType.NUMBER
                )
                mappings.append(mapping)
                
                transformed = (transformed[:match.start()] + 
                             word + 
                             transformed[match.end():])
        
        return transformed, mappings
    
    def _is_age_context(self, text: str) -> bool:
        """Determine if text contains age-related context."""
        # Check for common age-related words near the pattern
        age_indicators = [
            'sister', 'brother', 'friend', 'roommate', 'coworker',
            'boyfriend', 'girlfriend', 'husband', 'wife', 'partner',
            'son', 'daughter', 'parent', 'mother', 'father',
            'years old', 'age', 'born', 'birthday'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in age_indicators)
    
    def _create_word_mappings(self, original: str, tts: str, 
                             existing_mappings: List[TextMapping]) -> List[TextMapping]:
        """Create complete word-level mappings including unchanged words."""
        # This is a simplified version - in production you'd want more sophisticated
        # word alignment algorithms
        
        # For now, return existing transformation mappings
        # In the future, this would create mappings for ALL words
        return existing_mappings
    
    def get_subtitle_text(self, normalized: NormalizedText, use_original: bool = False) -> str:
        """
        Get text for subtitles.
        
        Args:
            normalized: The normalized text object
            use_original: If True, use original text; if False, use TTS text
            
        Returns:
            Text formatted for subtitles
        """
        if use_original:
            return normalized.original_text
        else:
            return normalized.tts_text
    
    def map_word_position(self, normalized: NormalizedText, 
                         word_index: int, from_original: bool = True) -> Optional[int]:
        """
        Map word position between original and TTS text.
        
        Args:
            normalized: The normalized text object
            word_index: Word index in source text
            from_original: If True, map from original to TTS; else TTS to original
            
        Returns:
            Corresponding word index in target text, or None if not found
        """
        # Simplified implementation - would need more sophisticated mapping
        # in production using the word_mappings
        return word_index


def create_normalizer() -> BidirectionalTextNormalizer:
    """Factory function to create a text normalizer instance."""
    return BidirectionalTextNormalizer()