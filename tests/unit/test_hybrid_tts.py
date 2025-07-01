"""
Unit tests for Hybrid TTS Engine.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.generators.hybrid_tts import HybridTTSEngine, TTSStrategy
from src.generators.tts_engine import TTSProvider, TTSRequest, TTSResult


class TestHybridTTSEngine:
    """Test cases for HybridTTSEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tts_engine = HybridTTSEngine()
    
    def test_strategy_for_high_quality_content(self):
        """Test strategy selection for high-quality content."""
        content_analysis = {
            "quality_score": 0.9,
            "story_type": "aita",
            "word_count": 300,
            "emotional_score": 0.7
        }
        
        strategy = self.tts_engine.get_strategy_for_content(content_analysis)
        
        assert strategy.provider_priorities[0] == TTSProvider.EDGE_TTS
        assert strategy.quality_threshold >= 0.8
        assert strategy.cost_weight == 0.0  # Don't worry about cost for high quality
    
    def test_strategy_for_emotional_content(self):
        """Test strategy selection for emotional content."""
        content_analysis = {
            "quality_score": 0.6,
            "story_type": "relationship",
            "word_count": 250,
            "emotional_score": 0.8
        }
        
        strategy = self.tts_engine.get_strategy_for_content(content_analysis)
        
        assert TTSProvider.EDGE_TTS in strategy.provider_priorities[:2]
        assert strategy.quality_threshold >= 0.7
    
    def test_strategy_for_long_content(self):
        """Test strategy selection for long content."""
        content_analysis = {
            "quality_score": 0.6,
            "story_type": "tifu",
            "word_count": 500,
            "emotional_score": 0.4
        }
        
        strategy = self.tts_engine.get_strategy_for_content(content_analysis)
        
        # Long content should prioritize reliability
        assert strategy.provider_priorities[0] == TTSProvider.GTTS
        assert strategy.speed_preference >= 0.7
    
    def test_strategy_for_standard_content(self):
        """Test strategy selection for standard content."""
        content_analysis = {
            "quality_score": 0.5,
            "story_type": "general",
            "word_count": 200,
            "emotional_score": 0.3
        }
        
        strategy = self.tts_engine.get_strategy_for_content(content_analysis)
        
        # Standard content should balance quality and speed
        assert strategy.provider_priorities[0] == TTSProvider.GTTS
        assert strategy.cost_weight >= 0.5
    
    def test_edge_voice_selection(self):
        """Test Edge TTS voice selection based on content."""
        # Test AITA content with neutral emotion
        voice = self.tts_engine._select_edge_voice("aita", "neutral")
        assert voice == "en-US-AriaNeural"
        
        # Test relationship content with sad emotion
        voice = self.tts_engine._select_edge_voice("relationship", "sad")
        assert voice == "en-US-JennyNeural"
        
        # Test workplace content
        voice = self.tts_engine._select_edge_voice("workplace", "professional")
        assert voice == "en-GB-SoniaNeural"
    
    def test_gtts_voice_selection(self):
        """Test Google TTS voice selection."""
        # Test different story types
        voice = self.tts_engine._select_gtts_voice("workplace")
        assert voice == "en-uk"  # Professional accent
        
        voice = self.tts_engine._select_gtts_voice("family")
        assert voice == "en-au"  # Friendly accent
        
        voice = self.tts_engine._select_gtts_voice("aita")
        assert voice == "en"  # Standard English
    
    def test_coqui_voice_selection(self):
        """Test Coqui TTS voice selection."""
        # Test emotional content
        voice = self.tts_engine._select_coqui_voice("aita", "angry")
        assert "vctk" in voice  # Multi-speaker model for emotion
        
        # Test professional content
        voice = self.tts_engine._select_coqui_voice("workplace", "neutral")
        assert "glow-tts" in voice  # Clear, professional model
    
    @patch('src.generators.hybrid_tts.HybridTTSEngine.tts_engine')
    def test_synthesize_with_fallback_success(self, mock_tts_engine):
        """Test successful synthesis with fallback system."""
        # Mock successful result
        mock_result = TTSResult(
            success=True,
            audio_path=Path("/tmp/test.mp3"),
            provider_used=TTSProvider.GTTS,
            duration=10.0,
            quality_score=0.75
        )
        mock_tts_engine.synthesize.return_value = mock_result
        
        content_analysis = {
            "quality_score": 0.6,
            "story_type": "general",
            "word_count": 200,
            "emotional_score": 0.3
        }
        
        result = self.tts_engine.synthesize_with_fallback(
            "Test text", content_analysis
        )
        
        assert result.success is True
        assert result.provider_used == TTSProvider.GTTS
        assert result.quality_score == 0.75
    
    @patch('src.generators.hybrid_tts.HybridTTSEngine.tts_engine')
    def test_synthesize_with_fallback_failure(self, mock_tts_engine):
        """Test fallback behavior when all providers fail."""
        # Mock failed result for all providers
        mock_result = TTSResult(
            success=False,
            audio_path=None,
            provider_used=TTSProvider.GTTS,
            duration=0.0,
            quality_score=0.0,
            error_message="Provider failed"
        )
        mock_tts_engine.synthesize.return_value = mock_result
        
        content_analysis = {
            "quality_score": 0.6,
            "story_type": "general", 
            "word_count": 200,
            "emotional_score": 0.3
        }
        
        result = self.tts_engine.synthesize_with_fallback(
            "Test text", content_analysis
        )
        
        assert result.success is False
        assert "All TTS providers failed" in result.error_message
    
    def test_provider_specs_structure(self):
        """Test that provider specifications are properly structured."""
        for provider, specs in self.tts_engine.provider_specs.items():
            assert "quality" in specs
            assert "cost" in specs
            assert "reliability" in specs
            assert "speed" in specs
            assert "emotional_range" in specs
            assert "best_for" in specs
            
            # Check value ranges
            assert 0.0 <= specs["quality"] <= 1.0
            assert 0.0 <= specs["reliability"] <= 1.0
            assert 0.0 <= specs["speed"] <= 1.0
            assert 0.0 <= specs["emotional_range"] <= 1.0
            assert isinstance(specs["best_for"], list)
    
    def test_recommended_setup_generation(self):
        """Test recommendation generation based on available providers."""
        recommendations = self.tts_engine.get_recommended_setup()
        
        assert "primary_provider" in recommendations
        assert "fallback_provider" in recommendations
        assert "setup_commands" in recommendations
        assert "quality_rating" in recommendations
        
        # Should be lists of strings
        assert isinstance(recommendations["setup_commands"], list)
    
    @patch('src.generators.hybrid_tts.HybridTTSEngine.tts_engine')
    def test_benchmark_providers(self, mock_tts_engine):
        """Test provider benchmarking functionality."""
        # Mock some providers as available
        mock_tts_engine.get_available_providers.return_value = [
            TTSProvider.GTTS, TTSProvider.PYTTSX3
        ]
        
        # Mock successful synthesis results
        mock_result = TTSResult(
            success=True,
            audio_path=Path("/tmp/test.mp3"),
            provider_used=TTSProvider.GTTS,
            duration=5.0,
            quality_score=0.75
        )
        mock_tts_engine.synthesize.return_value = mock_result
        
        test_texts = ["Hello world", "This is a test"]
        results = self.tts_engine.benchmark_providers(test_texts)
        
        assert len(results) == 2  # Two providers
        for provider, metrics in results.items():
            assert "success_rate" in metrics
            assert "average_quality" in metrics
            assert "total_tests" in metrics
            assert metrics["total_tests"] == len(test_texts)


class TestTTSStrategy:
    """Test cases for TTSStrategy class."""
    
    def test_strategy_creation(self):
        """Test TTSStrategy creation and attributes."""
        strategy = TTSStrategy(
            provider_priorities=[TTSProvider.GTTS, TTSProvider.EDGE_TTS],
            quality_threshold=0.7,
            speed_preference=0.8,
            cost_weight=0.3
        )
        
        assert len(strategy.provider_priorities) == 2
        assert strategy.provider_priorities[0] == TTSProvider.GTTS
        assert strategy.quality_threshold == 0.7
        assert strategy.speed_preference == 0.8
        assert strategy.cost_weight == 0.3
    
    def test_strategy_defaults(self):
        """Test TTSStrategy with various parameter combinations."""
        # Test with minimal parameters
        strategy = TTSStrategy(
            provider_priorities=[TTSProvider.GTTS],
            quality_threshold=0.5,
            speed_preference=1.0,
            cost_weight=0.0
        )
        
        assert len(strategy.provider_priorities) == 1
        assert 0.0 <= strategy.quality_threshold <= 1.0
        assert 0.0 <= strategy.speed_preference <= 1.0
        assert 0.0 <= strategy.cost_weight <= 1.0