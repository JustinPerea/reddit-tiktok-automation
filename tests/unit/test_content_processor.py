"""
Unit tests for ContentProcessor.
"""

import pytest
from src.processors.content_processor import ContentProcessor, ContentValidation


class TestContentProcessor:
    """Test cases for ContentProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ContentProcessor()
    
    def test_basic_validation_valid_content(self):
        """Test basic validation with valid content."""
        valid_text = "This is a valid story with enough content to pass basic validation checks."
        result = self.processor._basic_validation(valid_text)
        assert result is True
    
    def test_basic_validation_empty_content(self):
        """Test basic validation with empty content."""
        empty_text = ""
        result = self.processor._basic_validation(empty_text)
        assert result is False
    
    def test_basic_validation_too_short(self):
        """Test basic validation with too short content."""
        short_text = "Too short"
        result = self.processor._basic_validation(short_text)
        assert result is False
    
    def test_narrative_structure_detection(self):
        """Test narrative structure detection."""
        story_text = """
        Yesterday I went to work and something crazy happened. 
        My boyfriend called me and told me he was angry about something. 
        I felt so confused and didn't know what to do.
        """
        result = self.processor._has_narrative_structure(story_text)
        assert result is True
    
    def test_story_type_detection_aita(self):
        """Test AITA story type detection."""
        aita_text = "AITA for telling my friend the truth about her boyfriend?"
        story_type = self.processor._detect_story_type(aita_text)
        assert story_type == "aita"
    
    def test_story_type_detection_relationship(self):
        """Test relationship story type detection."""
        relationship_text = "My boyfriend and I have been dating for two years..."
        story_type = self.processor._detect_story_type(relationship_text)
        assert story_type == "relationship"
    
    def test_voice_suggestion(self):
        """Test voice suggestion based on content."""
        aita_text = "AITA for doing something?"
        suggested_voice = self.processor._suggest_voice(aita_text, "aita")
        assert suggested_voice == "alloy"
    
    def test_duration_estimation(self):
        """Test video duration estimation."""
        # ~150 words should be about 60 seconds
        text = " ".join(["word"] * 150)
        duration = self.processor._estimate_duration(text)
        assert 50 <= duration <= 80  # Allow some variance
    
    def test_inappropriate_content_detection(self):
        """Test inappropriate content detection."""
        inappropriate_text = "I want to kill myself and end it all"
        result = self.processor._contains_inappropriate_content(inappropriate_text)
        assert result is True
        
        appropriate_text = "I was really sad about the situation"
        result = self.processor._contains_inappropriate_content(appropriate_text)
        assert result is False
    
    def test_tts_friendly_check(self):
        """Test TTS-friendly content check."""
        tts_friendly = "This is a normal story with regular words and good structure."
        result = self.processor._is_tts_friendly(tts_friendly)
        assert result is True
        
        tts_unfriendly = "OMG WTF BBQ!!! $$$$ #### LOL ROFL!!!"
        result = self.processor._is_tts_friendly(tts_unfriendly)
        assert result is False
    
    def test_content_validation_valid(self):
        """Test content validation with valid content."""
        valid_content = """
        Yesterday I had the most incredible experience at work. My coworker Sarah, 
        who I thought was my friend, completely threw me under the bus during a 
        meeting with our boss. I couldn't believe what was happening. She told 
        our manager that I had been slacking off, which wasn't true at all. 
        I felt so angry and betrayed. But then something amazing happened. 
        Our boss actually stood up for me and said that my work had been excellent. 
        He told Sarah that her accusations were unprofessional. In the end, 
        Sarah had to apologize to me in front of the whole team. I learned that 
        sometimes people show their true colors when you least expect it.
        """
        
        validation = self.processor.validate_content(valid_content)
        assert validation.is_valid is True
        assert validation.quality_score > 0.5
        assert 100 < validation.word_count < 600
    
    def test_content_validation_too_short(self):
        """Test content validation with too short content."""
        short_content = "This is way too short."
        
        validation = self.processor.validate_content(short_content)
        assert validation.is_valid is False
        assert any("too short" in issue.lower() for issue in validation.issues)
    
    def test_process_valid_content(self):
        """Test full processing pipeline with valid content."""
        valid_story = """
        AITA for calling out my roommate's girlfriend? 
        
        So basically, I live with my best friend Jake and his girlfriend Emma 
        has been staying over constantly. She never cleans up after herself, 
        eats our food, and is generally just really inconsiderate. 
        
        Yesterday I came home and she had used all my expensive shampoo and 
        left the bottle empty in the shower. I was so angry because I just 
        bought it and specifically asked her not to use my stuff. 
        
        When I confronted her about it, she just shrugged and said "it's just 
        shampoo, buy more." I couldn't believe how dismissive she was being. 
        So I told her that she was being disrespectful and needed to replace 
        my shampoo or stop using my things. 
        
        Now Jake is mad at me for "attacking" his girlfriend and says I'm 
        being petty. But I don't think I'm wrong for standing up for myself. 
        AITA?
        
        Edit: Thanks for all the responses, I talked to Jake and we worked it out.
        """
        
        result = self.processor.process(valid_story)
        assert result is not None
        assert result.validation.is_valid is True
        assert len(result.cleaned_text) > 0
        assert len(result.tts_optimized_text) > 0
        assert result.metadata["story_type"] == "aita"
        assert result.estimated_duration > 0
    
    def test_process_invalid_content(self):
        """Test processing with invalid content."""
        invalid_content = "Too short"
        
        result = self.processor.process(invalid_content)
        assert result is None