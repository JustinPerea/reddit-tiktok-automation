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

logger = get_logger("VideoGenerator")
settings = get_settings()


class VideoFormat(Enum):
    """Supported video output formats."""
    TIKTOK = "tiktok"  # 9:16 aspect ratio, 1080x1920
    INSTAGRAM_REEL = "instagram_reel"  # 9:16 aspect ratio, 1080x1920
    YOUTUBE_SHORT = "youtube_short"  # 9:16 aspect ratio, 1080x1920
    SQUARE = "square"  # 1:1 aspect ratio, 1080x1080


class BackgroundType(Enum):
    """Types of background content."""
    MINECRAFT_PARKOUR = "minecraft_parkour"
    SUBWAY_SURFERS = "subway_surfers"
    SATISFYING_SLIME = "satisfying_slime"
    COOKING_ASMR = "cooking_asmr"
    NATURE_SCENES = "nature_scenes"
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
        
        # Video specifications for different formats
        self.format_specs = {
            VideoFormat.TIKTOK: {"width": 1080, "height": 1920, "fps": 30},
            VideoFormat.INSTAGRAM_REEL: {"width": 1080, "height": 1920, "fps": 30},
            VideoFormat.YOUTUBE_SHORT: {"width": 1080, "height": 1920, "fps": 30},
            VideoFormat.SQUARE: {"width": 1080, "height": 1080, "fps": 30}
        }
        
        # Check FFmpeg availability
        self._check_ffmpeg()
        
        logger.info("Video generator initialized")
    
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
            
            # Generate text overlay
            overlay_path = self._create_text_overlay(text, audio_duration, config)
            if not overlay_path:
                return VideoResult(
                    success=False,
                    error_message="Failed to create text overlay"
                )
            
            # Combine all elements
            final_video = self._assemble_final_video(
                background_path, 
                overlay_path, 
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
        """Create or select background video."""
        try:
            specs = self.format_specs[config.format]
            output_path = self.temp_dir / f"background_{random.randint(1000, 9999)}.mp4"
            
            # For now, create a simple colored background with subtle animation
            # In production, you'd select from a library of background videos
            
            if config.background_type == BackgroundType.GEOMETRIC_PATTERNS:
                # Create animated geometric pattern
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", f"color=c=0x1a1a2e:size={specs['width']}x{specs['height']}:duration={duration}",
                    "-f", "lavfi", 
                    "-i", f"testsrc2=size={specs['width']}x{specs['height']}:duration={duration}",
                    "-filter_complex", 
                    f"[1]scale={specs['width']}:{specs['height']},format=rgba,colorchannelmixer=aa=0.1[overlay];[0][overlay]overlay",
                    "-r", str(specs['fps']),
                    "-c:v", "libx264",
                    "-preset", "fast",
                    str(output_path)
                ]
            else:
                # Simple gradient background
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
                logger.info(f"Background video created: {output_path}")
                return output_path
            else:
                logger.error(f"Failed to create background video: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating background video: {e}")
            return None
    
    def _create_text_overlay(self, text: str, duration: float, config: VideoConfig) -> Optional[Path]:
        """Create text overlay video with word-by-word highlighting."""
        try:
            specs = self.format_specs[config.format]
            output_path = self.temp_dir / f"text_overlay_{random.randint(1000, 9999)}.mp4"
            
            # Split text into words for timing
            words = text.split()
            words_per_second = len(words) / duration
            
            # Escape text for FFmpeg
            escaped_text = text.replace("'", "\\'").replace(":", "\\:")
            
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
                "-pix_fmt", "yuva420p",
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
        overlay_path: Path,
        audio_path: Path,
        config: VideoConfig,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """Assemble final video from all components."""
        try:
            if output_path is None:
                output_path = self.temp_dir / f"final_video_{random.randint(1000, 9999)}.mp4"
            
            specs = self.format_specs[config.format]
            
            # Combine background, text overlay, and audio
            cmd = [
                "ffmpeg", "-y",
                "-i", str(background_path),  # Background video
                "-i", str(overlay_path),     # Text overlay
                "-i", str(audio_path),       # Audio
                "-filter_complex", 
                f"[0:v][1:v]overlay=0:0[v]",
                "-map", "[v]",
                "-map", "2:a",
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
    
    def suggest_background(self, story_type: str, emotional_score: float) -> BackgroundType:
        """Suggest optimal background type based on content analysis."""
        # High emotional content gets more engaging backgrounds
        if emotional_score > 0.7:
            if story_type in ["aita", "relationship"]:
                return BackgroundType.SUBWAY_SURFERS
            elif story_type == "tifu":
                return BackgroundType.MINECRAFT_PARKOUR
            else:
                return BackgroundType.SATISFYING_SLIME
        
        # Medium emotional content
        elif emotional_score > 0.4:
            if story_type in ["family", "workplace"]:
                return BackgroundType.COOKING_ASMR
            else:
                return BackgroundType.GEOMETRIC_PATTERNS
        
        # Low emotional content gets calming backgrounds
        else:
            return BackgroundType.NATURE_SCENES
    
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