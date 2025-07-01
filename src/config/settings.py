"""
Application settings and configuration management.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Application Info
    VERSION: str = "0.1.0"
    APP_NAME: str = "Reddit-to-TikTok Automation"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ELEVENLABS_API_KEY: Optional[str] = Field(default=None, env="ELEVENLABS_API_KEY")
    
    # Platform API Keys
    TIKTOK_API_KEY: Optional[str] = Field(default=None, env="TIKTOK_API_KEY")
    YOUTUBE_API_KEY: Optional[str] = Field(default=None, env="YOUTUBE_API_KEY")
    INSTAGRAM_API_KEY: Optional[str] = Field(default=None, env="INSTAGRAM_API_KEY")
    
    # TTS Configuration
    DEFAULT_TTS_PROVIDER: str = Field(default="openai", env="DEFAULT_TTS_PROVIDER")
    DEFAULT_VOICE: str = Field(default="alloy", env="DEFAULT_VOICE")
    ELEVENLABS_VOICE_ID: Optional[str] = Field(default=None, env="ELEVENLABS_VOICE_ID")
    
    # Video Processing
    VIDEO_OUTPUT_FORMAT: str = Field(default="mp4", env="VIDEO_OUTPUT_FORMAT")
    VIDEO_RESOLUTION: str = Field(default="1080x1920", env="VIDEO_RESOLUTION")
    VIDEO_FPS: int = Field(default=30, env="VIDEO_FPS")
    VIDEO_BITRATE: int = Field(default=3500, env="VIDEO_BITRATE")
    MAX_VIDEO_DURATION: int = Field(default=180, env="MAX_VIDEO_DURATION")
    
    # Content Processing
    QUALITY_THRESHOLD: float = Field(default=0.7, env="QUALITY_THRESHOLD")
    MIN_WORD_COUNT: int = Field(default=150, env="MIN_WORD_COUNT")
    MAX_WORD_COUNT: int = Field(default=500, env="MAX_WORD_COUNT")
    ENABLE_EMOTIONAL_ANALYSIS: bool = Field(default=True, env="ENABLE_EMOTIONAL_ANALYSIS")
    
    # File Paths
    OUTPUT_DIRECTORY: str = Field(default="./output", env="OUTPUT_DIRECTORY")
    ASSETS_DIRECTORY: str = Field(default="./assets", env="ASSETS_DIRECTORY")
    BACKGROUND_VIDEOS_PATH: str = Field(default="./assets/backgrounds", env="BACKGROUND_VIDEOS_PATH")
    MUSIC_PATH: str = Field(default="./assets/music", env="MUSIC_PATH")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./app.db", env="DATABASE_URL")
    
    # Platform Settings
    TIKTOK_MAX_FILE_SIZE: int = Field(default=287, env="TIKTOK_MAX_FILE_SIZE")  # MB
    YOUTUBE_SHORTS_MAX_DURATION: int = Field(default=60, env="YOUTUBE_SHORTS_MAX_DURATION")  # seconds
    INSTAGRAM_REELS_MAX_DURATION: int = Field(default=90, env="INSTAGRAM_REELS_MAX_DURATION")  # seconds
    
    # Scheduling
    ENABLE_SCHEDULING: bool = Field(default=True, env="ENABLE_SCHEDULING")
    DEFAULT_TIMEZONE: str = Field(default="EST", env="DEFAULT_TIMEZONE")
    
    # Analytics
    ENABLE_ANALYTICS: bool = Field(default=True, env="ENABLE_ANALYTICS")
    ANALYTICS_RETENTION_DAYS: int = Field(default=365, env="ANALYTICS_RETENTION_DAYS")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-this", env="SECRET_KEY")
    
    # Rate Limiting
    API_RATE_LIMIT: int = Field(default=100, env="API_RATE_LIMIT")
    TTS_RATE_LIMIT: int = Field(default=50, env="TTS_RATE_LIMIT")
    
    # Feature Flags
    ENABLE_MULTI_PLATFORM: bool = Field(default=True, env="ENABLE_MULTI_PLATFORM")
    ENABLE_A_B_TESTING: bool = Field(default=True, env="ENABLE_A_B_TESTING")
    ENABLE_BATCH_PROCESSING: bool = Field(default=True, env="ENABLE_BATCH_PROCESSING")
    ENABLE_MOBILE_API: bool = Field(default=False, env="ENABLE_MOBILE_API")
    ENABLE_BROWSER_EXTENSION: bool = Field(default=False, env="ENABLE_BROWSER_EXTENSION")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent
    
    @property
    def src_root(self) -> Path:
        """Get the source code root directory."""
        return Path(__file__).parent.parent
    
    def get_output_path(self, subfolder: str = "") -> Path:
        """Get output directory path."""
        path = self.project_root / self.OUTPUT_DIRECTORY.lstrip("./")
        if subfolder:
            path = path / subfolder
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_assets_path(self, subfolder: str = "") -> Path:
        """Get assets directory path."""
        path = self.project_root / self.ASSETS_DIRECTORY.lstrip("./")
        if subfolder:
            path = path / subfolder
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings