"""
Background Video Library Management System

Handles real background videos instead of procedurally generated placeholders.
Provides video selection, validation, and management functionality.
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger("BackgroundVideoLibrary")
settings = get_settings()


class VideoCategory(Enum):
    """Video categories for background content."""
    GAMING = "gaming"
    SATISFYING = "satisfying"
    NATURE = "nature"
    ABSTRACT = "abstract"
    LIFESTYLE = "lifestyle"


class VideoSubcategory(Enum):
    """Video subcategories within each main category."""
    # Gaming
    MINECRAFT_PARKOUR = "minecraft_parkour"
    SUBWAY_SURFERS = "subway_surfers"
    TEMPLE_RUN = "temple_run"
    FRUIT_NINJA = "fruit_ninja"
    
    # Satisfying
    SLIME_MIXING = "slime_mixing"
    KINETIC_SAND = "kinetic_sand"
    SOAP_CUTTING = "soap_cutting"
    
    # Nature
    RAIN_WINDOW = "rain_window"
    OCEAN_WAVES = "ocean_waves"
    FIREPLACE = "fireplace"
    
    # Abstract
    GEOMETRIC_PATTERNS = "geometric_patterns"
    COLOR_GRADIENTS = "color_gradients"
    PARTICLE_EFFECTS = "particle_effects"
    
    # Lifestyle
    COOKING_ASMR = "cooking_asmr"


@dataclass
class BackgroundVideo:
    """Represents a background video file."""
    path: Path
    category: VideoCategory
    subcategory: VideoSubcategory
    name: str
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    file_size: Optional[int] = None
    
    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return self.name.replace('_', ' ').title()
    
    @property
    def is_available(self) -> bool:
        """Check if video file exists and is accessible."""
        return self.path.exists() and self.path.is_file()


class BackgroundVideoLibrary:
    """Manages the background video library."""
    
    def __init__(self):
        """Initialize the background video library."""
        self.base_path = Path("assets/backgrounds")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Video cache for performance
        self._video_cache: Dict[VideoSubcategory, List[BackgroundVideo]] = {}
        self._last_scan_time = 0
        
        # Category to subcategory mapping
        self.category_mapping = {
            VideoCategory.GAMING: [
                VideoSubcategory.MINECRAFT_PARKOUR,
                VideoSubcategory.SUBWAY_SURFERS,
                VideoSubcategory.TEMPLE_RUN,
                VideoSubcategory.FRUIT_NINJA
            ],
            VideoCategory.SATISFYING: [
                VideoSubcategory.SLIME_MIXING,
                VideoSubcategory.KINETIC_SAND,
                VideoSubcategory.SOAP_CUTTING
            ],
            VideoCategory.NATURE: [
                VideoSubcategory.RAIN_WINDOW,
                VideoSubcategory.OCEAN_WAVES,
                VideoSubcategory.FIREPLACE
            ],
            VideoCategory.ABSTRACT: [
                VideoSubcategory.GEOMETRIC_PATTERNS,
                VideoSubcategory.COLOR_GRADIENTS,
                VideoSubcategory.PARTICLE_EFFECTS
            ],
            VideoCategory.LIFESTYLE: [
                VideoSubcategory.COOKING_ASMR
            ]
        }
        
        # Story type to subcategory recommendations
        self.story_recommendations = {
            "aita": [VideoSubcategory.SUBWAY_SURFERS, VideoSubcategory.SLIME_MIXING],
            "tifu": [VideoSubcategory.MINECRAFT_PARKOUR, VideoSubcategory.TEMPLE_RUN],
            "relationship": [VideoSubcategory.SUBWAY_SURFERS, VideoSubcategory.RAIN_WINDOW],
            "workplace": [VideoSubcategory.GEOMETRIC_PATTERNS, VideoSubcategory.PARTICLE_EFFECTS],
            "family": [VideoSubcategory.COOKING_ASMR, VideoSubcategory.FIREPLACE],
            "general": [VideoSubcategory.MINECRAFT_PARKOUR, VideoSubcategory.GEOMETRIC_PATTERNS]
        }
        
        logger.info("Background video library initialized")
    
    def scan_videos(self, force_rescan: bool = False) -> int:
        """Scan the background directory for available videos."""
        import time
        current_time = time.time()
        
        # Skip scan if recent and not forced
        if not force_rescan and (current_time - self._last_scan_time) < 300:  # 5 minutes
            return sum(len(videos) for videos in self._video_cache.values())
        
        self._video_cache.clear()
        video_count = 0
        
        for category in VideoCategory:
            category_path = self.base_path / category.value
            if not category_path.exists():
                continue
                
            for subcategory in self.category_mapping.get(category, []):
                subcategory_path = category_path / subcategory.value
                if not subcategory_path.exists():
                    continue
                
                videos = []
                for video_file in subcategory_path.glob("*.mp4"):
                    try:
                        video = BackgroundVideo(
                            path=video_file,
                            category=category,
                            subcategory=subcategory,
                            name=video_file.stem,
                            file_size=video_file.stat().st_size
                        )
                        videos.append(video)
                        video_count += 1
                    except Exception as e:
                        logger.warning(f"Error processing video {video_file}: {e}")
                
                if videos:
                    self._video_cache[subcategory] = videos
        
        self._last_scan_time = current_time
        logger.info(f"Scanned {video_count} background videos across {len(self._video_cache)} subcategories")
        return video_count
    
    def get_videos_by_subcategory(self, subcategory: VideoSubcategory) -> List[BackgroundVideo]:
        """Get all videos for a specific subcategory."""
        self.scan_videos()
        return self._video_cache.get(subcategory, [])
    
    def get_videos_by_category(self, category: VideoCategory) -> List[BackgroundVideo]:
        """Get all videos for a category."""
        self.scan_videos()
        videos = []
        for subcategory in self.category_mapping.get(category, []):
            videos.extend(self._video_cache.get(subcategory, []))
        return videos
    
    def get_random_video(self, 
                        subcategory: Optional[VideoSubcategory] = None,
                        category: Optional[VideoCategory] = None) -> Optional[BackgroundVideo]:
        """Get a random video, optionally filtered by subcategory or category."""
        self.scan_videos()
        
        if subcategory:
            videos = self.get_videos_by_subcategory(subcategory)
        elif category:
            videos = self.get_videos_by_category(category)
        else:
            # Get all videos
            videos = []
            for video_list in self._video_cache.values():
                videos.extend(video_list)
        
        available_videos = [v for v in videos if v.is_available]
        
        if not available_videos:
            logger.warning(f"No available videos found for {subcategory or category or 'any category'}")
            return None
        
        selected = random.choice(available_videos)
        logger.info(f"Selected random video: {selected.name} from {selected.subcategory.value}")
        return selected
    
    def suggest_video_for_story(self, story_type: str, emotional_score: float = 0.5) -> Optional[BackgroundVideo]:
        """Suggest optimal video based on story type and emotional context."""
        story_type = story_type.lower()
        
        # Get recommended subcategories for this story type
        recommended_subcategories = self.story_recommendations.get(story_type, 
                                                                  self.story_recommendations["general"])
        
        # Adjust based on emotional score
        if emotional_score > 0.7:  # High emotion - more engaging backgrounds
            if VideoSubcategory.SUBWAY_SURFERS in recommended_subcategories:
                recommended_subcategories = [VideoSubcategory.SUBWAY_SURFERS] + recommended_subcategories
        elif emotional_score < 0.3:  # Low emotion - calmer backgrounds
            recommended_subcategories.extend([VideoSubcategory.RAIN_WINDOW, VideoSubcategory.OCEAN_WAVES])
        
        # Try to find a video from recommended subcategories
        for subcategory in recommended_subcategories:
            video = self.get_random_video(subcategory=subcategory)
            if video:
                logger.info(f"Suggested {video.name} for {story_type} story (emotion: {emotional_score:.2f})")
                return video
        
        # Fallback to any available video
        fallback = self.get_random_video()
        if fallback:
            logger.info(f"Using fallback video {fallback.name} for {story_type} story")
        
        return fallback
    
    def get_library_stats(self) -> Dict[str, any]:
        """Get statistics about the video library."""
        self.scan_videos()
        
        stats = {
            "total_videos": 0,
            "categories": {},
            "subcategories": {},
            "total_size_mb": 0
        }
        
        for subcategory, videos in self._video_cache.items():
            category = None
            for cat, subcat_list in self.category_mapping.items():
                if subcategory in subcat_list:
                    category = cat
                    break
            
            if category:
                if category.value not in stats["categories"]:
                    stats["categories"][category.value] = 0
                stats["categories"][category.value] += len(videos)
            
            stats["subcategories"][subcategory.value] = len(videos)
            stats["total_videos"] += len(videos)
            
            # Calculate total size
            for video in videos:
                if video.file_size:
                    stats["total_size_mb"] += video.file_size / (1024 * 1024)
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats
    
    def validate_library(self) -> Dict[str, any]:
        """Validate the video library and report issues."""
        self.scan_videos()
        
        validation = {
            "valid_videos": 0,
            "missing_videos": 0,
            "empty_subcategories": [],
            "issues": []
        }
        
        for category in VideoCategory:
            for subcategory in self.category_mapping.get(category, []):
                videos = self.get_videos_by_subcategory(subcategory)
                
                if not videos:
                    validation["empty_subcategories"].append(subcategory.value)
                    validation["issues"].append(f"No videos found in {subcategory.value}")
                else:
                    for video in videos:
                        if video.is_available:
                            validation["valid_videos"] += 1
                        else:
                            validation["missing_videos"] += 1
                            validation["issues"].append(f"Missing video: {video.path}")
        
        return validation


# Convenience function for creating the library instance
def create_background_video_library() -> BackgroundVideoLibrary:
    """Create and return a background video library instance."""
    return BackgroundVideoLibrary()