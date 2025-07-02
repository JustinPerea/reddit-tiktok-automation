# 📹 Background Video Download Guide

This guide shows you multiple efficient ways to build your background video library for the Reddit-to-TikTok automation system.

## 🚀 Quick Start Options

### Option 1: Automated API Downloads (Recommended)
**Fastest and highest quality** - Downloads directly from Pixabay and Pexels APIs

```bash
# Get API setup instructions
python src/cli.py download auto --api-keys

# Download 3 videos per subcategory for all categories
python src/cli.py download auto

# Download only specific categories
python src/cli.py download auto --category gaming --count 5
python src/cli.py download auto --category satisfying --count 3
```

### Option 2: Direct URL Downloads
**Most flexible** - Download any video from a direct URL

```bash
# Download a specific video
python src/cli.py download url "https://example.com/video.mp4" --category gaming --subcategory minecraft_parkour --filename epic_parkour

# Example with real URL
python src/cli.py download url "https://cdn.pixabay.com/vimeo/123456/example.mp4" --category nature --subcategory ocean_waves
```

### Option 3: Batch URL Downloads
**Most efficient for bulk** - Download multiple videos from a text file

```bash
# Generate example URL file
python src/cli.py download example-urls

# Download from URL file
python src/cli.py download batch video_urls.txt
```

## 🔑 API Key Setup (For Automated Downloads)

### 1. Pixabay API Key (Free)
1. Go to https://pixabay.com/api/docs/
2. Create a free account
3. Get your API key
4. Set environment variable: `export PIXABAY_API_KEY="your-key-here"`

### 2. Pexels API Key (Free)
1. Go to https://www.pexels.com/api/
2. Create a free account
3. Get your API key  
4. Set environment variable: `export PEXELS_API_KEY="your-key-here"`

### 3. Using .env File (Recommended)
Create a `.env` file in your project root:
```env
PIXABAY_API_KEY=your-pixabay-key-here
PEXELS_API_KEY=your-pexels-key-here
```

## 📁 Video Categories & Subcategories

### 🎮 Gaming
- **minecraft_parkour** - Minecraft parkour gameplay
- **subway_surfers** - Subway Surfers endless runner
- **temple_run** - Temple Run adventure gameplay  
- **fruit_ninja** - Fruit Ninja action gameplay

### 😌 Satisfying
- **slime_mixing** - Colorful slime mixing ASMR
- **kinetic_sand** - Kinetic sand manipulation
- **soap_cutting** - Soap cutting ASMR

### 🌿 Nature
- **rain_window** - Rain on window glass
- **ocean_waves** - Calming ocean scenes
- **fireplace** - Cozy fireplace videos

### 🎨 Abstract
- **geometric_patterns** - Animated geometric shapes
- **color_gradients** - Flowing color transitions
- **particle_effects** - Digital particle systems

### 🏠 Lifestyle
- **cooking_asmr** - Food preparation footage

## 📋 Batch Download File Format

Create a text file (e.g., `video_urls.txt`) with this format:

```
# Background Video URLs
# Format: URL [category] [subcategory] [filename]

# Gaming videos
https://cdn.pixabay.com/vimeo/460761836/minecraft.mp4 gaming minecraft_parkour epic_build
https://example.com/subway_video.mp4 gaming subway_surfers urban_run

# Nature videos  
https://example.com/rain_video.mp4 nature rain_window peaceful_rain
https://example.com/ocean_video.mp4 nature ocean_waves calm_waves

# Lines starting with # are ignored
```

## 🔍 Finding Quality Video URLs

### Free Video Sources

#### 1. Pixabay (Best for API)
- Website: https://pixabay.com/videos/
- API: Built-in support
- License: Free for commercial use
- Quality: High

#### 2. Pexels (Best for API)
- Website: https://www.pexels.com/videos/
- API: Built-in support  
- License: Free for commercial use
- Quality: Very high

