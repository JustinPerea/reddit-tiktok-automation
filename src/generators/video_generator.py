"""
Video generation engine for creating TikTok-style videos from processed content and TTS audio.
Handles background videos, text overlays, and final video assembly.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import random
import math

from utils.logger import get_logger
from config.settings import get_settings
from generators.background_library import BackgroundLibrary, BackgroundStyle

logger = get_logger("VideoGenerator")
settings = get_settings()


class VideoFormat(Enum):
    """Supported video output formats."""
    TIKTOK = "tiktok"  # 9:16 aspect ratio, 1080x1920
    INSTAGRAM_REEL = "instagram_reel"  # 9:16 aspect ratio, 1080x1920
    YOUTUBE_SHORT = "youtube_short"  # 9:16 aspect ratio, 1080x1920
    SQUARE = "square"  # 1:1 aspect ratio, 1080x1080


# Legacy BackgroundType for compatibility - now using BackgroundStyle from library
class BackgroundType(Enum):
    """Types of background content - Legacy compatibility."""
    MINECRAFT_PARKOUR = "minecraft_parkour"
    SUBWAY_SURFERS = "subway_surfers"
    SATISFYING_SLIME = "slime_mixing"
    COOKING_ASMR = "cooking_asmr"
    NATURE_SCENES = "ocean_waves"
    GEOMETRIC_PATTERNS = "geometric_patterns"


@dataclass
class VideoConfig:
    """Configuration for video generation."""
    format: VideoFormat = VideoFormat.TIKTOK
    background_type: BackgroundType = BackgroundType.MINECRAFT_PARKOUR
    text_color: str = "#FFFFFF"
    text_outline_color: str = "#000000"
    text_font: str = "Arial-Bold"
    text_size: int = 48
    text_position: str = "center"  # top, center, bottom
    fade_duration: float = 0.5  # seconds
    background_blur: bool = False
    background_dim: float = 0.3  # 0.0 to 1.0
    enable_captions: bool = True
    caption_highlight: bool = True


@dataclass
class VideoResult:
    """Result of video generation."""
    success: bool
    video_path: Optional[Path] = None
    duration: float = 0.0
    format: Optional[VideoFormat] = None
    file_size: int = 0  # bytes
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class VideoGenerator:
    """Generates TikTok-style videos from content and audio."""
    
    def __init__(self):
        """Initialize the video generator."""
        self.temp_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_videos"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize background library
        self.background_library = BackgroundLibrary()
        
        # Video specifications for different formats
        self.format_specs = {
            VideoFormat.TIKTOK: {"width": 1080, "height": 1920, "fps": 30},
            VideoFormat.INSTAGRAM_REEL: {"width": 1080, "height": 1920, "fps": 30},
            VideoFormat.YOUTUBE_SHORT: {"width": 1080, "height": 1920, "fps": 30},
            VideoFormat.SQUARE: {"width": 1080, "height": 1080, "fps": 30}
        }
        
        # Check FFmpeg availability
        self._check_ffmpeg()
        
        logger.info("Video generator initialized with enhanced background library")
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                logger.info("FFmpeg found and available")
                return True
            else:
                logger.warning("FFmpeg not available - video generation will fail")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("FFmpeg not found - install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)")
            return False
    
    def generate_video(
        self, 
        audio_path: Path, 
        text: str,
        config: VideoConfig = None,
        output_path: Optional[Path] = None
    ) -> VideoResult:
        """Generate a complete video from audio and text."""
        if config is None:
            config = VideoConfig()
        
        try:
            logger.info(f"Starting video generation for {len(text)} character text")
            
            # Get audio duration
            audio_duration = self._get_audio_duration(audio_path)
            if audio_duration <= 0:
                return VideoResult(
                    success=False,
                    error_message="Invalid audio file or duration"
                )
            
            # Create background video
            background_path = self._create_background_video(audio_duration, config)
            if not background_path:
                return VideoResult(
                    success=False,
                    error_message="Failed to create background video"
                )
            
            # Combine all elements (text is applied directly to background)
            final_video = self._assemble_final_video(
                background_path, 
                text, 
                audio_path, 
                config,
                output_path
            )
            
            if not final_video or not final_video.exists():
                return VideoResult(
                    success=False,
                    error_message="Failed to assemble final video"
                )
            
            # Get video metadata
            metadata = self._get_video_metadata(final_video)
            file_size = final_video.stat().st_size
            
            logger.info(f"Video generation successful: {final_video}")
            
            return VideoResult(
                success=True,
                video_path=final_video,
                duration=audio_duration,
                format=config.format,
                file_size=file_size,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return VideoResult(
                success=False,
                error_message=f"Video generation error: {str(e)}"
            )
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get the duration of an audio file."""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", str(audio_path)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                logger.error(f"Failed to get audio duration: {result.stderr}")
                return 0.0
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0
    
    def _create_background_video(self, duration: float, config: VideoConfig) -> Optional[Path]:
        """Create or select background video using the enhanced background library."""
        try:
            specs = self.format_specs[config.format]
            
            # Convert legacy BackgroundType to BackgroundStyle
            background_style_map = {
                BackgroundType.MINECRAFT_PARKOUR: BackgroundStyle.MINECRAFT_PARKOUR,
                BackgroundType.SUBWAY_SURFERS: BackgroundStyle.SUBWAY_SURFERS,
                BackgroundType.SATISFYING_SLIME: BackgroundStyle.SLIME_MIXING,
                BackgroundType.COOKING_ASMR: BackgroundStyle.COOKING_ASMR,
                BackgroundType.NATURE_SCENES: BackgroundStyle.OCEAN_WAVES,
                BackgroundType.GEOMETRIC_PATTERNS: BackgroundStyle.GEOMETRIC_PATTERNS
            }
            
            # Get the appropriate background style
            background_style = background_style_map.get(config.background_type, BackgroundStyle.GEOMETRIC_PATTERNS)
            
            # Use the background library to generate the video
            background_path = self.background_library.generate_background(
                style=background_style,
                duration=duration,
                video_specs=specs
            )
            
            if background_path and background_path.exists():
                logger.info(f"Background video created using library: {background_path}")
                return background_path
            else:
                logger.warning(f"Background library failed, falling back to simple generation")
                return self._create_simple_background(duration, config, specs)
                
        except Exception as e:
            logger.error(f"Error creating background video: {e}")
            return self._create_simple_background(duration, config, specs)
    
    def _create_simple_background(self, duration: float, config: VideoConfig, specs: Dict[str, Any]) -> Optional[Path]:
        """Create a simple fallback background video."""
        try:
            output_path = self.temp_dir / f"simple_background_{random.randint(1000, 9999)}.mp4"
            
            # Simple gradient background as fallback
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x667eea:size={specs['width']}x{specs['height']}:duration={duration},"
                       f"fade=t=in:st=0:d=0.5:alpha=1,fade=t=out:st={duration-0.5}:d=0.5:alpha=1",
                "-r", str(specs['fps']),
                "-c:v", "libx264",
                "-preset", "fast",
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Simple background video created: {output_path}")
                return output_path
            else:
                logger.error(f"Failed to create simple background video: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating simple background video: {e}")
            return None
    
    def _create_text_overlay(self, text: str, duration: float, config: VideoConfig) -> Optional[Path]:
        """Create text overlay video with word-by-word highlighting."""
        try:
            specs = self.format_specs[config.format]
            output_path = self.temp_dir / f"text_overlay_{random.randint(1000, 9999)}.mp4"
            
            # Split text into words for timing
            words = text.split()
            words_per_second = len(words) / duration
            
            # Escape text for FFmpeg drawtext filter
            escaped_text = (text
                .replace("\\", "\\\\")  # Escape backslashes first
                .replace("'", "\\'")    # Escape single quotes
                .replace(":", "\\:")    # Escape colons
                .replace("%", "\\%")    # Escape percent signs
                .replace("[", "\\[")    # Escape square brackets
                .replace("]", "\\]")    # Escape square brackets
                .replace(",", "\\,")    # Escape commas
                .replace(";", "\\;")    # Escape semicolons
                .replace("$", "\\$")    # Escape dollar signs
            )
            
            # Calculate text positioning
            if config.text_position == "top":
                y_pos = specs['height'] * 0.2
            elif config.text_position == "bottom":
                y_pos = specs['height'] * 0.8
            else:  # center
                y_pos = specs['height'] * 0.5
            
            # Create text overlay with outline
            text_filter = (
                f"drawtext=text='{escaped_text}':"
                f"fontfile=/System/Library/Fonts/Helvetica.ttc:"
                f"fontsize={config.text_size}:"
                f"fontcolor={config.text_color}:"
                f"borderw=3:"
                f"bordercolor={config.text_outline_color}:"
                f"x=(w-text_w)/2:"
                f"y={y_pos}:"
                f"box=1:"
                f"boxcolor=black@0.3:"
                f"boxborderw=10"
            )
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=black@0.0:size={specs['width']}x{specs['height']}:duration={duration}",
                "-vf", text_filter,
                "-r", str(specs['fps']),
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Text overlay created: {output_path}")
                return output_path
            else:
                logger.error(f"Failed to create text overlay: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating text overlay: {e}")
            return None
    
    def _assemble_final_video(
        self, 
        background_path: Path, 
        text: str,
        audio_path: Path,
        config: VideoConfig,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """Assemble final video by applying text directly to background."""
        try:
            if output_path is None:
                output_path = self.temp_dir / f"final_video_{random.randint(1000, 9999)}.mp4"
            
            specs = self.format_specs[config.format]
            
            # Escape text for FFmpeg drawtext filter
            escaped_text = (text
                .replace("\\", "\\\\")  # Escape backslashes first
                .replace("'", "\\'")    # Escape single quotes
                .replace(":", "\\:")    # Escape colons
                .replace("%", "\\%")    # Escape percent signs
                .replace("[", "\\[")    # Escape square brackets
                .replace("]", "\\]")    # Escape square brackets
                .replace(",", "\\,")    # Escape commas
                .replace(";", "\\;")    # Escape semicolons
                .replace("$", "\\$")    # Escape dollar signs
            )
            
            # Calculate text positioning
            if config.text_position == "top":
                y_pos = specs['height'] * 0.2
            elif config.text_position == "bottom":
                y_pos = specs['height'] * 0.8
            else:  # center
                y_pos = specs['height'] * 0.5
            
            # Create text filter for direct application to background
            text_filter = (
                f"drawtext=text='{escaped_text}':"
                f"fontfile=/System/Library/Fonts/Helvetica.ttc:"
                f"fontsize={config.text_size}:"
                f"fontcolor={config.text_color}:"
                f"borderw=3:"
                f"bordercolor={config.text_outline_color}:"
                f"x=(w-text_w)/2:"
                f"y={y_pos}:"
                f"box=1:"
                f"boxcolor=black@0.3:"
                f"boxborderw=10"
            )
            
            # Apply text directly to background video with audio
            cmd = [
                "ffmpeg", "-y",
                "-i", str(background_path),  # Background video
                "-i", str(audio_path),       # Audio
                "-vf", text_filter,          # Apply text directly to background
                "-map", "0:v",               # Use video from background
                "-map", "1:a",               # Use audio from audio file
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "medium",
                "-crf", "23",
                "-r", str(specs['fps']),
                "-s", f"{specs['width']}x{specs['height']}",
                "-movflags", "+faststart",
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Final video assembled: {output_path}")
                return output_path
            else:
                logger.error(f"Failed to assemble final video: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error assembling final video: {e}")
            return None
    
    def _get_video_metadata(self, video_path: Path) -> Dict[str, Any]:
        """Get metadata from generated video."""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(video_path)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                
                # Extract useful information
                format_info = metadata.get("format", {})
                video_stream = None
                audio_stream = None
                
                for stream in metadata.get("streams", []):
                    if stream.get("codec_type") == "video" and video_stream is None:
                        video_stream = stream
                    elif stream.get("codec_type") == "audio" and audio_stream is None:
                        audio_stream = stream
                
                return {
                    "duration": float(format_info.get("duration", 0)),
                    "size": int(format_info.get("size", 0)),
                    "bit_rate": int(format_info.get("bit_rate", 0)),
                    "video_codec": video_stream.get("codec_name") if video_stream else None,
                    "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
                    "width": int(video_stream.get("width", 0)) if video_stream else 0,
                    "height": int(video_stream.get("height", 0)) if video_stream else 0,
                    "fps": eval(video_stream.get("r_frame_rate", "0/1")) if video_stream else 0
                }
            else:
                logger.warning(f"Failed to get video metadata: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return {}
    
    def get_available_backgrounds(self) -> Dict[BackgroundType, Dict[str, Any]]:
        """Get information about available background types."""
        return {
            BackgroundType.GEOMETRIC_PATTERNS: {
                "name": "Geometric Patterns",
                "description": "Animated geometric shapes and patterns",
                "style": "modern",
                "best_for": ["tech", "educational", "general"]
            },
            BackgroundType.MINECRAFT_PARKOUR: {
                "name": "Minecraft Parkour",
                "description": "Minecraft parkour gameplay footage",
                "style": "gaming",
                "best_for": ["gaming", "tifu", "general"]
            },
            BackgroundType.SUBWAY_SURFERS: {
                "name": "Subway Surfers",
                "description": "Endless runner game footage",
                "style": "gaming",
                "best_for": ["aita", "relationship", "family"]
            },
            BackgroundType.SATISFYING_SLIME: {
                "name": "Satisfying Slime",
                "description": "Satisfying slime and ASMR content",
                "style": "relaxing",
                "best_for": ["aita", "emotional", "personal"]
            },
            BackgroundType.COOKING_ASMR: {
                "name": "Cooking ASMR",
                "description": "Cooking and food preparation footage",
                "style": "lifestyle",
                "best_for": ["family", "lifestyle", "tips"]
            },
            BackgroundType.NATURE_SCENES: {
                "name": "Nature Scenes",
                "description": "Calming nature and landscape footage",
                "style": "peaceful",
                "best_for": ["meditation", "reflection", "philosophical"]
            }
        }
    
    def suggest_background(self, story_type: str, emotional_score: float, 
                          dominant_emotion: str = "neutral") -> BackgroundType:
        """Suggest optimal background type based on content analysis (Legacy method)."""
        # Use the background library's intelligent suggestion
        background_style = self.background_library.suggest_background(
            story_type=story_type,
            emotional_score=emotional_score,
            dominant_emotion=dominant_emotion
        )
        
        # Convert BackgroundStyle back to legacy BackgroundType
        style_to_type_map = {
            BackgroundStyle.MINECRAFT_PARKOUR: BackgroundType.MINECRAFT_PARKOUR,
            BackgroundStyle.SUBWAY_SURFERS: BackgroundType.SUBWAY_SURFERS,
            BackgroundStyle.SLIME_MIXING: BackgroundType.SATISFYING_SLIME,
            BackgroundStyle.COOKING_ASMR: BackgroundType.COOKING_ASMR,
            BackgroundStyle.OCEAN_WAVES: BackgroundType.NATURE_SCENES,
            BackgroundStyle.GEOMETRIC_PATTERNS: BackgroundType.GEOMETRIC_PATTERNS
        }
        
        return style_to_type_map.get(background_style, BackgroundType.GEOMETRIC_PATTERNS)
    
    def get_available_backgrounds(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available background styles."""
        backgrounds = {}
        
        # Get background specs from library
        for style, spec in self.background_library.get_available_styles().items():
            backgrounds[style.value] = {
                "name": spec.name,
                "description": spec.description,
                "category": spec.category.value,
                "best_for": spec.best_for,
                "emotional_match": spec.emotional_match,
                "complexity": spec.generation_complexity,
                "estimated_time": spec.estimated_generation_time
            }
        
        return backgrounds
    
    def get_backgrounds_by_category(self, category: str) -> List[str]:
        """Get all background styles in a specific category."""
        from generators.background_library import BackgroundCategory
        
        try:
            cat_enum = BackgroundCategory(category)
            styles = self.background_library.get_styles_by_category(cat_enum)
            return [style.value for style in styles]
        except ValueError:
            logger.warning(f"Unknown background category: {category}")
            return []
    
    def suggest_background_enhanced(self, story_type: str, emotional_score: float,
                                  dominant_emotion: str = "neutral") -> str:
        """Enhanced background suggestion returning BackgroundStyle value."""
        background_style = self.background_library.suggest_background(
            story_type=story_type,
            emotional_score=emotional_score,
            dominant_emotion=dominant_emotion
        )
        return background_style.value
    
    def cleanup_temp_files(self, keep_final: bool = True):
        """Clean up temporary files created during video generation."""
        try:
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    if keep_final and "final_video" in file_path.name:
                        continue  # Keep final videos
                    try:
                        file_path.unlink()
                        logger.debug(f"Cleaned up temp file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")