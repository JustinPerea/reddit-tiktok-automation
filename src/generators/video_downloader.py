"""
Automated Background Video Downloader

Downloads high-quality background videos from free sources to build the video library.
Supports multiple sources with intelligent categorization and quality validation.
"""

import os
import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import hashlib
from urllib.parse import urlparse

from utils.logger import get_logger
from generators.background_video_library import VideoCategory, VideoSubcategory

logger = get_logger("VideoDownloader")


class VideoSource(Enum):
    """Supported video download sources."""
    PIXABAY = "pixabay"
    PEXELS = "pexels"
    UNSPLASH = "unsplash"
    VIDEVO = "videvo"
    DIRECT_URL = "direct_url"


@dataclass
class VideoMetadata:
    """Metadata for a downloaded video."""
    source: VideoSource
    source_id: str
    title: str
    description: str
    tags: List[str]
    duration: float
    resolution: Tuple[int, int]
    file_size: int
    download_url: str
    license: str
    author: str = ""
    author_url: str = ""
    downloaded_at: str = ""


@dataclass
class DownloadRequest:
    """Request for downloading a specific video."""
    url: str
    category: VideoCategory
    subcategory: VideoSubcategory
    source: VideoSource = VideoSource.DIRECT_URL
    custom_filename: Optional[str] = None
    expected_tags: List[str] = None