#### 3. Unsplash (Manual)
- Website: https://unsplash.com/videos/
- License: Free for commercial use
- Quality: Professional
- Note: Copy video URLs manually

#### 4. Videvo (Manual)
- Website: https://www.videvo.net/
- License: Mix of free and paid
- Quality: Professional
- Note: Check license for each video

#### 5. Coverr (Manual)
- Website: https://coverr.co/
- License: Free for commercial use
- Quality: High
- Note: Beautiful aesthetic videos

### Getting Direct Video URLs

#### Method 1: Right-click video → "Copy video address"
Most reliable method for direct URLs.

#### Method 2: Browser Developer Tools
1. Open video page
2. Press F12 → Network tab
3. Refresh page
4. Look for .mp4 files
5. Copy URL

#### Method 3: Video Downloaders
Use tools like `youtube-dl` or `yt-dlp` for supported sites:
```bash
# Install yt-dlp
pip install yt-dlp

# Get video URL (doesn't download)
yt-dlp --get-url "https://example.com/video-page"
```

## 📊 Monitoring Your Library

```bash
# Check current library status
python src/cli.py download stats

# Scan and validate videos
python src/cli.py backgrounds scan
python src/cli.py backgrounds validate

# Test video selection
python src/cli.py backgrounds test-selection --story-type aita
```

## ⚡ Efficient Workflow Examples

### Build Complete Library (API Method)
```bash
# 1. Set up API keys first
export PIXABAY_API_KEY="your-key"
export PEXELS_API_KEY="your-key"

# 2. Download all categories (45+ videos)
python src/cli.py download auto --count 3

# 3. Check results
python src/cli.py download stats
```

### Build Specific Categories (URL Method)
```bash
# 1. Create URL file for gaming videos
python src/cli.py download example-urls > gaming_urls.txt

# 2. Edit file with real gaming video URLs
# 3. Download batch
python src/cli.py download batch gaming_urls.txt
```

### Quick Single Video Test
```bash
# Download one video to test
python src/cli.py download url "https://cdn.pixabay.com/vimeo/example.mp4" --category abstract --subcategory geometric_patterns --filename test_video
```

## 🎯 Video Requirements

### Technical Specs
- **Format**: MP4 (H.264 codec preferred)
- **Resolution**: 1080p minimum (1920x1080 or higher)
- **Duration**: 30 seconds to 5 minutes
- **Frame Rate**: 30 FPS recommended
- **Quality**: High bitrate, clear visuals
- **Aspect Ratio**: Any ratio supported (16:9, 9:16, 1:1, etc.)
  - Videos are automatically cropped to fit vertical formats
  - Original aspect ratio is preserved with center cropping
  - No stretching or distortion

### Content Guidelines
- **Safe for Work**: Family-friendly content only
- **Engaging**: Visually interesting and dynamic
- **Loop-friendly**: Should work well when repeated
- **No text overlays**: System adds its own text
- **Copyright-free**: Use only licensed content

## 🔧 Troubleshooting

### Common Issues

#### API Downloads Not Working
```bash
# Check API key status
python src/cli.py download auto --api-keys

# Verify environment variables
echo $PIXABAY_API_KEY
echo $PEXELS_API_KEY
```

#### Video Download Fails
- Check internet connection
- Verify URL is direct video link (ends with .mp4)
- Ensure video is publicly accessible
- Try smaller videos first

#### Video Validation Fails
- Video may be corrupted
- Check minimum resolution (480x480)
- Ensure minimum duration (1 second)
- Verify video has actual video stream

### Getting Help
```bash
# Show all download commands
python src/cli.py download --help

# Check system status
python src/cli.py backgrounds validate
python src/cli.py download stats
```

## 📈 Recommended Strategy

1. **Start with APIs** (if you have keys) - Highest quality, least effort
2. **Use batch downloads** for specific content you've curated
3. **Test video selection** to ensure good variety
4. **Monitor library stats** to track your progress
5. **Validate periodically** to catch any issues

With this system, you can efficiently build a professional background video library without manually downloading files one by one!