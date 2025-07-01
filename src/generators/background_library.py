"""
Background video library manager for creating engaging TikTok-style backgrounds.
Supports procedural generation, caching, and intelligent selection based on content.
"""

import subprocess
import tempfile
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import math
import time

from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger("BackgroundLibrary")
settings = get_settings()


class BackgroundCategory(Enum):
    """Categories of background content for different story types."""
    GAMING = "gaming"
    SATISFYING = "satisfying"
    NATURE = "nature"
    ABSTRACT = "abstract"
    LIFESTYLE = "lifestyle"
    ASMR = "asmr"


class BackgroundStyle(Enum):
    """Specific background styles within categories."""
    # Gaming
    MINECRAFT_PARKOUR = "minecraft_parkour"
    SUBWAY_SURFERS = "subway_surfers"
    TEMPLE_RUN = "temple_run"
    FRUIT_NINJA = "fruit_ninja"
    
    # Satisfying
    SLIME_MIXING = "slime_mixing"
    KINETIC_SAND = "kinetic_sand"
    SOAP_CUTTING = "soap_cutting"
    ODDLY_SATISFYING = "oddly_satisfying"
    
    # Nature
    RAIN_WINDOW = "rain_window"
    OCEAN_WAVES = "ocean_waves"
    FOREST_WALK = "forest_walk"
    FIREPLACE = "fireplace"
    
    # Abstract
    GEOMETRIC_PATTERNS = "geometric_patterns"
    COLOR_GRADIENTS = "color_gradients"
    PARTICLE_EFFECTS = "particle_effects"
    FRACTAL_ZOOM = "fractal_zoom"
    
    # Lifestyle
    COOKING_ASMR = "cooking_asmr"
    COFFEE_BREWING = "coffee_brewing"
    PLANT_CARE = "plant_care"
    ORGANIZATION = "organization"
    
    # ASMR
    TRIGGER_SOUNDS = "trigger_sounds"
    GENTLE_MOVEMENTS = "gentle_movements"
    TEXTURE_FOCUS = "texture_focus"


@dataclass
class BackgroundSpec:
    """Specification for a background video style."""
    style: BackgroundStyle
    category: BackgroundCategory
    name: str
    description: str
    best_for: List[str]  # Story types this works best for
    emotional_match: List[str]  # Emotions this complements
    generation_complexity: str  # simple, medium, complex
    estimated_generation_time: int  # seconds
    quality_priority: str  # speed, balanced, quality


