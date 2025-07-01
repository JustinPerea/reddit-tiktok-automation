"""
Quality scoring algorithm for Reddit content viral potential assessment.
"""

import re
import math
from typing import Dict, List
from loguru import logger


class QualityScorer:
    """Analyzes content quality and viral potential."""
    
    def __init__(self):
        self.logger = logger.bind(name="QualityScorer")
        
        # Emotional indicators that drive engagement
        self.emotional_words = {
            "anger": ["angry", "furious", "mad", "pissed", "outraged", "livid", "rage"],
            "surprise": ["shocked", "stunned", "amazed", "unbelievable", "incredible", "wow"],
            "joy": ["happy", "excited", "thrilled", "amazing", "wonderful", "love"],
            "sadness": ["sad", "depressed", "heartbroken", "devastated", "crying"],
            "fear": ["scared", "terrified", "worried", "anxious", "panic"],
            "disgust": ["disgusting", "gross", "awful", "terrible", "horrible"]
        }
        
        # Engagement hooks and patterns
        self.engagement_patterns = [
            r'\b(you won\'t believe|incredible|shocking|unbelievable)\b',
            r'\b(wait until you hear|listen to this|get this)\b',
            r'\b(plot twist|turns out|little did i know)\b',
            r'\b(am i wrong|what would you do|tell me)\b'
        ]
        
        # Story structure indicators
        self.structure_indicators = {
            "setup": [r'\b(so|basically|here\'s what happened|context)\b'],
            "conflict": [r'\b(but|however|then|suddenly|unfortunately)\b'],
            "resolution": [r'\b(finally|ended up|turned out|in the end|now)\b']
        }
    
    def calculate_score(self, text: str) -> float:
        """
        Calculate overall quality score (0.0 to 1.0).
        
        Args:
            text: Cleaned text to analyze
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        try:
            score = 0.0
            
            # Length optimization (30% weight)
            score += self._score_length(text) * 0.30
            
            # Emotional engagement (25% weight) 
            score += self._score_emotional_engagement(text) * 0.25
            
            # Story structure (20% weight)
            score += self._score_structure(text) * 0.20
            
            # Readability (15% weight)
            score += self._score_readability(text) * 0.15
            
            # Engagement hooks (10% weight)
            score += self._score_engagement_hooks(text) * 0.10
            
            # Ensure score is between 0 and 1
            final_score = max(0.0, min(1.0, score))
            
            self.logger.debug(f"Quality score calculated: {final_score:.3f}")
            return final_score
            
        except Exception as e:
            self.logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def get_detailed_analysis(self, text: str) -> Dict[str, float]:
        """Get detailed breakdown of quality metrics."""
        return {
            "length_score": self._score_length(text),
            "emotional_score": self._score_emotional_engagement(text),
            "structure_score": self._score_structure(text),
            "readability_score": self._score_readability(text),
            "engagement_score": self._score_engagement_hooks(text),
            "overall_score": self.calculate_score(text)
        }
    
    def _score_length(self, text: str) -> float:
        """Score based on optimal length for TikTok videos."""
        word_count = len(text.split())
        
        # Optimal range: 200-400 words (60-90 second videos)
        if 200 <= word_count <= 400:
            return 1.0
        elif 150 <= word_count <= 500:  # Acceptable range
            return 0.8
        elif 100 <= word_count <= 600:  # Marginal
            return 0.6
        elif word_count < 100:  # Too short
            return max(0.2, word_count / 100 * 0.6)
        else:  # Too long
            return max(0.2, 600 / word_count * 0.6)
    
    def _score_emotional_engagement(self, text: str) -> float:
        """Score based on emotional words and intensity."""
        text_lower = text.lower()
        word_count = len(text.split())
        
        if word_count == 0:
            return 0.0
        
        emotional_score = 0.0
        emotion_counts = {}
        
        # Count emotional words by category
        for emotion, words in self.emotional_words.items():
            count = sum(1 for word in words if word in text_lower)
            emotion_counts[emotion] = count
            
        # Calculate emotional intensity
        total_emotional_words = sum(emotion_counts.values())
        emotional_density = total_emotional_words / word_count
        
        # Higher scores for anger, surprise (most viral emotions)
        high_engagement_emotions = emotion_counts.get("anger", 0) + emotion_counts.get("surprise", 0)
        medium_engagement_emotions = emotion_counts.get("joy", 0) + emotion_counts.get("sadness", 0)
        
        # Scoring formula
        emotional_score = min(1.0, 
            (high_engagement_emotions * 0.3) +
            (medium_engagement_emotions * 0.2) +
            (emotional_density * 5.0)
        )
        
        return emotional_score
    
    def _score_structure(self, text: str) -> float:
        """Score based on narrative structure completeness."""
        structure_score = 0.0
        
        # Check for each structural element
        for element, patterns in self.structure_indicators.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    structure_score += 0.33  # Each element worth 1/3
                    break  # Only count each element once
        
        # Bonus for clear problem-solution structure
        if self._has_problem_solution_structure(text):
            structure_score += 0.2
        
        return min(1.0, structure_score)
    
    def _score_readability(self, text: str) -> float:
        """Score based on readability and TTS optimization."""
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return 0.0
        
        words = text.split()
        if not words:
            return 0.0
        
        # Average sentence length (optimal: 15-20 words)
        avg_sentence_length = len(words) / len([s for s in sentences if s.strip()])
        
        if 15 <= avg_sentence_length <= 20:
            length_score = 1.0
        elif 10 <= avg_sentence_length <= 25:
            length_score = 0.8
        else:
            length_score = 0.5
        
        # Syllable complexity (rough estimate)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        if 4 <= avg_word_length <= 6:  # Optimal for TTS
            complexity_score = 1.0
        elif 3 <= avg_word_length <= 7:
            complexity_score = 0.8
        else:
            complexity_score = 0.6
        
        # Punctuation appropriateness
        punct_ratio = len(re.findall(r'[.!?]', text)) / len(words)
        if 0.05 <= punct_ratio <= 0.15:  # Good punctuation density
            punct_score = 1.0
        else:
            punct_score = 0.7
        
        return (length_score + complexity_score + punct_score) / 3
    
    def _score_engagement_hooks(self, text: str) -> float:
        """Score based on engagement hooks and viral patterns."""
        hook_score = 0.0
        
        # Check for engagement patterns
        for pattern in self.engagement_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                hook_score += 0.25
        
        # Check for questions (encourage interaction)
        question_count = len(re.findall(r'\?', text))
        if question_count > 0:
            hook_score += min(0.3, question_count * 0.1)
        
        # Check for cliffhangers
        cliffhanger_patterns = [
            r'\b(wait|but here\'s the thing|plot twist|little did i know)\b',
            r'\b(you won\'t believe what happened next)\b'
        ]
        
        for pattern in cliffhanger_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                hook_score += 0.2
                break
        
        return min(1.0, hook_score)
    
    def _has_problem_solution_structure(self, text: str) -> bool:
        """Check if text has clear problem-solution structure."""
        # Look for problem indicators in first half
        first_half = text[:len(text)//2]
        problem_indicators = [
            r'\b(problem|issue|trouble|wrong|bad|terrible)\b',
            r'\b(happened|occurred|situation|drama)\b'
        ]
        
        has_problem = any(re.search(pattern, first_half, re.IGNORECASE) 
                         for pattern in problem_indicators)
        
        # Look for solution indicators in second half
        second_half = text[len(text)//2:]
        solution_indicators = [
            r'\b(solved|fixed|resolved|worked out|better)\b',
            r'\b(decided|chose|ended up|finally)\b'
        ]
        
        has_solution = any(re.search(pattern, second_half, re.IGNORECASE) 
                          for pattern in solution_indicators)
        
        return has_problem and has_solution
    
    def suggest_improvements(self, text: str) -> List[str]:
        """Suggest specific improvements to increase quality score."""
        suggestions = []
        analysis = self.get_detailed_analysis(text)
        
        if analysis["length_score"] < 0.7:
            word_count = len(text.split())
            if word_count < 150:
                suggestions.append("Add more detail and context to reach 200-400 words")
            else:
                suggestions.append("Consider shortening to 200-400 words for optimal engagement")
        
        if analysis["emotional_score"] < 0.6:
            suggestions.append("Add more emotional language to increase engagement")
            suggestions.append("Include words that convey strong emotions (anger, surprise, joy)")
        
        if analysis["structure_score"] < 0.7:
            suggestions.append("Improve story structure with clear beginning, conflict, and resolution")
            suggestions.append("Use transition words like 'but', 'then', 'finally'")
        
        if analysis["engagement_score"] < 0.5:
            suggestions.append("Add engagement hooks like 'You won't believe what happened'")
            suggestions.append("Include questions to encourage audience interaction")
        
        if analysis["readability_score"] < 0.7:
            suggestions.append("Simplify sentence structure for better text-to-speech")
            suggestions.append("Use shorter sentences (15-20 words each)")
        
        return suggestions