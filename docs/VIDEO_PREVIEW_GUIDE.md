# 🎬 Video Preview & Approval Guide

This guide explains how to preview and manage downloaded background videos before adding them to your main library.

## 📂 Staging Area Workflow

When you download videos, they're placed in a **staging area** where you can preview them before approving for use:

```
assets/backgrounds_staging/     ← Staging area (preview here)
assets/backgrounds/            ← Main library (approved videos)
```

## 🎯 Preview Process

### 1. Download Videos to Staging

```bash
# Download videos (they go to staging automatically)
python src/cli.py download auto --category nature --count 2
```

### 2. Check Staging Status

```bash
# See what's in staging
python src/cli.py download preview

# Check overall stats
python src/cli.py download stats
```

### 3. Preview Videos

#### Option A: Using Finder/Explorer
1. Open `assets/backgrounds_staging/` in Finder (Mac) or Explorer (Windows)
2. Navigate to category → subcategory folders
3. Double-click videos to preview in your default video player

#### Option B: Using Terminal
```bash
# Mac: Open staging folder in Finder
open assets/backgrounds_staging/

# Windows: Open staging folder in Explorer
explorer assets/backgrounds_staging/

# Linux: Open with file manager
xdg-open assets/backgrounds_staging/
```

### 4. Approve or Reject Videos

After previewing, decide which videos to keep:

```bash
# Approve specific video (moves to main library)
python src/cli.py download approve "assets/backgrounds_staging/nature/ocean_waves/pixabay_123_ocean.mp4"

# Approve ALL staging videos
python src/cli.py download approve-all

# Reject specific video (deletes it)
python src/cli.py download reject "assets/backgrounds_staging/nature/rain_window/pixabay_456_rain.mp4"
```

## 🎥 What to Look For

When previewing videos, check for:

### ✅ Good Videos
- **Visual Quality**: Clear, high resolution (1080p+)
- **Content**: Engaging, dynamic movement
- **Duration**: 30+ seconds (for looping)
- **Style**: Matches the subcategory (e.g., "rain_window" should show rain on glass)
- **No Watermarks**: Clean footage without logos
- **Loop-Friendly**: Can repeat smoothly

### ❌ Reject If
- Low quality or pixelated
- Contains inappropriate content
- Has distracting watermarks/logos
- Too short (< 10 seconds)
- Doesn't match the category
- Static/boring visuals

## 📊 Example Workflow

```bash
# 1. Download gaming videos for preview
python src/cli.py download auto --category gaming --count 3

# 2. Check what was downloaded
python src/cli.py download preview

# 3. Open videos in your video player
open assets/backgrounds_staging/gaming/  # Mac
# or navigate manually to the folder

# 4. After reviewing, approve the good ones
python src/cli.py download approve-all
# or approve individually

# 5. Check final library
python src/cli.py backgrounds list
```

## 🔄 Bulk Operations

### Quick Approve All
If you trust the source (e.g., Pixabay with safe search):
```bash
python src/cli.py download approve-all
```

### Clean Staging Area
Remove all staging videos:
```bash
# On Mac/Linux
rm -rf assets/backgrounds_staging/*

# On Windows
rmdir /s /q assets\backgrounds_staging\*
```

## 💡 Tips

1. **Preview in Batches**: Download 5-10 videos, preview, then approve/reject before downloading more
2. **Use Categories**: Focus on one category at a time for easier organization
3. **Check File Sizes**: Very large files (>100MB) might slow down processing
4. **Test with Videos**: Generate a test video with approved backgrounds to see how they look

## 🎯 Quality Standards

For best results, approve videos that are:
- **Resolution**: 1920x1080 or higher
- **Frame Rate**: 30 FPS or higher  
- **Bitrate**: Medium to high quality
- **Duration**: 30 seconds to 5 minutes
- **Content**: Visually interesting, safe for all audiences

## 🔍 Quick Commands Reference

```bash
# Download to staging
python src/cli.py download auto --category abstract --count 5

# Preview staging
python src/cli.py download preview

# Open staging folder
open assets/backgrounds_staging/              # Mac
explorer assets\backgrounds_staging\          # Windows

# Approve video
python src/cli.py download approve "<path>"

# Approve all
python src/cli.py download approve-all

# Reject video  
python src/cli.py download reject "<path>"

# Check stats
python src/cli.py download stats
```

With this workflow, you have full control over which videos enter your main library!