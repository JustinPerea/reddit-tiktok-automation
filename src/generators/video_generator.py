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
import re
from datetime import timedelta
import numpy as np

try:
    import librosa
    import soundfile as sf
    AUDIO_ANALYSIS_AVAILABLE = True
except ImportError:
    AUDIO_ANALYSIS_AVAILABLE = False

from utils.logger import get_logger
from config.settings import get_settings
from generators.background_library import BackgroundLibrary, BackgroundStyle
# Temporarily disabled due to NumPy 2.x compatibility issues
# from generators.whisperx_aligner import create_aligner, WordTiming
# from generators.whisper_analyzer import create_whisper_analyzer  
# from generators.fast_whisper_analyzer import create_fast_whisper_analyzer
from generators.whispers2t_analyzer import create_whispers2t_analyzer, WhisperS2TTiming
from generators.edge_tts_timing_provider import create_edge_tts_timing_provider
from processors.text_normalizer import create_normalizer, NormalizedText

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
    synchronized_text: bool = True  # Enable text synchronization with simple chunk approach


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
        
        # Initialize WhisperS2T analyzer (lazy loading)
        self.whispers2t_analyzer = None
        
        # Initialize Edge TTS timing provider (lazy loading)
        self.edge_tts_timing = None
        
        # Initialize text normalizer for TTS-subtitle synchronization
        self.text_normalizer = create_normalizer()
        
        # Video specifications for different formats
        self.format_specs = {
            VideoFormat.TIKTOK: {"width": 1080, "height": 1920, "fps": 30},
            VideoFormat.INSTAGRAM_REEL: {"width": 1080, "height": 1920, "fps": 30},
            VideoFormat.YOUTUBE_SHORT: {"width": 1080, "height": 1920, "fps": 30},
            VideoFormat.SQUARE: {"width": 1080, "height": 1080, "fps": 30}
        }
        
        # Check FFmpeg availability
        self._check_ffmpeg()
    
    def _get_whispers2t_analyzer(self):
        """Get or create WhisperS2T analyzer instance (lazy loading)."""
        if self.whispers2t_analyzer is None:
            self.whispers2t_analyzer = create_whispers2t_analyzer(model_size="base")
        return self.whispers2t_analyzer
    
    def _get_edge_tts_timing_provider(self):
        """Get or create Edge TTS timing provider instance (lazy loading)."""
        if self.edge_tts_timing is None:
            self.edge_tts_timing = create_edge_tts_timing_provider()
        return self.edge_tts_timing
    
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
        output_path: Optional[Path] = None,
        subtitle_path: Optional[Path] = None
    ) -> Optional[Path]:
        """Assemble final video by applying synchronized text directly to background."""
        try:
            if output_path is None:
                output_path = self.temp_dir / f"final_video_{random.randint(1000, 9999)}.mp4"
            
            specs = self.format_specs[config.format]
            
            # Create subtitles or static text based on configuration
            if config.synchronized_text:
                # Get audio duration for subtitle timing
                audio_duration = self._get_audio_duration(audio_path)
                if audio_duration <= 0:
                    logger.warning("Could not determine audio duration, using static text")
                    # Fall back to static text
                    text_filter = self._create_static_text_filter(text, config, specs)
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
                else:
                    # Use provided subtitle file or create new one with audio analysis
                    if subtitle_path is None:
                        subtitle_path = self._create_subtitle_file(text, audio_path, output_path)
                    
                    if subtitle_path and subtitle_path.exists():
                        logger.info(f"Using subtitle file for synchronized text: {subtitle_path}")
                        
                        # Use subtitles filter to burn in subtitles
                        subtitle_filter = (
                            f"subtitles='{str(subtitle_path)}':"
                            f"force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF&,"
                            f"OutlineColour=&H000000&,BorderStyle=3,Outline=2,Shadow=0,"
                            f"Alignment=2,MarginV=50'"
                        )
                        
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", str(background_path),  # Background video
                            "-i", str(audio_path),       # Audio
                            "-vf", subtitle_filter,      # Apply subtitles
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
                    else:
                        logger.warning("Failed to create subtitle file, using static text")
                        # Fall back to static text
                        text_filter = self._create_static_text_filter(text, config, specs)
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", str(background_path),
                            "-i", str(audio_path),
                            "-vf", text_filter,
                            "-map", "0:v",
                            "-map", "1:a",
                            "-c:v", "libx264",
                            "-c:a", "aac",
                            "-preset", "medium",
                            "-crf", "23",
                            "-r", str(specs['fps']),
                            "-s", f"{specs['width']}x{specs['height']}",
                            "-movflags", "+faststart",
                            str(output_path)
                        ]
            else:
                # Use static text overlay
                text_filter = self._create_static_text_filter(text, config, specs)
                logger.info("Using static text overlay")
                
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
                
                # Keep subtitle file for debugging - comment out cleanup
                # if config.synchronized_text:
                #     subtitle_path = output_path.with_suffix('.srt')
                #     if subtitle_path.exists():
                #         try:
                #             subtitle_path.unlink()
                #             logger.debug(f"Cleaned up subtitle file: {subtitle_path}")
                #         except Exception as e:
                #             logger.warning(f"Failed to clean up subtitle file: {e}")
                
                return output_path
            else:
                logger.error(f"Failed to assemble final video: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error assembling final video: {e}")
            return None
    def _analyze_audio_for_word_timings(self, audio_path: Path, text: str) -> List[Tuple[str, float, float]]:
        """Analyze actual audio using TTS-aware timing with WhisperS2T segment anchors."""
        
        # Try WhisperS2T for segment-level timing anchors
        try:
            analyzer = self._get_whispers2t_analyzer()
            if analyzer.is_available():
                logger.info("Using WhisperS2T segment timing with TTS text alignment")
                
                # Get segment-level timing from WhisperS2T
                segment_timings = self._get_whispers2t_segments(analyzer, audio_path)
                
                if segment_timings:
                    # Apply TTS text to segment timing
                    word_timings = self._apply_tts_text_to_segments(text, segment_timings)
                    logger.info(f"WhisperS2T segments: {len(segment_timings)}, TTS words: {len(word_timings)}")
                    return word_timings
                else:
                    logger.warning("WhisperS2T analysis returned no segments, falling back to estimation")
            else:
                logger.warning("WhisperS2T not available, falling back to estimation")
        except Exception as e:
            logger.warning(f"WhisperS2T analysis failed: {e}, falling back to estimation")
        
        # Fallback to enhanced estimation with phonetic modeling
        logger.info("Using enhanced phonetic-based timing estimation for word-level synchronization")
        return self._calculate_word_timings_estimated(text, self._get_audio_duration(audio_path))
    
    def _get_whispers2t_segments(self, analyzer, audio_path: Path) -> List[Tuple[float, float, str]]:
        """Get segment-level timing from WhisperS2T (start, end, text)."""
        try:
            from whisper_s2t import load_model
            
            # Load model and transcribe to get segments
            model = load_model('base', backend='CTranslate2', device='cpu', compute_type='int8')
            result = model.transcribe_with_vad(
                [str(audio_path)],
                lang_codes=["en"],
                tasks=["transcribe"],
                initial_prompts=[None],
                batch_size=1,
            )
            
            segments = []
            if result and len(result) > 0:
                file_result = result[0]
                for segment in file_result:
                    start_time = segment.get('start_time', 0.0)
                    end_time = segment.get('end_time', start_time + 1.0)
                    text = segment.get('text', '').strip()
                    
                    if text and end_time > start_time:
                        segments.append((start_time, end_time, text))
            
            logger.info(f"WhisperS2T extracted {len(segments)} speech segments")
            return segments
            
        except Exception as e:
            logger.error(f"Failed to get WhisperS2T segments: {e}")
            return []
    
    def _apply_tts_text_to_segments(self, tts_text: str, segments: List[Tuple[float, float, str]]) -> List[Tuple[str, float, float]]:
        """Apply TTS text words to WhisperS2T segment timing anchors."""
        if not segments:
            return []
            
        tts_words = tts_text.split()
        if not tts_words:
            return []
        
        # Calculate total duration from segments
        total_duration = segments[-1][1] if segments else 60.0
        
        # Create word timing by distributing TTS words across segment boundaries
        word_timings = []
        
        # Calculate word distribution based on segment text similarity
        current_word_index = 0
        
        for i, (seg_start, seg_end, seg_text) in enumerate(segments):
            # Estimate words for this segment based on segment text length
            seg_words = seg_text.split()
            segment_word_count = len(seg_words)
            
            # Adjust for remaining words
            remaining_words = len(tts_words) - current_word_index
            remaining_segments = len(segments) - i
            
            if remaining_segments == 1:
                # Last segment gets all remaining words
                segment_word_count = remaining_words
            else:
                # Don't exceed remaining words
                segment_word_count = min(segment_word_count, remaining_words)
                segment_word_count = max(1, segment_word_count)  # At least one word
            
            # Get words for this segment
            segment_words = tts_words[current_word_index:current_word_index + segment_word_count]
            
            if segment_words:
                # Distribute words within segment evenly
                segment_duration = seg_end - seg_start
                word_duration = segment_duration / len(segment_words)
                
                for j, word in enumerate(segment_words):
                    word_start = seg_start + (j * word_duration)
                    word_end = word_start + word_duration
                    
                    # Ensure we don't exceed segment boundary
                    word_end = min(word_end, seg_end)
                    
                    word_timings.append((word, word_start, word_end))
                
                current_word_index += len(segment_words)
            
            # Break if we've processed all words
            if current_word_index >= len(tts_words):
                break
        
        logger.info(f"Applied {len(tts_words)} TTS words to {len(segments)} WhisperS2T segments -> {len(word_timings)} word timings")
        return word_timings
    
    def _get_edge_tts_timing_for_audio(self, audio_path: Path, text: str) -> Optional[List[Tuple[str, float, float]]]:
        """Check if we have Edge TTS timing data for this audio file."""
        try:
            # Check if this is an Edge TTS file by looking for timing cache
            timing_cache_path = audio_path.with_suffix('.timing.json')
            
            if timing_cache_path.exists():
                logger.info(f"Found Edge TTS timing cache: {timing_cache_path}")
                import json
                
                with open(timing_cache_path, 'r') as f:
                    timing_data = json.load(f)
                
                # Verify the text matches (basic check)
                cached_words = [w['word'] for w in timing_data.get('words', [])]
                text_words = text.split()
                
                if len(cached_words) == len(text_words) and cached_words[:5] == text_words[:5]:
                    # Convert to expected format
                    word_timings = [
                        (w['word'], w['start'], w['end'])
                        for w in timing_data['words']
                    ]
                    logger.info(f"Using cached Edge TTS timing for {len(word_timings)} words")
                    return word_timings
                else:
                    logger.warning("Cached timing data doesn't match current text")
            
            return None
            
        except Exception as e:
            logger.debug(f"No Edge TTS timing cache found: {e}")
            return None
    
    def generate_video_with_perfect_timing(
        self, 
        audio_path: Path, 
        text: str, 
        word_timings: List[Tuple[str, float, float]], 
        config: VideoConfig
    ) -> VideoResult:
        """Generate video using pre-calculated perfect word timings from Edge TTS."""
        try:
            logger.info(f"Generating video with perfect timing: {len(word_timings)} words")
            
            # Get audio duration
            audio_duration = self._get_audio_duration(audio_path)
            
            # Create background video
            background_video = self._create_background_video(audio_duration, config)
            if not background_video:
                return VideoResult(
                    success=False,
                    error_message="Failed to create background video"
                )
            
            # Create perfect subtitle file using provided timings
            output_path = self.temp_dir / f"perfect_video_{random.randint(1000, 9999)}.mp4"
            subtitle_path = self._create_perfect_subtitle_file(word_timings, output_path)
            
            if not subtitle_path:
                return VideoResult(
                    success=False,
                    error_message="Failed to create perfect subtitle file"
                )
            
            # Assemble final video using perfect subtitle file
            final_video = self._assemble_final_video(
                background_path=background_video,
                text=text,
                audio_path=audio_path,
                config=config,
                output_path=output_path,
                subtitle_path=subtitle_path
            )
            
            if final_video:
                file_size = final_video.stat().st_size
                
                return VideoResult(
                    success=True,
                    video_path=final_video,
                    duration=audio_duration,
                    format=config.format,
                    file_size=file_size,
                    metadata={
                        "timing_method": "edge_tts_perfect",
                        "word_count": len(word_timings),
                        "text_length": len(text),
                        "background_type": config.background_type.value,
                        "synchronized": True
                    }
                )
            else:
                return VideoResult(
                    success=False,
                    error_message="Failed to assemble final video with perfect timing"
                )
                
        except Exception as e:
            logger.error(f"Perfect timing video generation failed: {e}")
            return VideoResult(
                success=False,
                error_message=f"Perfect timing generation failed: {e}"
            )
    
    def _create_perfect_subtitle_file(self, word_timings: List[Tuple[str, float, float]], output_path: Path) -> Optional[Path]:
        """Create subtitle file using perfect word timings from Edge TTS."""
        try:
            srt_content = []
            
            for i, (word, start_time, end_time) in enumerate(word_timings):
                # Format times as HH:MM:SS,mmm
                start_time_str = self._format_srt_time(start_time)
                end_time_str = self._format_srt_time(end_time)
                
                # Use uppercase for viral TikTok effect
                display_word = word.upper()
                
                # Add subtitle entry for this word
                srt_content.append(f"{i + 1}")
                srt_content.append(f"{start_time_str} --> {end_time_str}")
                srt_content.append(display_word)
                srt_content.append("")  # Empty line between subtitles
            
            # Write SRT file
            srt_path = output_path.with_suffix('.srt')
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_content))
            
            logger.info(f"Created perfect subtitle file with {len(word_timings)} words: {srt_path}")
            logger.info("Perfect timing: subtitles exactly match Edge TTS word boundaries")
            return srt_path
            
        except Exception as e:
            logger.error(f"Error creating perfect subtitle file: {e}")
            return None
    
    def _calculate_word_timings_estimated(self, text: str, audio_duration: float) -> List[Tuple[str, float, float]]:
        """Calculate realistic timing for each word based on audio duration and natural speech patterns (enhanced fallback)."""
        
        # Extract words preserving original case and form
        words = []
        original_positions = []  # Track position in original text for punctuation context
        
        word_pattern = r'\b\w+(?:\'\w+)?\b'  # Matches words including contractions
        for match in re.finditer(word_pattern, text):
            words.append(match.group())
            original_positions.append(match.start())
        
        if not words:
            return []
        
        # Calculate word durations based on phonetic complexity
        word_durations = []
        total_duration_units = 0
        
        for i, word in enumerate(words):
            # Base duration by syllable count (more accurate than character count)
            syllables = self._estimate_syllables(word)
            
            # Phonetic complexity factors
            consonant_clusters = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]{2,}', word.lower()))
            vowel_complexity = len(re.findall(r'[aeiou]{2,}|ough|tion|sion', word.lower()))
            
            # Base duration: 150ms per syllable, adjusted for complexity
            base_duration = syllables * 0.15
            complexity_factor = 1.0 + (consonant_clusters * 0.1) + (vowel_complexity * 0.1)
            
            # Word frequency adjustment (common words spoken faster)
            if word.lower() in {'i', 'a', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}:
                frequency_factor = 0.7
            elif word.lower() in {'am', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would', 'could', 'should'}:
                frequency_factor = 0.8
            else:
                frequency_factor = 1.0
            
            duration_units = base_duration * complexity_factor * frequency_factor
            word_durations.append(duration_units)
            total_duration_units += duration_units
        
        # Calculate pause durations based on punctuation context
        pause_times = []
        for i, pos in enumerate(original_positions):
            # Look ahead to next punctuation
            next_punct_pos = len(text)
            if i < len(original_positions) - 1:
                next_punct_pos = original_positions[i + 1]
            
            # Check for punctuation between current word and next
            between_text = text[pos + len(words[i]):next_punct_pos]
            
            if '.' in between_text or '!' in between_text or '?' in between_text:
                pause_time = 0.4  # Sentence end pause
            elif ',' in between_text or ';' in between_text or ':' in between_text:
                pause_time = 0.2  # Clause pause
            elif '"' in between_text or "'" in between_text:
                pause_time = 0.1  # Quote pause
            else:
                pause_time = 0.05  # Natural word spacing
            
            pause_times.append(pause_time)
        
        # Scale timing to fit actual audio duration
        total_estimated_time = sum(word_durations) + sum(pause_times)
        scale_factor = audio_duration / total_estimated_time if total_estimated_time > 0 else 1.0
        
        # Generate synchronized word timings
        word_timings = []
        current_time = 0.0
        
        for i, (word, duration_units, pause_time) in enumerate(zip(words, word_durations, pause_times)):
            # Scale word duration to fit actual audio
            scaled_duration = duration_units * scale_factor
            
            start_time = current_time
            end_time = start_time + scaled_duration
            
            word_timings.append((word, start_time, end_time))
            
            # Add pause after word
            current_time = end_time + (pause_time * scale_factor)
        
        logger.info(f"Enhanced estimated timing for {len(word_timings)} words over {audio_duration:.1f}s (scale: {scale_factor:.2f})")
        return word_timings
    
    def _estimate_syllables(self, word: str) -> int:
        """Estimate syllable count for more accurate speech timing."""
        word = word.lower()
        
        # Remove common endings that don't add syllables
        word = re.sub(r'(ed|es|ing|ly|tion|sion)$', '', word)
        
        # Count vowel groups as syllables
        syllables = len(re.findall(r'[aeiouy]+', word))
        
        # Adjust for silent e
        if word.endswith('e') and syllables > 1:
            syllables -= 1
        
        # Minimum one syllable per word
        return max(1, syllables)
    
    def _align_tts_text_with_whisper_timing(self, tts_words: List[str], whisper_timings: List[Tuple[str, float, float]]) -> List[Tuple[str, float, float]]:
        """Align TTS text words with WhisperS2T timing information for perfect synchronization."""
        
        if len(tts_words) == len(whisper_timings):
            # Perfect match - use TTS words with WhisperS2T timing
            return [(tts_words[i], timing[1], timing[2]) for i, timing in enumerate(whisper_timings)]
        
        # Different word counts - need intelligent alignment
        logger.info(f"Aligning {len(tts_words)} TTS words with {len(whisper_timings)} WhisperS2T timings")
        
        # Use dynamic time warping approach
        if len(whisper_timings) == 0:
            # No timing data - fall back to estimation
            total_duration = 60.0  # Default duration
            word_duration = total_duration / len(tts_words)
            return [(word, i * word_duration, (i + 1) * word_duration) for i, word in enumerate(tts_words)]
        
        # Scale WhisperS2T timing to fit TTS word count
        total_duration = whisper_timings[-1][2] if whisper_timings else 60.0
        
        # Create timing for each TTS word by interpolating WhisperS2T timing
        aligned_timings = []
        for i, word in enumerate(tts_words):
            # Map TTS word index to WhisperS2T timing index
            whisper_index = int((i / len(tts_words)) * len(whisper_timings))
            whisper_index = min(whisper_index, len(whisper_timings) - 1)
            
            # Calculate proportional timing
            if i == 0:
                start_time = 0.0
            else:
                start_time = (i / len(tts_words)) * total_duration
            
            if i == len(tts_words) - 1:
                end_time = total_duration
            else:
                end_time = ((i + 1) / len(tts_words)) * total_duration
            
            aligned_timings.append((word, start_time, end_time))
        
        logger.info(f"Aligned {len(aligned_timings)} TTS words with proportional timing")
        return aligned_timings
    
    def _create_subtitle_file(self, text: str, audio_path: Path, output_path: Path) -> Optional[Path]:
        """Create an SRT subtitle file with word-by-word synchronized text using bidirectional normalization."""
        try:
            # Apply bidirectional text normalization
            normalized = self.text_normalizer.process_for_sync(text)
            
            logger.info(f"Text normalization applied: {len(normalized.transformation_log)} transformation types")
            for transform in normalized.transformation_log:
                logger.debug(f"  {transform['type']}: {transform['count']} changes, examples: {transform.get('examples', [])}")
            
            # Use TTS-optimized text for audio analysis (what was actually spoken)
            tts_text = normalized.tts_text
            word_timings = self._analyze_audio_for_word_timings(audio_path, tts_text)
            
            if not word_timings:
                logger.warning("No word timings available, falling back to original text analysis")
                word_timings = self._analyze_audio_for_word_timings(audio_path, text)
                if not word_timings:
                    return None
            
            # For subtitles, use TTS text (matches what's spoken) with WhisperS2T timing
            subtitle_words = tts_text.split()
            
            # Word timings are already aligned with TTS text, no need for hybrid alignment
            aligned_timings = word_timings
            
            logger.info(f"Using {len(aligned_timings)} word timings (already TTS-aligned)")
            
            # Create SRT content with one entry per word  
            srt_content = []
            for i, (word, start_time, end_time) in enumerate(aligned_timings):
                # Word is already from TTS text, ensuring perfect sync
                display_word = word.upper()  # Use uppercase for viral TikTok effect
                
                # Format times as HH:MM:SS,mmm
                start_time_str = self._format_srt_time(start_time)
                end_time_str = self._format_srt_time(end_time)
                
                # Add subtitle entry for this word
                srt_content.append(f"{i + 1}")
                srt_content.append(f"{start_time_str} --> {end_time_str}")
                srt_content.append(display_word)
                srt_content.append("")  # Empty line between subtitles
            
            # Write SRT file
            srt_path = output_path.with_suffix('.srt')
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_content))
            
            logger.info(f"Created synchronized subtitle file with {len(aligned_timings)} words: {srt_path}")
            logger.info(f"Subtitle text matches TTS audio (bidirectional normalization applied)")
            return srt_path
            
        except Exception as e:
            logger.error(f"Error creating subtitle file: {e}")
            return None
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        millis = int((td.total_seconds() % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds."""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", str(audio_path)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                duration = float(metadata.get("format", {}).get("duration", 0))
                logger.debug(f"Audio duration: {duration:.2f}s")
                return duration
            else:
                logger.error(f"Failed to get audio duration: {result.stderr}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0
    
    def _create_synchronized_text_filter(self, text: str, audio_duration: float, config: VideoConfig, specs: Dict[str, Any]) -> str:
        """Create FFmpeg filter for text synchronization - not used when using subtitle files."""
        
        # This method is kept for backward compatibility but not used when subtitle files are enabled
        logger.info("Synchronized text filter called but subtitle files will be used instead")
        return self._create_static_text_filter(text, config, specs)
    
    def _create_chunk_based_text_filter(self, text: str, audio_duration: float, config: VideoConfig, specs: Dict[str, Any], chunk_size: int = 50) -> str:
        """Create text filter using simple 10-second chunks for reliable synchronization."""
        
        # Split text into word chunks (much simpler approach)
        words = text.split()
        chunk_duration = 10.0  # 10 seconds per chunk
        num_chunks = max(1, int(audio_duration / chunk_duration))
        words_per_chunk = len(words) // num_chunks if num_chunks > 0 else len(words)
        
        # Calculate text positioning
        if config.text_position == "top":
            y_pos = specs['height'] * 0.2
        elif config.text_position == "bottom":
            y_pos = specs['height'] * 0.8
        else:  # center
            y_pos = specs['height'] * 0.5
        
        # Create simple chunk filters (max 6 chunks to avoid FFmpeg complexity)
        text_filters = []
        max_chunks = min(6, num_chunks)  # Limit to 6 chunks maximum
        actual_chunk_duration = audio_duration / max_chunks
        
        for i in range(max_chunks):
            start_word = i * words_per_chunk
            end_word = min((i + 1) * words_per_chunk, len(words))
            chunk_text = " ".join(words[start_word:end_word])
            
            if not chunk_text.strip():
                continue
                
            start_time = i * actual_chunk_duration
            end_time = (i + 1) * actual_chunk_duration
            
            # Simple text escaping
            escaped_text = chunk_text.replace("'", "\\'").replace(":", "\\:")
            
            # Create filter for this chunk
            chunk_filter = (
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
                f"boxborderw=10:"
                f"enable='between(t,{start_time:.1f},{end_time:.1f})'"
            )
            
            text_filters.append(chunk_filter)
        
        logger.info(f"Created {len(text_filters)} simple text chunks")
        return ",".join(text_filters)
    
    def _create_word_by_word_filter(self, word_timings: List[Tuple[str, float, float]], audio_duration: float, config: VideoConfig, specs: Dict[str, Any]) -> str:
        """Create word-by-word text filter for shorter texts."""
        
        # Calculate text positioning
        if config.text_position == "top":
            y_pos = specs['height'] * 0.2
        elif config.text_position == "bottom":
            y_pos = specs['height'] * 0.8
        else:  # center
            y_pos = specs['height'] * 0.5
        
        # Create progressive text reveal filters
        text_filters = []
        current_text = ""
        
        for i, (word, start_time, end_time) in enumerate(word_timings):
            current_text += (" " if current_text else "") + word
            
            # Escape text for FFmpeg
            escaped_text = (current_text
                .replace("\\", "\\\\")
                .replace("'", "\\'")
                .replace(":", "\\:")
                .replace("%", "\\%")
                .replace("[", "\\[")
                .replace("]", "\\]")
                .replace(",", "\\,")
                .replace(";", "\\;")
                .replace("$", "\\$")
            )
            
            # Create filter for this word reveal
            word_filter = (
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
                f"boxborderw=10:"
                f"enable='between(t,{start_time:.2f},{audio_duration:.2f})'"
            )
            
            text_filters.append(word_filter)
        
        logger.info(f"Created {len(text_filters)} word-by-word text filters")
        return ",".join(text_filters)
    
    def _create_static_text_filter(self, text: str, config: VideoConfig, specs: Dict[str, Any]) -> str:
        """Create static text filter as fallback."""
        
        # Escape text for FFmpeg
        escaped_text = (text
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace(":", "\\:")
            .replace("%", "\\%")
            .replace("[", "\\[")
            .replace("]", "\\]")
            .replace(",", "\\,")
            .replace(";", "\\;")
            .replace("$", "\\$")
        )
        
        # Calculate text positioning
        if config.text_position == "top":
            y_pos = specs['height'] * 0.2
        elif config.text_position == "bottom":
            y_pos = specs['height'] * 0.8
        else:  # center
            y_pos = specs['height'] * 0.5
        
        return (
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