# 🎮 YouTube Gaming Video Download Guide

This guide shows you how to download gaming background videos from YouTube for your Reddit-to-TikTok videos.

## 🚀 Quick Start

### 1. Install Prerequisites
```bash
# yt-dlp should already be installed, but if not:
pip install yt-dlp
```

### 2. Generate Gaming URLs Automatically
```bash
# Generate URLs for all gaming categories
python src/cli.py download youtube-gaming

# Or specific category only
python src/cli.py download youtube-gaming --category minecraft_parkour
```

### 3. Download the Videos
```bash
# Download all videos from the generated file
python src/cli.py download batch youtube_gaming_urls.txt
```

### 4. Preview and Approve
```bash
# See what was downloaded
python src/cli.py download preview

# Open folder to watch videos
open assets/backgrounds_staging/

# Approve the good ones
python src/cli.py download approve-all
```

## 📹 Supported Gaming Categories

1. **minecraft_parkour** - Minecraft parkour and jumping gameplay
2. **subway_surfers** - Subway Surfers endless runner
3. **temple_run** - Temple Run adventure gameplay
4. **fruit_ninja** - Fruit Ninja slicing action

## 🔍 Finding Good Gaming Videos

### What to Look For:
- **No Commentary** - Pure gameplay footage
- **No Music** - Or minimal background music
- **Clean UI** - Minimal overlays or HUD elements
- **High Quality** - 1080p or 720p resolution
- **Good Length** - 1-5 minutes (for looping)
- **Steady Gameplay** - Smooth, consistent action

### What to Avoid:
- Videos with commentary or reactions
- Heavy music or sound effects
- Tutorial overlays or annotations
- Low resolution or poor quality
- Videos with watermarks
- Copyrighted content warnings

## 🎯 Manual YouTube Downloads

### Step 1: Find a Video
Browse YouTube for gaming videos. Good search terms:
- "minecraft parkour no commentary"
- "subway surfers gameplay no music"
- "temple run 2 pure gameplay"
- "fruit ninja zen mode no sound"

### Step 2: Get Video Info
```bash
python src/cli.py download youtube-info "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Step 3: Create URL File
Create a text file (e.g., `gaming_urls.txt`):
```
# Format: URL category subcategory filename
https://direct-url-from-youtube-info.googlevideo.com/... gaming minecraft_parkour epic_parkour_run
https://another-direct-url.googlevideo.com/... gaming subway_surfers urban_dash
```

### Step 4: Download Batch
```bash
python src/cli.py download batch gaming_urls.txt
```

## 🛠️ Advanced Usage

### Custom Search Terms
Edit `src/generators/youtube_helper.py` to add your own search terms:
```python
self.search_terms = {
    "minecraft_parkour": [
        "your custom search term",
        "another search term"
    ]
}
```

### Direct Channel Downloads
Some reliable gaming channels:

**Minecraft Parkour:**
- https://www.youtube.com/@WadZee
- https://www.youtube.com/@PrestonPlayz

**Mobile Games:**
- https://www.youtube.com/@Oddbods
- https://www.youtube.com/@KiranJayakar

### Filtering Options
The YouTube helper automatically:
- Filters videos over 10 minutes
- Prefers 1080p resolution
- Selects video-only formats (no audio)
- Cleans titles for filenames

## 📊 Storage Considerations

YouTube videos are larger than stock footage:
- **Pixabay/Pexels**: 5-50 MB per video
- **YouTube Gaming**: 50-200 MB per video

Plan your storage accordingly!

## ⚡ Workflow Example

Complete workflow for Minecraft videos:
```bash
# 1. Generate Minecraft URLs
python src/cli.py download youtube-gaming --category minecraft_parkour

# 2. Review what will be downloaded
cat youtube_gaming_urls.txt

# 3. Download videos (this may take time)
python src/cli.py download batch youtube_gaming_urls.txt

# 4. Check staging area
python src/cli.py download stats
python src/cli.py download preview

# 5. Preview videos in your media player
open assets/backgrounds_staging/gaming/minecraft_parkour/

# 6. Approve the good ones
python src/cli.py download approve-all

# 7. Test with a Reddit story
python src/cli.py create-video --text "Your AITA story here..." --background minecraft_parkour --format tiktok
```

## 🎨 Tips for Best Results

1. **Download in Batches**: Don't download too many at once
2. **Preview Everything**: Not all gaming videos work well as backgrounds
3. **Check Licenses**: Respect content creators and YouTube's terms
4. **Optimize Storage**: Delete rejected videos promptly
5. **Test Integration**: Generate test videos to see how backgrounds look

## 🔧 Troubleshooting

### yt-dlp Errors
If yt-dlp fails:
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Test manually
yt-dlp --version
yt-dlp -F "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download Failures
- Check internet connection
- Try smaller/shorter videos
- Verify the video is public
- Some videos may be region-locked

### Storage Issues
- Clear staging area regularly
- Compress approved videos if needed
- Use external storage for large libraries

## 📝 Legal Notes

- Respect YouTube's Terms of Service
- Check video licenses and creator permissions  
- Use videos only as backgrounds, not as main content
- Give credit where required
- Consider fair use guidelines

## 🎮 Ready to Download!

You now have everything needed to build a gaming video library:

```bash
# Quick start - download everything!
python src/cli.py download youtube-gaming
python src/cli.py download batch youtube_gaming_urls.txt
python src/cli.py download preview
```

Happy downloading! 🚀