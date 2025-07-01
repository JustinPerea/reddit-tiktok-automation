"""
Hybrid TTS engine that intelligently selects the best provider
based on content analysis, quality requirements, and availability.
"""

from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
from loguru import logger

from .tts_engine import TTSEngine, TTSProvider, TTSRequest, TTSResult
from config.settings import get_settings


@dataclass
class TTSStrategy:
    """TTS provider selection strategy."""
    provider_priorities: List[TTSProvider]
    quality_threshold: float
    speed_preference: float
    cost_weight: float  # 0.0 = don't care about cost, 1.0 = minimize cost


class HybridTTSEngine:
    """
    Intelligent TTS engine that selects optimal providers based on:
    - Content quality score
    - Emotional content
    - Text length
    - Provider availability
    - Cost optimization
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.tts_engine = TTSEngine()
        self.logger = logger.bind(name="HybridTTS")
        
        # Define provider characteristics
        self.provider_specs = {
            TTSProvider.EDGE_TTS: {
                "quality": 0.9,
                "cost": 0.0,  # Free
                "reliability": 0.85,  # Requires internet
                "speed": 0.7,  # Moderate speed
                "emotional_range": 0.8,
                "best_for": ["high_quality", "emotional", "long_content"]
            },
            TTSProvider.GTTS: {
                "quality": 0.75,
                "cost": 0.0,  # Free
                "reliability": 0.8,  # Requires internet
                "speed": 0.8,  # Fast
                "emotional_range": 0.5,
                "best_for": ["standard_quality", "fast_processing", "reliable"]
            },
            TTSProvider.COQUI: {
                "quality": 0.85,
                "cost": 0.0,  # Free but resource intensive
                "reliability": 0.95,  # Offline
                "speed": 0.4,  # Slow, but high quality
                "emotional_range": 0.9,
                "best_for": ["premium_quality", "voice_cloning", "offline"]
            },
            TTSProvider.PYTTSX3: {
                "quality": 0.5,
                "cost": 0.0,  # Free
                "reliability": 1.0,  # Always available offline
                "speed": 0.9,  # Very fast
                "emotional_range": 0.3,
                "best_for": ["fallback", "testing", "simple_content"]
            }
        }
    
    def get_strategy_for_content(self, content_analysis: Dict) -> TTSStrategy:
        """
        Determine the best TTS strategy based on content analysis.
        
        Args:
            content_analysis: Output from ContentProcessor with quality scores
            
        Returns:
            TTSStrategy with provider priorities and preferences
        """
        quality_score = content_analysis.get("quality_score", 0.5)
        story_type = content_analysis.get("story_type", "general")
        word_count = content_analysis.get("word_count", 200)
        emotional_score = content_analysis.get("emotional_score", 0.3)
        
        # High quality content gets premium treatment
        if quality_score >= 0.8:
            return TTSStrategy(
                provider_priorities=[
                    TTSProvider.EDGE_TTS,
                    TTSProvider.COQUI,
                    TTSProvider.GTTS,
                    TTSProvider.PYTTSX3
                ],
                quality_threshold=0.8,
                speed_preference=0.5,  # Quality over speed
                cost_weight=0.0  # Don't worry about cost for high-quality content
            )
        
        # Emotional content benefits from better voice control
        elif emotional_score >= 0.6:
            return TTSStrategy(
                provider_priorities=[
                    TTSProvider.EDGE_TTS,
                    TTSProvider.COQUI,
                    TTSProvider.GTTS,
                    TTSProvider.PYTTSX3
                ],
                quality_threshold=0.7,
                speed_preference=0.6,
                cost_weight=0.2
            )
        
        # Long content needs reliability
        elif word_count > 400:
            return TTSStrategy(
                provider_priorities=[
                    TTSProvider.GTTS,
                    TTSProvider.EDGE_TTS,
                    TTSProvider.COQUI,
                    TTSProvider.PYTTSX3
                ],
                quality_threshold=0.6,
                speed_preference=0.7,
                cost_weight=0.3
            )
        
        # Standard content - balance quality and speed
        else:
            return TTSStrategy(
                provider_priorities=[
                    TTSProvider.GTTS,
                    TTSProvider.EDGE_TTS,
                    TTSProvider.PYTTSX3,
                    TTSProvider.COQUI
                ],
                quality_threshold=0.6,
                speed_preference=0.8,
                cost_weight=0.5
            )
    
    def select_voice_for_content(self, content_analysis: Dict, provider: TTSProvider) -> str:
        """
        Select the best voice for content based on story type and emotion.
        
        Args:
            content_analysis: Content analysis results
            provider: Selected TTS provider
            
        Returns:
            Voice identifier for the provider
        """
        story_type = content_analysis.get("story_type", "general")
        emotional_tone = content_analysis.get("dominant_emotion", "neutral")
        
        # Get available voices for provider
        if provider not in self.tts_engine.providers:
            return "default"
        
        tts_provider = self.tts_engine.providers[provider]
        
        # Provider-specific voice selection
        if provider == TTSProvider.EDGE_TTS:
            return self._select_edge_voice(story_type, emotional_tone)
        elif provider == TTSProvider.GTTS:
            return self._select_gtts_voice(story_type)
        elif provider == TTSProvider.COQUI:
            return self._select_coqui_voice(story_type, emotional_tone)
        elif provider == TTSProvider.PYTTSX3:
            return self._select_system_voice(story_type)
        
        return "default"
    
    def _select_edge_voice(self, story_type: str, emotion: str) -> str:
        """Select Edge TTS voice based on content."""
        # High-quality voice mapping for different content types
        voice_mapping = {
            ("aita", "neutral"): "en-US-AriaNeural",
            ("aita", "angry"): "en-US-DavisNeural",
            ("relationship", "sad"): "en-US-JennyNeural",
            ("relationship", "happy"): "en-US-AriaNeural",
            ("workplace", "professional"): "en-GB-SoniaNeural",
            ("family", "warm"): "en-AU-NatashaNeural",
            ("tifu", "embarrassed"): "en-US-GuyNeural",
        }
        
        key = (story_type, emotion)
        if key in voice_mapping:
            return voice_mapping[key]
        
        # Default high-quality voices by story type
        story_defaults = {
            "aita": "en-US-AriaNeural",
            "relationship": "en-US-JennyNeural",
            "workplace": "en-GB-SoniaNeural",
            "family": "en-AU-NatashaNeural",
            "tifu": "en-US-GuyNeural"
        }
        
        return story_defaults.get(story_type, "en-US-AriaNeural")
    
    def _select_gtts_voice(self, story_type: str) -> str:
        """Select gTTS language/accent based on content."""
        # gTTS uses language codes
        story_mapping = {
            "aita": "en",
            "relationship": "en",
            "workplace": "en-uk",  # More professional
            "family": "en-au",     # Friendly accent
            "tifu": "en-ca"        # Casual
        }
        
        return story_mapping.get(story_type, "en")
    
    def _select_coqui_voice(self, story_type: str, emotion: str) -> str:
        """Select Coqui TTS model based on content."""
        # Choose model based on emotional needs
        if emotion in ["angry", "sad", "surprised"]:
            return "tts_models/en/vctk/vits"  # Multi-speaker for emotion
        elif story_type in ["aita", "workplace"]:
            return "tts_models/en/ljspeech/glow-tts"  # Clear, professional
        else:
            return "tts_models/en/ljspeech/tacotron2-DDC"  # General purpose
    
    def _select_system_voice(self, story_type: str) -> str:
        """Select system voice based on content."""
        # This would need to be customized based on available system voices
        # For now, return a preference that can be checked against available voices
        if story_type in ["workplace", "aita"]:
            return "female"  # Look for female voice
        else:
            return "male"    # Look for male voice
    
    def synthesize_with_fallback(self, text: str, content_analysis: Dict, 
                                output_path: Optional[Path] = None) -> TTSResult:
        """
        Synthesize speech with intelligent provider selection and fallback.
        
        Args:
            text: Text to synthesize
            content_analysis: Analysis from ContentProcessor
            output_path: Optional output path
            
        Returns:
            TTSResult with best available quality
        """
        strategy = self.get_strategy_for_content(content_analysis)
        
        # Try providers in order of preference
        for provider in strategy.provider_priorities:
            if provider not in self.tts_engine.providers:
                self.logger.debug(f"Provider {provider.value} not available, skipping")
                continue
            
            # Select appropriate voice
            voice = self.select_voice_for_content(content_analysis, provider)
            
            # Create request
            request = TTSRequest(
                text=text,
                voice=voice,
                speed=1.0,  # Can be adjusted based on content
                output_path=output_path,
                provider_preferences=[provider]
            )
            
            # Attempt synthesis
            result = self.tts_engine.synthesize(request)
            
            if result.success:
                self.logger.info(f"TTS successful with {provider.value} (quality: {result.quality_score:.2f})")
                return result
            else:
                self.logger.warning(f"TTS failed with {provider.value}: {result.error_message}")
        
        # If all providers fail
        return TTSResult(
            success=False,
            audio_path=None,
            provider_used=None,
            duration=0.0,
            quality_score=0.0,
            error_message="All TTS providers failed"
        )
    
    def benchmark_providers(self, test_texts: List[str]) -> Dict[TTSProvider, Dict]:
        """
        Benchmark all available providers with test content.
        
        Args:
            test_texts: List of test texts to synthesize
            
        Returns:
            Performance metrics for each provider
        """
        results = {}
        
        for provider in self.tts_engine.get_available_providers():
            self.logger.info(f"Benchmarking {provider.value}")
            
            provider_results = {
                "success_rate": 0.0,
                "average_quality": 0.0,
                "average_duration": 0.0,
                "total_tests": len(test_texts),
                "successful_tests": 0,
                "failed_tests": 0,
                "error_messages": []
            }
            
            for text in test_texts:
                request = TTSRequest(
                    text=text,
                    voice="default",
                    provider_preferences=[provider]
                )
                
                result = self.tts_engine.synthesize(request)
                
                if result.success:
                    provider_results["successful_tests"] += 1
                    provider_results["average_quality"] += result.quality_score
                    provider_results["average_duration"] += result.duration
                else:
                    provider_results["failed_tests"] += 1
                    provider_results["error_messages"].append(result.error_message)
            
            # Calculate averages
            if provider_results["successful_tests"] > 0:
                provider_results["success_rate"] = provider_results["successful_tests"] / provider_results["total_tests"]
                provider_results["average_quality"] /= provider_results["successful_tests"]
                provider_results["average_duration"] /= provider_results["successful_tests"]
            
            results[provider] = provider_results
        
        return results
    
    def get_recommended_setup(self) -> Dict[str, str]:
        """Get recommendations for TTS setup based on available providers."""
        available = self.tts_engine.get_available_providers()
        
        recommendations = {
            "primary_provider": "None available",
            "fallback_provider": "None available", 
            "setup_commands": [],
            "quality_rating": "Unknown"
        }
        
        if TTSProvider.EDGE_TTS in available:
            recommendations["primary_provider"] = "Microsoft Edge TTS (Highest Quality)"
            recommendations["quality_rating"] = "Excellent"
        elif TTSProvider.GTTS in available:
            recommendations["primary_provider"] = "Google TTS (Good Quality)"
            recommendations["quality_rating"] = "Good"
        elif TTSProvider.COQUI in available:
            recommendations["primary_provider"] = "Coqui TTS (High Quality, Slow)"
            recommendations["quality_rating"] = "Very Good"
        
        if TTSProvider.PYTTSX3 in available:
            recommendations["fallback_provider"] = "System TTS (Always Available)"
        elif TTSProvider.GTTS in available and recommendations["primary_provider"] != "Google TTS":
            recommendations["fallback_provider"] = "Google TTS (Reliable)"
        
        # Setup commands for missing providers
        if TTSProvider.EDGE_TTS not in available:
            recommendations["setup_commands"].append("pip install edge-tts")
        if TTSProvider.GTTS not in available:
            recommendations["setup_commands"].append("pip install gtts")
        if TTSProvider.COQUI not in available:
            recommendations["setup_commands"].append("pip install TTS")
        
        return recommendations