class VideoDownloader:
    """Downloads and manages background videos from various sources."""
    
    def __init__(self):
        """Initialize the video downloader."""
        self.base_path = Path("assets/backgrounds")
        self.staging_path = Path("assets/backgrounds_staging")
        self.cache_path = Path("assets/backgrounds/.cache")
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.staging_path.mkdir(parents=True, exist_ok=True)
        
        # API keys (optional - many sources work without keys)
        self.api_keys = {
            VideoSource.PIXABAY: os.getenv("PIXABAY_API_KEY"),
            VideoSource.PEXELS: os.getenv("PEXELS_API_KEY"),
            VideoSource.UNSPLASH: os.getenv("UNSPLASH_ACCESS_KEY")
        }
        
        # Download session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Predefined search terms for each subcategory
        self.search_terms = {
            VideoSubcategory.MINECRAFT_PARKOUR: ["minecraft", "parkour", "gaming", "blocks"],
            VideoSubcategory.SUBWAY_SURFERS: ["subway", "urban", "city", "running"],
            VideoSubcategory.TEMPLE_RUN: ["temple", "adventure", "jungle", "ancient"],
            VideoSubcategory.FRUIT_NINJA: ["fruit", "cutting", "kitchen", "food"],
            VideoSubcategory.SLIME_MIXING: ["slime", "mixing", "colorful", "satisfying"],
            VideoSubcategory.KINETIC_SAND: ["sand", "kinetic", "asmr", "satisfying"],
            VideoSubcategory.SOAP_CUTTING: ["soap", "cutting", "asmr", "satisfying"],
            VideoSubcategory.RAIN_WINDOW: ["rain", "window", "drops", "glass"],
            VideoSubcategory.OCEAN_WAVES: ["ocean", "waves", "sea", "water"],
            VideoSubcategory.FIREPLACE: ["fireplace", "fire", "cozy", "warm"],
            VideoSubcategory.GEOMETRIC_PATTERNS: ["geometric", "patterns", "abstract", "shapes"],
            VideoSubcategory.COLOR_GRADIENTS: ["gradient", "colors", "abstract", "smooth"],
            VideoSubcategory.PARTICLE_EFFECTS: ["particles", "effects", "abstract", "digital"],
            VideoSubcategory.COOKING_ASMR: ["cooking", "food", "kitchen", "preparation"]
        }
        
        logger.info("Video downloader initialized")
    
    def download_from_url(self, request: DownloadRequest) -> Optional[Path]:
        """Download a video from a direct URL."""
        try:
            # Validate URL
            parsed_url = urlparse(request.url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.error(f"Invalid URL: {request.url}")
                return None
            
            # Generate filename and hash
            url_hash = hashlib.md5(request.url.encode()).hexdigest()[:8]
            if request.custom_filename:
                filename = request.custom_filename
                if not filename.endswith('.mp4'):
                    filename += '.mp4'
            else:
                # Generate filename from URL and content
                filename = f"{request.subcategory.value}_{url_hash}.mp4"
            
            # Create target directory in staging area
            target_dir = self.staging_path / request.category.value / request.subcategory.value
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / filename
            
            # Skip if already exists
            if target_path.exists():
                logger.info(f"Video already exists: {target_path}")
                return target_path
            
            # Download video
            logger.info(f"Downloading video from {request.url}")
            
            response = self.session.get(request.url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Write video file
            temp_path = target_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Validate video file
            if self._validate_video_file(temp_path):
                temp_path.rename(target_path)
                
                # Save metadata
                metadata = VideoMetadata(
                    source=request.source,
                    source_id=url_hash,
                    title=filename,
                    description=f"Downloaded from {parsed_url.netloc}",
                    tags=request.expected_tags or [],
                    duration=0.0,  # Will be filled by validation
                    resolution=(0, 0),  # Will be filled by validation
                    file_size=target_path.stat().st_size,
                    download_url=request.url,
                    license="Unknown",
                    downloaded_at=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                
                self._save_metadata(target_path, metadata)
                
                logger.info(f"Successfully downloaded: {target_path}")
                return target_path
            else:
                temp_path.unlink(missing_ok=True)
                logger.error(f"Downloaded file failed validation: {request.url}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading video from {request.url}: {e}")
            return None
    
    def download_from_pixabay(self, subcategory: VideoSubcategory, count: int = 5) -> List[Path]:
        """Download videos from Pixabay API."""
        if not self.api_keys[VideoSource.PIXABAY]:
            logger.warning("Pixabay API key not found. Set PIXABAY_API_KEY environment variable.")
            return []
        
        try:
            search_terms = self.search_terms.get(subcategory, ["abstract"])
            category = self._get_category_for_subcategory(subcategory)
            downloaded_videos = []
            
            for term in search_terms[:2]:  # Use first 2 search terms
                logger.info(f"Searching Pixabay for '{term}' videos")
                
                # Pixabay API request
                url = "https://pixabay.com/api/videos/"
                params = {
                    'key': self.api_keys[VideoSource.PIXABAY],
                    'q': term,
                    'video_type': 'all',
                    'per_page': max(3, min(count, 20)),  # Pixabay requires minimum 3
                    'safesearch': 'true'
                }
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code != 200:
                    logger.error(f"Pixabay API error {response.status_code}: {response.text}")
                    continue
                
                data = response.json()
                
                for video in data.get('hits', [])[:count]:
                    try:
                        # Get the best quality video URL
                        video_url = None
                        for size in ['large', 'medium', 'small']:
                            if size in video.get('videos', {}):
                                video_url = video['videos'][size]['url']
                                break
                        
                        if not video_url:
                            continue
                        
                        # Create download request
                        request = DownloadRequest(
                            url=video_url,
                            category=category,
                            subcategory=subcategory,
                            source=VideoSource.PIXABAY,
                            custom_filename=f"pixabay_{video['id']}_{term}",
                            expected_tags=video.get('tags', '').split(', ')
                        )
                        
                        downloaded_path = self.download_from_url(request)
                        if downloaded_path:
                            downloaded_videos.append(downloaded_path)
                            
                            # Save enhanced metadata
                            metadata = VideoMetadata(
                                source=VideoSource.PIXABAY,
                                source_id=str(video['id']),
                                title=term.title() + " Video",
                                description=f"Pixabay video for {subcategory.value}",
                                tags=video.get('tags', '').split(', '),
                                duration=video.get('duration', 0),
                                resolution=(video.get('picture_width', 0), video.get('picture_height', 0)),
                                file_size=downloaded_path.stat().st_size,
                                download_url=video_url,
                                license="Pixabay License",
                                author=video.get('user', ''),
                                author_url=f"https://pixabay.com/users/{video.get('user', '')}/",
                                downloaded_at=time.strftime("%Y-%m-%d %H:%M:%S")
                            )
                            
                            self._save_metadata(downloaded_path, metadata)
                        
                        # Rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.warning(f"Error downloading Pixabay video {video.get('id', 'unknown')}: {e}")
                        continue
            
            logger.info(f"Downloaded {len(downloaded_videos)} videos from Pixabay for {subcategory.value}")
            return downloaded_videos
            
        except Exception as e:
            logger.error(f"Error downloading from Pixabay: {e}")
            return []
    
    def download_from_pexels(self, subcategory: VideoSubcategory, count: int = 5) -> List[Path]:
        """Download videos from Pexels API."""
        if not self.api_keys[VideoSource.PEXELS]:
            logger.warning("Pexels API key not found. Set PEXELS_API_KEY environment variable.")
            return []
        
        try:
            search_terms = self.search_terms.get(subcategory, ["abstract"])
            category = self._get_category_for_subcategory(subcategory)
            downloaded_videos = []
            
            headers = {
                'Authorization': self.api_keys[VideoSource.PEXELS],
                'User-Agent': 'Reddit-TikTok-Automation/1.0'
            }
            
            for term in search_terms[:2]:
                logger.info(f"Searching Pexels for '{term}' videos")
                
                url = "https://api.pexels.com/videos/search"
                params = {
                    'query': term,
                    'per_page': min(count, 20),
                    'size': 'large'
                }
                
                response = self.session.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                for video in data.get('videos', [])[:count]:
                    try:
                        # Get the best quality video file
                        video_file = None
                        for file in video.get('video_files', []):
                            if file.get('quality') == 'hd':
                                video_file = file
                                break
                        
                        if not video_file:
                            video_file = video.get('video_files', [{}])[0]
                        
                        if not video_file.get('link'):
                            continue
                        
                        request = DownloadRequest(
                            url=video_file['link'],
                            category=category,
                            subcategory=subcategory,
                            source=VideoSource.PEXELS,
                            custom_filename=f"pexels_{video['id']}_{term}",
                            expected_tags=[term]
                        )
                        
                        downloaded_path = self.download_from_url(request)
                        if downloaded_path:
                            downloaded_videos.append(downloaded_path)
                            
                            # Save enhanced metadata
                            metadata = VideoMetadata(
                                source=VideoSource.PEXELS,
                                source_id=str(video['id']),
                                title=f"Pexels {term.title()} Video",
                                description=f"Pexels video for {subcategory.value}",
                                tags=[term],
                                duration=video.get('duration', 0),
                                resolution=(video.get('width', 0), video.get('height', 0)),
                                file_size=downloaded_path.stat().st_size,
                                download_url=video_file['link'],
                                license="Pexels License",
                                author=video.get('user', {}).get('name', ''),
                                author_url=video.get('user', {}).get('url', ''),
                                downloaded_at=time.strftime("%Y-%m-%d %H:%M:%S")
                            )
                            
                            self._save_metadata(downloaded_path, metadata)
                        
                        time.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        logger.warning(f"Error downloading Pexels video {video.get('id', 'unknown')}: {e}")
                        continue
            
            logger.info(f"Downloaded {len(downloaded_videos)} videos from Pexels for {subcategory.value}")
            return downloaded_videos
            
        except Exception as e:
            logger.error(f"Error downloading from Pexels: {e}")
            return []
    
    def bulk_download_category(self, category: VideoCategory, videos_per_subcategory: int = 3) -> Dict[VideoSubcategory, List[Path]]:
        """Download videos for an entire category."""
        results = {}
        
        # Get subcategories for this category
        subcategory_map = {
            VideoCategory.GAMING: [VideoSubcategory.MINECRAFT_PARKOUR, VideoSubcategory.SUBWAY_SURFERS, 
                                  VideoSubcategory.TEMPLE_RUN, VideoSubcategory.FRUIT_NINJA],
            VideoCategory.SATISFYING: [VideoSubcategory.SLIME_MIXING, VideoSubcategory.KINETIC_SAND, 
                                     VideoSubcategory.SOAP_CUTTING],
            VideoCategory.NATURE: [VideoSubcategory.RAIN_WINDOW, VideoSubcategory.OCEAN_WAVES, 
                                 VideoSubcategory.FIREPLACE],
            VideoCategory.ABSTRACT: [VideoSubcategory.GEOMETRIC_PATTERNS, VideoSubcategory.COLOR_GRADIENTS, 
                                   VideoSubcategory.PARTICLE_EFFECTS],
            VideoCategory.LIFESTYLE: [VideoSubcategory.COOKING_ASMR]
        }
        
        subcategories = subcategory_map.get(category, [])
        
        for subcategory in subcategories:
            logger.info(f"Downloading videos for {subcategory.value}")
            
            downloaded = []
            
            # Try multiple sources
            if self.api_keys[VideoSource.PIXABAY]:
                downloaded.extend(self.download_from_pixabay(subcategory, videos_per_subcategory))
            
            if self.api_keys[VideoSource.PEXELS] and len(downloaded) < videos_per_subcategory:
                remaining = videos_per_subcategory - len(downloaded)
                downloaded.extend(self.download_from_pexels(subcategory, remaining))
            
            results[subcategory] = downloaded
            
            # Brief pause between subcategories
            time.sleep(2)
        
        return results
    
    def download_from_url_list(self, url_file: Path) -> List[Path]:
        """Download videos from a text file containing URLs."""
        if not url_file.exists():
            logger.error(f"URL file not found: {url_file}")
            return []
        
        downloaded_videos = []
        
        try:
            with open(url_file, 'r') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse line: URL [category] [subcategory] [filename]
                parts = line.split()
                if len(parts) < 1:
                    continue
                
                url = parts[0]
                category = VideoCategory.ABSTRACT  # Default
                subcategory = VideoSubcategory.GEOMETRIC_PATTERNS  # Default
                filename = None
                
                if len(parts) >= 2:
                    try:
                        category = VideoCategory(parts[1])
                    except ValueError:
                        logger.warning(f"Invalid category '{parts[1]}' on line {line_num}")
                
                if len(parts) >= 3:
                    try:
                        subcategory = VideoSubcategory(parts[2])
                    except ValueError:
                        logger.warning(f"Invalid subcategory '{parts[2]}' on line {line_num}")
                
                if len(parts) >= 4:
                    filename = parts[3]
                
                request = DownloadRequest(
                    url=url,
                    category=category,
                    subcategory=subcategory,
                    custom_filename=filename
                )
                
                downloaded_path = self.download_from_url(request)
                if downloaded_path:
                    downloaded_videos.append(downloaded_path)
                
                # Brief pause between downloads
                time.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Error processing URL file: {e}")
        
        logger.info(f"Downloaded {len(downloaded_videos)} videos from URL file")
        return downloaded_videos
    
    def _validate_video_file(self, video_path: Path) -> bool:
        """Validate video file using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json", 
                "-show_format", "-show_streams", str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return False
            
            data = json.loads(result.stdout)
            
            # Check if it has video stream
            video_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']
            if not video_streams:
                return False
            
            # Check minimum duration (at least 1 second)
            duration = float(data.get('format', {}).get('duration', 0))
            if duration < 1.0:
                return False
            
            # Check minimum resolution
            video_stream = video_streams[0]
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            if width < 480 or height < 480:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating video file {video_path}: {e}")
            return False
    
    def _save_metadata(self, video_path: Path, metadata: VideoMetadata):
        """Save video metadata to cache."""
        try:
            metadata_path = self.cache_path / f"{video_path.stem}.json"
            
            # Convert metadata to dict and handle enum serialization
            metadata_dict = asdict(metadata)
            metadata_dict['source'] = metadata.source.value  # Convert enum to string
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not save metadata for {video_path}: {e}")
    
    def _get_category_for_subcategory(self, subcategory: VideoSubcategory) -> VideoCategory:
        """Get the parent category for a subcategory."""
        mapping = {
            VideoSubcategory.MINECRAFT_PARKOUR: VideoCategory.GAMING,
            VideoSubcategory.SUBWAY_SURFERS: VideoCategory.GAMING,
            VideoSubcategory.TEMPLE_RUN: VideoCategory.GAMING,
            VideoSubcategory.FRUIT_NINJA: VideoCategory.GAMING,
            VideoSubcategory.SLIME_MIXING: VideoCategory.SATISFYING,
            VideoSubcategory.KINETIC_SAND: VideoCategory.SATISFYING,
            VideoSubcategory.SOAP_CUTTING: VideoCategory.SATISFYING,
            VideoSubcategory.RAIN_WINDOW: VideoCategory.NATURE,
            VideoSubcategory.OCEAN_WAVES: VideoCategory.NATURE,
            VideoSubcategory.FIREPLACE: VideoCategory.NATURE,
            VideoSubcategory.GEOMETRIC_PATTERNS: VideoCategory.ABSTRACT,
            VideoSubcategory.COLOR_GRADIENTS: VideoCategory.ABSTRACT,
            VideoSubcategory.PARTICLE_EFFECTS: VideoCategory.ABSTRACT,
            VideoSubcategory.COOKING_ASMR: VideoCategory.LIFESTYLE
        }
        return mapping.get(subcategory, VideoCategory.ABSTRACT)
    
    def get_staging_videos(self) -> List[Dict[str, any]]:
        """Get list of videos in staging area for preview."""
        staging_videos = []
        
        if not self.staging_path.exists():
            return staging_videos
        
        for video_file in sorted(self.staging_path.rglob("*.mp4")):
            # Get relative path components
            relative_path = video_file.relative_to(self.staging_path)
            parts = relative_path.parts
            
            if len(parts) >= 3:  # category/subcategory/filename
                category = parts[0]
                subcategory = parts[1]
                
                video_info = {
                    "path": str(video_file),
                    "filename": video_file.name,
                    "category": category,
                    "subcategory": subcategory,
                    "size_mb": round(video_file.stat().st_size / (1024 * 1024), 2),
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", 
                                            time.localtime(video_file.stat().st_mtime))
                }
                
                # Try to load metadata if exists
                metadata_path = self.cache_path / f"{video_file.stem}.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            video_info["metadata"] = metadata
                    except:
                        pass
                
                staging_videos.append(video_info)
        
        return staging_videos
    
    def approve_video(self, staging_path: str) -> bool:
        """Approve a video and move it from staging to main library."""
        try:
            staging_file = Path(staging_path)
            if not staging_file.exists():
                logger.error(f"Staging file not found: {staging_path}")
                return False
            
            # Get relative path from staging
            relative_path = staging_file.relative_to(self.staging_path)
            
            # Create target path in main library
            target_path = self.base_path / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            staging_file.rename(target_path)
            logger.info(f"Approved and moved video to: {target_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error approving video: {e}")
            return False
    
    def reject_video(self, staging_path: str) -> bool:
        """Reject a video and remove it from staging."""
        try:
            staging_file = Path(staging_path)
            if not staging_file.exists():
                logger.error(f"Staging file not found: {staging_path}")
                return False
            
            # Delete the file
            staging_file.unlink()
            
            # Remove metadata if exists
            metadata_path = self.cache_path / f"{staging_file.stem}.json"
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Rejected and removed video: {staging_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting video: {e}")
            return False
    
    def approve_all_staging(self) -> int:
        """Approve all videos in staging area."""
        approved_count = 0
        
        for video_info in self.get_staging_videos():
            if self.approve_video(video_info["path"]):
                approved_count += 1
        
        return approved_count
    
    def get_download_stats(self) -> Dict[str, any]:
        """Get statistics about downloaded videos."""
        stats = {
            "total_videos": 0,
            "total_size_mb": 0,
            "by_category": {},
            "by_source": {},
            "metadata_files": 0,
            "staging_videos": 0,
            "staging_size_mb": 0
        }
        
        # Count video files in main library
        for category_dir in self.base_path.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith('.'):
                continue
                
            category_stats = {"videos": 0, "size_mb": 0}
            
            for subcategory_dir in category_dir.iterdir():
                if not subcategory_dir.is_dir():
                    continue
                
                for video_file in subcategory_dir.glob("*.mp4"):
                    stats["total_videos"] += 1
                    category_stats["videos"] += 1
                    
                    file_size = video_file.stat().st_size / (1024 * 1024)
                    stats["total_size_mb"] += file_size
                    category_stats["size_mb"] += file_size
            
            if category_stats["videos"] > 0:
                stats["by_category"][category_dir.name] = category_stats
        
        # Count staging videos
        if self.staging_path.exists():
            for video_file in self.staging_path.rglob("*.mp4"):
                stats["staging_videos"] += 1
                stats["staging_size_mb"] += video_file.stat().st_size / (1024 * 1024)
        
        # Count metadata files
        if self.cache_path.exists():
            stats["metadata_files"] = len(list(self.cache_path.glob("*.json")))
        
        # Round sizes
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        stats["staging_size_mb"] = round(stats["staging_size_mb"], 2)
        for category in stats["by_category"].values():
            category["size_mb"] = round(category["size_mb"], 2)
        
        return stats


def create_video_downloader() -> VideoDownloader:
    """Create and return a video downloader instance."""
    return VideoDownloader()