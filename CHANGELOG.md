# Changelog

All notable changes to the Reddit-to-TikTok Automation System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-07-02

### Fixed
- **🎯 Perfect Text Synchronization**: Fixed text overlay synchronization with audio using intelligent Edge TTS timing detection
  - Previously: Text used artificial fixed timing (350ms per word) from WhisperS2T segments
  - Now: Automatically detects and uses Edge TTS perfect word-level timing when available
  - Result: Natural text synchronization (87ms to 474ms per word based on speech complexity)
  - Maintains backward compatibility with gTTS/WhisperS2T timing as fallback
  - Technical: Added Edge TTS timing cache detection in both main generation and analysis paths

- **Video Aspect Ratio Preservation**: Fixed critical issue where background videos were being stretched to fit vertical formats instead of properly cropped
  - Previously: Videos were scaled directly to 1080x1920, causing distortion
  - Now: Videos maintain original aspect ratio with center cropping
  - Technical: Updated FFmpeg filter to use `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`
  - Affects all video formats (TikTok, Instagram Reels, YouTube Shorts)

### Added
- Downloaded 4 new Minecraft parkour background videos (805.6 MB total)
  - 5 minutes gameplay footage (x2)
  - 7 minutes gameplay footage
  - 4K 60fps vertical footage

## [1.0.0] - 2025-07-01

### Added
- Initial release with complete video generation pipeline
- Web interface for Reddit-to-TikTok conversion
- Hybrid TTS system with 4 free providers
- Edge TTS perfect synchronization
- Background video library with 14 styles
- Automatic quality scoring and content optimization