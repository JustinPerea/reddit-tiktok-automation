"""
YouTube Video Helper for Gaming Background Downloads

Helps extract direct download URLs from YouTube videos for gaming backgrounds.
Uses yt-dlp to get video information and generate download links.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

from utils.logger import get_logger

logger = get_logger("YouTubeHelper")


@dataclass
class YouTubeVideoInfo:
    """Information about a YouTube video."""
    url: str
    title: str
    duration: int
    resolution: str
    filesize: Optional[int]
    format_id: str
    direct_url: str


class YouTubeHelper:
    """Helper for extracting YouTube video information and URLs."""
    
    def __init__(self):
        """Initialize YouTube helper."""
        self.gaming_channels = {
            "minecraft": [
                "https://www.youtube.com/@MinecraftParkourParadise",
                "https://www.youtube.com/@ParkourCivilization",
            ],
            "subway_surfers": [
                "https://www.youtube.com/@SubwaySurfersOfficial",
                "https://www.youtube.com/@MobileGamingHub",
            ],
            "temple_run": [
                "https://www.youtube.com/@ImangistudiosOfficial",
                "https://www.youtube.com/@MobileGamingContent",
            ],
            "fruit_ninja": [
                "https://www.youtube.com/@halfbrick",
                "https://www.youtube.com/@FruitNinjaOfficial",
            ]
        }
        
        # Popular gaming video search terms
        self.search_terms = {
            "minecraft_parkour": [
                "minecraft parkour gameplay no commentary",
                "minecraft parkour compilation",
                "minecraft jumping blocks gameplay"
            ],
            "subway_surfers": [
                "subway surfers gameplay no commentary",
                "subway surfers high score run",
                "subway surfers endless runner"
            ],
            "temple_run": [
                "temple run 2 gameplay no commentary",
                "temple run endless running",
                "temple run high score"
            ],
            "fruit_ninja": [
                "fruit ninja gameplay no commentary",
                "fruit ninja classic mode",
                "fruit ninja zen mode gameplay"
            ]
        }
    
    def get_video_info(self, url: str, max_duration: int = 600) -> Optional[YouTubeVideoInfo]:
        """Get video information from YouTube URL.
        
        Args:
            url: YouTube video URL
            max_duration: Maximum video duration in seconds (default 10 minutes)
            
        Returns:
            Video information or None if extraction fails
        """
        try:
            # Get video info with yt-dlp
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-playlist",
                f"--match-filter", f"duration<{max_duration}",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"yt-dlp error: {result.stderr}")
                return None
            
            if not result.stdout.strip():
                logger.error(f"No output from yt-dlp for {url}")
                return None
                
            info = json.loads(result.stdout)
            
            # Find best format (1080p preferred, no audio needed)
            best_format = self._find_best_format(info)
            
            if not best_format:
                logger.warning(f"No suitable format found for {url}")
                return None
            
            return YouTubeVideoInfo(
                url=url,
                title=self._clean_title(info.get("title", "Unknown")),
                duration=info.get("duration", 0),
                resolution=f"{best_format.get('width', 0)}x{best_format.get('height', 0)}",
                filesize=best_format.get("filesize"),
                format_id=best_format["format_id"],
                direct_url=best_format["url"]
            )
            
        except Exception as e:
            logger.error(f"Error getting video info from {url}: {e}")
            return None
    
    def search_videos(self, query: str, max_results: int = 5) -> List[str]:
        """Search YouTube for videos matching query.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of video URLs
        """
        try:
            cmd = [
                "yt-dlp",
                f"ytsearch{max_results}:{query}",
                "--get-id",
                "--no-playlist"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Search error: {result.stderr}")
                return []
            
            video_ids = result.stdout.strip().split('\n')
            urls = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids if vid]
            
            return urls
            
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return []
    
    def generate_gaming_urls(self, category: str = "all") -> Dict[str, List[str]]:
        """Generate list of gaming video URLs for download.
        
        Args:
            category: Gaming category or "all"
            
        Returns:
            Dictionary of category -> list of video URLs
        """
        urls = {}
        
        categories = list(self.search_terms.keys()) if category == "all" else [category]
        
        for cat in categories:
            if cat not in self.search_terms:
                continue
                
            cat_urls = []
            
            # Search for videos
            for term in self.search_terms[cat]:
                logger.info(f"Searching YouTube for: {term}")
                found_urls = self.search_videos(term, max_results=3)
                cat_urls.extend(found_urls)
            
            urls[cat] = cat_urls[:10]  # Limit to 10 per category
        
        return urls
    
    def create_download_file(self, output_path: Path, category: str = "all") -> bool:
        """Create a download file with YouTube gaming video URLs.
        
        Args:
            output_path: Path to save the URL file
            category: Gaming category or "all"
            
        Returns:
            Success boolean
        """
        try:
            urls = self.generate_gaming_urls(category)
            
            with open(output_path, 'w') as f:
                f.write("# YouTube Gaming Video URLs\n")
                f.write("# Generated for background video library\n")
                f.write("# Format: URL [category] [subcategory] [filename]\n\n")
                
                for cat, video_urls in urls.items():
                    f.write(f"\n# {cat.upper()}\n")
                    
                    for url in video_urls:
                        # Get video info to create proper filename
                        info = self.get_video_info(url, max_duration=600)  # 10 min max for gaming
                        
                        if info:
                            filename = self._create_filename(info.title, cat)
                            f.write(f"{info.direct_url} gaming {cat} {filename}\n")
                            logger.info(f"Added: {filename} ({info.resolution}, {info.duration}s)")
                        else:
                            logger.warning(f"Skipped {url} - could not get info")
            
            logger.info(f"Created download file: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating download file: {e}")
            return False
    
    def _find_best_format(self, info: Dict) -> Optional[Dict]:
        """Find best video format (1080p preferred, video only)."""
        formats = info.get("formats", [])
        
        # Filter video-only formats that have a direct URL (not HLS/DASH)
        video_formats = [
            f for f in formats 
            if f.get("vcodec") != "none" 
            and f.get("acodec") == "none"
            and f.get("url")  # Must have direct URL
            and not f.get("manifest_url")  # Avoid HLS/DASH manifests
            and f.get("ext") == "mp4"  # Prefer MP4
        ]
        
        # Sort by resolution preference
        resolution_priority = ["1920x1080", "1280x720", "854x480"]
        
        for res in resolution_priority:
            width, height = map(int, res.split('x'))
            for fmt in video_formats:
                if fmt.get("width") == width and fmt.get("height") == height:
                    return fmt
        
        # Fallback to any HD video
        hd_formats = [f for f in video_formats if f.get("height", 0) >= 720]
        if hd_formats:
            return max(hd_formats, key=lambda f: f.get("height", 0))
        
        # Last resort - any video format with direct URL
        return video_formats[0] if video_formats else None
    
    def _clean_title(self, title: str) -> str:
        """Clean video title for use as filename."""
        # Remove special characters and limit length
        clean = re.sub(r'[^\w\s-]', '', title.lower())
        clean = re.sub(r'[-\s]+', '_', clean)
        return clean[:50]
    
    def _create_filename(self, title: str, category: str) -> str:
        """Create filename from title and category."""
        clean_title = self._clean_title(title)
        # Remove common words
        remove_words = ["gameplay", "no_commentary", "walkthrough", "lets_play", "part", "episode"]
        for word in remove_words:
            clean_title = clean_title.replace(word, "")
        clean_title = re.sub(r'_+', '_', clean_title).strip('_')
        
        return f"yt_{category}_{clean_title}"[:60]


def create_youtube_helper() -> YouTubeHelper:
    """Create and return a YouTube helper instance."""
    return YouTubeHelper()