class BackgroundLibrary:
    """Manages background video generation and caching."""
    
    def __init__(self):
        """Initialize the background library."""
        self.cache_dir = Path(tempfile.gettempdir()) / "reddit_tiktok_backgrounds"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Background specifications
        self.background_specs = self._initialize_background_specs()
        
        # Cache management
        self.cache_index = self._load_cache_index()
        
        logger.info(f"Background library initialized with {len(self.background_specs)} styles")
    
    def _initialize_background_specs(self) -> Dict[BackgroundStyle, BackgroundSpec]:
        """Initialize all background style specifications."""
        return {
            # Gaming backgrounds
            BackgroundStyle.MINECRAFT_PARKOUR: BackgroundSpec(
                style=BackgroundStyle.MINECRAFT_PARKOUR,
                category=BackgroundCategory.GAMING,
                name="Minecraft Parkour",
                description="Fast-paced Minecraft parkour gameplay with jumps and obstacles",
                best_for=["tifu", "gaming", "general", "adventure"],
                emotional_match=["excitement", "energy", "neutral"],
                generation_complexity="complex",
                estimated_generation_time=45,
                quality_priority="balanced"
            ),
            
            BackgroundStyle.SUBWAY_SURFERS: BackgroundSpec(
                style=BackgroundStyle.SUBWAY_SURFERS,
                category=BackgroundCategory.GAMING,
                name="Subway Surfers Style",
                description="Endless runner style gameplay with colorful graphics",
                best_for=["aita", "relationship", "family", "drama"],
                emotional_match=["tension", "conflict", "neutral"],
                generation_complexity="complex",
                estimated_generation_time=50,
                quality_priority="quality"
            ),
            
            BackgroundStyle.TEMPLE_RUN: BackgroundSpec(
                style=BackgroundStyle.TEMPLE_RUN,
                category=BackgroundCategory.GAMING,
                name="Temple Run Adventure",
                description="Adventure running through ancient temples",
                best_for=["adventure", "travel", "escape"],
                emotional_match=["excitement", "fear", "urgency"],
                generation_complexity="complex",
                estimated_generation_time=40,
                quality_priority="balanced"
            ),
            
            # Satisfying backgrounds
            BackgroundStyle.SLIME_MIXING: BackgroundSpec(
                style=BackgroundStyle.SLIME_MIXING,
                category=BackgroundCategory.SATISFYING,
                name="Slime Mixing ASMR",
                description="Colorful slime being mixed and stretched",
                best_for=["aita", "emotional", "personal", "stress"],
                emotional_match=["calm", "satisfaction", "stress_relief"],
                generation_complexity="medium",
                estimated_generation_time=25,
                quality_priority="quality"
            ),
            
            BackgroundStyle.KINETIC_SAND: BackgroundSpec(
                style=BackgroundStyle.KINETIC_SAND,
                category=BackgroundCategory.SATISFYING,
                name="Kinetic Sand Play",
                description="Kinetic sand being shaped and manipulated",
                best_for=["meditation", "calm", "therapeutic"],
                emotional_match=["peace", "satisfaction", "focus"],
                generation_complexity="medium",
                estimated_generation_time=30,
                quality_priority="quality"
            ),
            
            BackgroundStyle.SOAP_CUTTING: BackgroundSpec(
                style=BackgroundStyle.SOAP_CUTTING,
                category=BackgroundCategory.SATISFYING,
                name="Soap Cutting ASMR",
                description="Satisfying soap cutting with clean cuts",
                best_for=["asmr", "satisfying", "clean"],
                emotional_match=["satisfaction", "precision", "calm"],
                generation_complexity="medium",
                estimated_generation_time=20,
                quality_priority="quality"
            ),
            
            # Nature backgrounds
            BackgroundStyle.RAIN_WINDOW: BackgroundSpec(
                style=BackgroundStyle.RAIN_WINDOW,
                category=BackgroundCategory.NATURE,
                name="Rain on Window",
                description="Peaceful rain droplets on glass with soft lighting",
                best_for=["sad", "emotional", "reflection", "contemplation"],
                emotional_match=["melancholy", "peace", "introspection"],
                generation_complexity="simple",
                estimated_generation_time=15,
                quality_priority="balanced"
            ),
            
            BackgroundStyle.OCEAN_WAVES: BackgroundSpec(
                style=BackgroundStyle.OCEAN_WAVES,
                category=BackgroundCategory.NATURE,
                name="Ocean Waves",
                description="Gentle ocean waves with natural sounds",
                best_for=["meditation", "peace", "nature", "escape"],
                emotional_match=["calm", "peace", "freedom"],
                generation_complexity="simple",
                estimated_generation_time=20,
                quality_priority="balanced"
            ),
            
            BackgroundStyle.FIREPLACE: BackgroundSpec(
                style=BackgroundStyle.FIREPLACE,
                category=BackgroundCategory.NATURE,
                name="Cozy Fireplace",
                description="Warm fireplace with crackling flames",
                best_for=["cozy", "winter", "comfort", "family"],
                emotional_match=["warmth", "comfort", "security"],
                generation_complexity="medium",
                estimated_generation_time=25,
                quality_priority="quality"
            ),
            
            # Abstract backgrounds
            BackgroundStyle.GEOMETRIC_PATTERNS: BackgroundSpec(
                style=BackgroundStyle.GEOMETRIC_PATTERNS,
                category=BackgroundCategory.ABSTRACT,
                name="Geometric Patterns",
                description="Clean animated geometric shapes and patterns",
                best_for=["tech", "educational", "professional", "general"],
                emotional_match=["neutral", "focus", "modern"],
                generation_complexity="simple",
                estimated_generation_time=10,
                quality_priority="speed"
            ),
            
            BackgroundStyle.COLOR_GRADIENTS: BackgroundSpec(
                style=BackgroundStyle.COLOR_GRADIENTS,
                category=BackgroundCategory.ABSTRACT,
                name="Color Gradients",
                description="Flowing color gradients with smooth transitions",
                best_for=["artistic", "creative", "mood"],
                emotional_match=["calm", "artistic", "flow"],
                generation_complexity="simple",
                estimated_generation_time=12,
                quality_priority="balanced"
            ),
            
            BackgroundStyle.PARTICLE_EFFECTS: BackgroundSpec(
                style=BackgroundStyle.PARTICLE_EFFECTS,
                category=BackgroundCategory.ABSTRACT,
                name="Particle Effects",
                description="Dynamic particle systems with motion",
                best_for=["tech", "science", "energy"],
                emotional_match=["energy", "movement", "dynamic"],
                generation_complexity="medium",
                estimated_generation_time=30,
                quality_priority="quality"
            ),
            
            # Lifestyle backgrounds
            BackgroundStyle.COOKING_ASMR: BackgroundSpec(
                style=BackgroundStyle.COOKING_ASMR,
                category=BackgroundCategory.LIFESTYLE,
                name="Cooking ASMR",
                description="Satisfying cooking processes and food preparation",
                best_for=["family", "lifestyle", "food", "comfort"],
                emotional_match=["comfort", "satisfaction", "nourishment"],
                generation_complexity="complex",
                estimated_generation_time=35,
                quality_priority="quality"
            ),
            
            BackgroundStyle.COFFEE_BREWING: BackgroundSpec(
                style=BackgroundStyle.COFFEE_BREWING,
                category=BackgroundCategory.LIFESTYLE,
                name="Coffee Brewing",
                description="Peaceful coffee brewing and steam",
                best_for=["morning", "work", "routine", "calm"],
                emotional_match=["comfort", "routine", "focus"],
                generation_complexity="medium",
                estimated_generation_time=20,
                quality_priority="balanced"
            ),
        }
    
    def _load_cache_index(self) -> Dict[str, Any]:
        """Load the background cache index."""
        index_file = self.cache_dir / "cache_index.json"
        try:
            if index_file.exists():
                with open(index_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache index: {e}")
        return {}
    
    def _save_cache_index(self):
        """Save the background cache index."""
        index_file = self.cache_dir / "cache_index.json"
        try:
            with open(index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def get_cache_key(self, style: BackgroundStyle, duration: float, specs: Dict[str, Any]) -> str:
        """Generate a cache key for a background video."""
        key_data = {
            "style": style.value,
            "duration": duration,
            "specs": specs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def suggest_background(self, story_type: str, emotional_score: float, 
                          dominant_emotion: str = "neutral") -> BackgroundStyle:
        """Suggest optimal background based on content analysis."""
        
        # Score each background based on content match
        best_match = None
        best_score = 0
        
        for style, spec in self.background_specs.items():
            score = 0
            
            # Story type match (40% weight)
            if story_type in spec.best_for:
                score += 40
            elif "general" in spec.best_for:
                score += 20
            
            # Emotional match (35% weight)
            if dominant_emotion in spec.emotional_match:
                score += 35
            elif "neutral" in spec.emotional_match:
                score += 15
            
            # Emotional intensity match (25% weight)
            if emotional_score > 0.7 and style.value in ["subway_surfers", "minecraft_parkour"]:
                score += 25
            elif emotional_score < 0.4 and style.value in ["rain_window", "ocean_waves"]:
                score += 25
            else:
                score += 10
            
            if score > best_score:
                best_score = score
                best_match = style
        
        logger.info(f"Selected background {best_match.value} for {story_type} story (score: {best_score})")
        return best_match or BackgroundStyle.GEOMETRIC_PATTERNS
    
    def generate_background(self, style: BackgroundStyle, duration: float, 
                          video_specs: Dict[str, Any]) -> Optional[Path]:
        """Generate a background video for the specified style and duration."""
        
        # Check cache first
        cache_key = self.get_cache_key(style, duration, video_specs)
        if cache_key in self.cache_index:
            cached_path = Path(self.cache_index[cache_key]["path"])
            if cached_path.exists():
                logger.info(f"Using cached background: {cached_path}")
                return cached_path
        
        # Generate new background
        spec = self.background_specs.get(style)
        if not spec:
            logger.error(f"Unknown background style: {style}")
            return None
        
        logger.info(f"Generating {spec.name} background ({duration}s)")
        start_time = time.time()
        
        # Generate based on style
        if style in [BackgroundStyle.GEOMETRIC_PATTERNS, BackgroundStyle.COLOR_GRADIENTS]:
            output_path = self._generate_abstract_background(style, duration, video_specs)
        elif style in [BackgroundStyle.SLIME_MIXING, BackgroundStyle.KINETIC_SAND]:
            output_path = self._generate_satisfying_background(style, duration, video_specs)
        elif style in [BackgroundStyle.RAIN_WINDOW, BackgroundStyle.OCEAN_WAVES]:
            output_path = self._generate_nature_background(style, duration, video_specs)
        elif style in [BackgroundStyle.PARTICLE_EFFECTS]:
            output_path = self._generate_particle_background(style, duration, video_specs)
        elif style == BackgroundStyle.FIREPLACE:
            output_path = self._generate_fireplace_background(duration, video_specs)
        else:
            # Complex gaming/lifestyle backgrounds use simplified versions for now
            output_path = self._generate_placeholder_background(style, duration, video_specs)
        
        generation_time = time.time() - start_time
        
        if output_path and output_path.exists():
            # Cache the result
            self.cache_index[cache_key] = {
                "path": str(output_path),
                "style": style.value,
                "duration": duration,
                "generation_time": generation_time,
                "created_at": time.time()
            }
            self._save_cache_index()
            
            logger.info(f"Generated {spec.name} in {generation_time:.1f}s: {output_path}")
            return output_path
        else:
            logger.error(f"Failed to generate background for {style.value}")
            return None
    
    def _generate_abstract_background(self, style: BackgroundStyle, duration: float, 
                                   video_specs: Dict[str, Any]) -> Optional[Path]:
        """Generate abstract geometric or gradient backgrounds."""
        output_path = self.cache_dir / f"{style.value}_{random.randint(1000, 9999)}.mp4"
        
        width = video_specs.get("width", 1080)
        height = video_specs.get("height", 1920)
        fps = video_specs.get("fps", 30)
        
        if style == BackgroundStyle.GEOMETRIC_PATTERNS:
            # Animated geometric patterns
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x1a1a2e:size={width}x{height}:duration={duration}",
                "-f", "lavfi",
                "-i", f"testsrc2=size={width}x{height}:duration={duration}:rate={fps}",
                "-filter_complex", 
                f"[1]scale={width}:{height},format=rgba,colorchannelmixer=aa=0.15[overlay];[0][overlay]overlay,fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5",
                "-r", str(fps),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "28",
                str(output_path)
            ]
        else:  # COLOR_GRADIENTS
            # Flowing color gradients
            colors = ["0x667eea", "0x764ba2", "0xf093fb", "0xf5576c", "0x4facfe", "0x00f2fe"]
            color1, color2 = random.sample(colors, 2)
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c={color1}:size={width}x{height}:duration={duration}",
                "-f", "lavfi",
                "-i", f"color=c={color2}:size={width}x{height}:duration={duration}",
                "-filter_complex",
                f"[0][1]blend=all_mode=overlay:all_opacity=0.5,fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1",
                "-r", str(fps),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "28",
                str(output_path)
            ]
        
        return self._run_ffmpeg_command(cmd, output_path)
    
    def _generate_satisfying_background(self, style: BackgroundStyle, duration: float,
                                      video_specs: Dict[str, Any]) -> Optional[Path]:
        """Generate satisfying content backgrounds."""
        output_path = self.cache_dir / f"{style.value}_{random.randint(1000, 9999)}.mp4"
        
        width = video_specs.get("width", 1080)
        height = video_specs.get("height", 1920)
        fps = video_specs.get("fps", 30)
        
        # Create satisfying color patterns
        if style == BackgroundStyle.SLIME_MIXING:
            # Slime-like flowing colors using color gradients
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0xff69b4:size={width}x{height}:duration={duration}",
                "-f", "lavfi", 
                "-i", f"color=c=0x87ceeb:size={width}x{height}:duration={duration}",
                "-filter_complex",
                f"[0][1]blend=all_mode=multiply:all_opacity=0.7,noise=alls=20:allf=t+u,fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "26",
                str(output_path)
            ]
        else:  # KINETIC_SAND
            # Sand-like texture patterns
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"life=s={width}x{height}:rate={fps}:mold=10:ratio=0.1:death_color=#C19A6B:life_color=#8B4513",
                "-t", str(duration),
                "-vf", f"scale={width}:{height},fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "26",
                str(output_path)
            ]
        
        return self._run_ffmpeg_command(cmd, output_path)
    
    def _generate_nature_background(self, style: BackgroundStyle, duration: float,
                                  video_specs: Dict[str, Any]) -> Optional[Path]:
        """Generate nature-themed backgrounds."""
        output_path = self.cache_dir / f"{style.value}_{random.randint(1000, 9999)}.mp4"
        
        width = video_specs.get("width", 1080)
        height = video_specs.get("height", 1920)
        fps = video_specs.get("fps", 30)
        
        if style == BackgroundStyle.RAIN_WINDOW:
            # Rain effect on window
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x2c3e50:size={width}x{height}:duration={duration}",
                "-f", "lavfi",
                "-i", f"nullsrc=s={width}x{height}:d={duration}:r={fps}",
                "-filter_complex",
                f"[1]geq=random(1)*255:128:128,scale={width}:{height}[rain];[0][rain]overlay:x=0:y=0:alpha=0.3,fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "28",
                str(output_path)
            ]
        else:  # OCEAN_WAVES
            # Ocean-like wave patterns
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x006994:size={width}x{height}:duration={duration}",
                "-f", "lavfi",
                "-i", f"sine=frequency=0.1:sample_rate=48000:duration={duration}",
                "-filter_complex",
                f"[0]fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1[v]",
                "-map", "[v]",
                "-map", "1:a",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "fast",
                "-crf", "28",
                str(output_path)
            ]
        
        return self._run_ffmpeg_command(cmd, output_path)
    
    def _generate_particle_background(self, style: BackgroundStyle, duration: float,
                                    video_specs: Dict[str, Any]) -> Optional[Path]:
        """Generate particle effect backgrounds."""
        output_path = self.cache_dir / f"{style.value}_{random.randint(1000, 9999)}.mp4"
        
        width = video_specs.get("width", 1080)
        height = video_specs.get("height", 1920)
        fps = video_specs.get("fps", 30)
        
        # Particle-like effects using Conway's Game of Life
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"life=s={width}x{height}:rate={fps}:ratio=0.2:death_color=#000814:life_color=#ffd60a",
            "-t", str(duration),
            "-vf", f"scale={width}:{height},fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "26",
            str(output_path)
        ]
        
        return self._run_ffmpeg_command(cmd, output_path)
    
    def _generate_fireplace_background(self, duration: float, video_specs: Dict[str, Any]) -> Optional[Path]:
        """Generate fireplace background."""
        output_path = self.cache_dir / f"fireplace_{random.randint(1000, 9999)}.mp4"
        
        width = video_specs.get("width", 1080)
        height = video_specs.get("height", 1920)
        fps = video_specs.get("fps", 30)
        
        # Fire-like effect using color blending
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x8B4513:size={width}x{height}:duration={duration}",
            "-f", "lavfi",
            "-i", f"color=c=0xFF4500:size={width}x{height}:duration={duration}",
            "-filter_complex",
            f"[0][1]blend=all_mode=overlay:all_opacity=0.6,noise=alls=15:allf=t,fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "26",
            str(output_path)
        ]
        
        return self._run_ffmpeg_command(cmd, output_path)
    
    def _generate_placeholder_background(self, style: BackgroundStyle, duration: float,
                                       video_specs: Dict[str, Any]) -> Optional[Path]:
        """Generate placeholder backgrounds for complex styles not yet implemented."""
        output_path = self.cache_dir / f"{style.value}_placeholder_{random.randint(1000, 9999)}.mp4"
        
        width = video_specs.get("width", 1080)
        height = video_specs.get("height", 1920)
        fps = video_specs.get("fps", 30)
        
        # Simple colored background with text overlay
        style_colors = {
            BackgroundStyle.SUBWAY_SURFERS: "0x00b4d8",
            BackgroundStyle.MINECRAFT_PARKOUR: "0x0077b6",
            BackgroundStyle.COOKING_ASMR: "0xffb700",
            BackgroundStyle.COFFEE_BREWING: "0x8b4513"
        }
        
        color = style_colors.get(style, "0x667eea")
        style_name = style.value.replace("_", " ").title()
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:size={width}x{height}:duration={duration}",
            "-vf", f"drawtext=text='{style_name}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:fontfile=/System/Library/Fonts/Helvetica.ttc,fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "28",
            str(output_path)
        ]
        
        return self._run_ffmpeg_command(cmd, output_path)
    
    def _run_ffmpeg_command(self, cmd: List[str], output_path: Path) -> Optional[Path]:
        """Run an FFmpeg command and return the output path if successful."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and output_path.exists():
                return output_path
            else:
                logger.error(f"FFmpeg command failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg command timed out")
            return None
        except Exception as e:
            logger.error(f"Error running FFmpeg command: {e}")
            return None
    
    def get_available_styles(self) -> Dict[BackgroundStyle, BackgroundSpec]:
        """Get all available background styles with their specifications."""
        return self.background_specs.copy()
    
    def get_styles_by_category(self, category: BackgroundCategory) -> List[BackgroundStyle]:
        """Get all styles in a specific category."""
        return [style for style, spec in self.background_specs.items() 
                if spec.category == category]
    
    def cleanup_cache(self, max_age_hours: int = 24, max_size_mb: int = 1000):
        """Clean up old or large cached background videos."""
        try:
            total_size = 0
            files_to_delete = []
            current_time = time.time()
            
            for file_path in self.cache_dir.glob("*.mp4"):
                file_age_hours = (current_time - file_path.stat().st_mtime) / 3600
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                total_size += file_size_mb
                
                if file_age_hours > max_age_hours:
                    files_to_delete.append(file_path)
            
            # If total size exceeds limit, delete oldest files
            if total_size > max_size_mb:
                all_files = list(self.cache_dir.glob("*.mp4"))
                all_files.sort(key=lambda x: x.stat().st_mtime)
                
                while total_size > max_size_mb and all_files:
                    oldest_file = all_files.pop(0)
                    if oldest_file not in files_to_delete:
                        files_to_delete.append(oldest_file)
                        total_size -= oldest_file.stat().st_size / (1024 * 1024)
            
            # Delete files and update cache index
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    # Remove from cache index
                    keys_to_remove = [k for k, v in self.cache_index.items() 
                                    if v.get("path") == str(file_path)]
                    for key in keys_to_remove:
                        del self.cache_index[key]
                except Exception as e:
                    logger.warning(f"Failed to delete cached file {file_path}: {e}")
            
            if files_to_delete:
                self._save_cache_index()
                logger.info(f"Cleaned up {len(files_to_delete)} cached background videos")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")