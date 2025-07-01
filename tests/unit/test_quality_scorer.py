"""
Unit tests for QualityScorer.
"""

import pytest
from src.processors.quality_scorer import QualityScorer


class TestQualityScorer:
    """Test cases for QualityScorer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = QualityScorer()
    
    def test_calculate_score_high_quality(self):
        """Test quality score calculation for high-quality content."""
        high_quality_text = """
        I couldn't believe what happened yesterday at work. My boss, who I thought 
        was reasonable, completely lost it during our team meeting. He started 
        yelling at everyone for no reason and threw papers around the room. 
        I was shocked and didn't know what to do. But then something incredible 
        happened. Our HR manager walked in and witnessed the whole thing. 
        She immediately pulled him aside and we later found out he was suspended. 
        The whole office was buzzing with excitement. It turns out he had been 
        under investigation for months. Now we have a much better work environment 
        and everyone feels relieved. Sometimes justice really does prevail.
        """
        
        score = self.scorer.calculate_score(high_quality_text)
        assert 0.7 <= score <= 1.0  # Should be high quality
    
    def test_calculate_score_low_quality(self):
        """Test quality score calculation for low-quality content."""
        low_quality_text = "This is a very short and boring story with no emotion or structure."
        
        score = self.scorer.calculate_score(low_quality_text)
        assert 0.0 <= score <= 0.5  # Should be low quality
    
    def test_length_scoring_optimal(self):
        """Test length scoring for optimal word count."""
        # Create text with ~300 words (optimal range)
        optimal_text = " ".join(["word"] * 300)
        length_score = self.scorer._score_length(optimal_text)
        assert length_score == 1.0
    
    def test_length_scoring_too_short(self):
        """Test length scoring for too short content."""
        short_text = " ".join(["word"] * 50)
        length_score = self.scorer._score_length(short_text)
        assert length_score < 0.6
    
    def test_length_scoring_too_long(self):
        """Test length scoring for too long content."""
        long_text = " ".join(["word"] * 800)
        length_score = self.scorer._score_length(long_text)
        assert length_score < 0.6
    
    def test_emotional_engagement_high(self):
        """Test emotional engagement scoring with high emotion."""
        emotional_text = """
        I was absolutely furious and shocked when I discovered what my friend 
        had done. She was angry at me for no reason and said terrible things. 
        I couldn't believe how awful and horrible she was being. It was 
        incredible how someone could be so disgusting and outrageous.
        """
        
        emotion_score = self.scorer._score_emotional_engagement(emotional_text)
        assert emotion_score > 0.6
    
    def test_emotional_engagement_low(self):
        """Test emotional engagement scoring with low emotion."""
        neutral_text = """
        I went to the store today and bought some groceries. The weather was 
        okay and I met a person I knew. We talked about normal things and then 
        I went home. It was a regular day with nothing special happening.
        """
        
        emotion_score = self.scorer._score_emotional_engagement(neutral_text)
        assert emotion_score < 0.4
    
    def test_structure_scoring_good_structure(self):
        """Test structure scoring with good narrative structure."""
        structured_text = """
        So yesterday I went to meet my friend at the coffee shop. But when I 
        arrived, she wasn't there and I felt confused. However, I decided to 
        wait and see what would happen. Then she finally showed up an hour late. 
        In the end, we had a great conversation and worked everything out.
        """
        
        structure_score = self.scorer._score_structure(structured_text)
        assert structure_score > 0.6
    
    def test_structure_scoring_poor_structure(self):
        """Test structure scoring with poor narrative structure."""
        unstructured_text = """
        There are some things that happen sometimes. People do various activities 
        and situations occur in different ways. Things are the way they are and 
        that is how it works in general circumstances.
        """
        
        structure_score = self.scorer._score_structure(unstructured_text)
        assert structure_score < 0.4
    
    def test_readability_scoring_good(self):
        """Test readability scoring with good readability."""
        readable_text = """
        This is a story with good sentence structure. Each sentence has a 
        reasonable length. The words are not too complex. The punctuation 
        is appropriate for the content. This makes it easy to read and understand.
        """
        
        readability_score = self.scorer._score_readability(readable_text)
        assert readability_score > 0.7
    
    def test_readability_scoring_poor(self):
        """Test readability scoring with poor readability."""
        unreadable_text = """
        This sentence is extremely long and contains way too many words that 
        make it very difficult to read and understand because it goes on and 
        on without proper breaks or pauses which would make it much more 
        suitable for text-to-speech generation and overall comprehension by 
        the average reader who might be listening to this content.
        """
        
        readability_score = self.scorer._score_readability(unreadable_text)
        assert readability_score < 0.7
    
    def test_engagement_hooks_detection(self):
        """Test engagement hooks detection."""
        hook_text = """
        You won't believe what happened to me yesterday! Wait until you hear 
        this incredible story. Have you ever wondered what you would do in 
        this situation? Well, here's what happened next...
        """
        
        engagement_score = self.scorer._score_engagement_hooks(hook_text)
        assert engagement_score > 0.5
    
    def test_problem_solution_structure(self):
        """Test problem-solution structure detection."""
        problem_solution_text = """
        I had a terrible problem at work when my computer crashed and I lost 
        all my important files. The situation was really bad and I was worried 
        about meeting my deadline. But then I remembered I had a backup on 
        the cloud. I managed to recover everything and actually finished the 
        project early. The issue was completely resolved and I felt much better.
        """
        
        has_structure = self.scorer._has_problem_solution_structure(problem_solution_text)
        assert has_structure is True
    
    def test_detailed_analysis(self):
        """Test detailed analysis breakdown."""
        test_text = """
        I was shocked when my roommate told me she was angry about the dishes. 
        She said I never clean up, which isn't true. But then we talked about 
        it and worked out a cleaning schedule. Now everything is much better.
        """
        
        analysis = self.scorer.get_detailed_analysis(test_text)
        
        assert "length_score" in analysis
        assert "emotional_score" in analysis
        assert "structure_score" in analysis
        assert "readability_score" in analysis
        assert "engagement_score" in analysis
        assert "overall_score" in analysis
        
        # All scores should be between 0 and 1
        for score in analysis.values():
            assert 0.0 <= score <= 1.0
    
    def test_suggest_improvements(self):
        """Test improvement suggestions."""
        poor_text = "Short story. No emotion. Bad."
        
        suggestions = self.scorer.suggest_improvements(poor_text)
        assert len(suggestions) > 0
        assert any("word" in suggestion.lower() for suggestion in suggestions)
        assert any("emotion" in suggestion.lower() for suggestion in suggestions)