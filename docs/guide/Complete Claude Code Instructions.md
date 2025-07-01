# Reddit-to-TikTok Automation: Complete Claude Code Instructions

## Project Overview

Build an automated system that converts Reddit stories into viral TikTok videos through manual content curation and automated video production. The system prioritizes legal compliance by avoiding web scraping, instead using manual copy-paste with sophisticated automation for video generation.

**Goal**: Create a system capable of generating $15,000+ monthly revenue through optimized content creation across TikTok, YouTube Shorts, and Instagram Reels.

## Critical Success Factors (Must Implement)

### 1. Voice Strategy (35% Impact on Engagement)
- **Primary Voice**: Use "Jessie" (TikTok's lady voice) - averages 3.2M views and 8.5% engagement
- **Emotional Matching**:
  - Anger content: Increase pace 15-25%, raise pitch on key words (63% better recognition)
  - Sad content: Lower pitch/speed by 20%, extend vowels (40% increase in empathy)
- **Floor-holding**: Lengthen phrase endings ("sooo," "aaand") - improves retention by 35%
- **Technical Requirements**: 77-82% pronunciation accuracy (ElevenLabs preferred at 77.3%)

### 2. Content Selection Criteria
- **Target Subreddits** (by viral conversion rate):
  - r/AmItheAsshole: 15-25% viral conversion
  - r/confession: 18-28% viral conversion
  - r/relationship_advice: High engagement
- **Post Selection**: Target 500-2,000 upvotes (sweet spot for engagement vs competition)
- **Story Requirements**:
  - 800-1,200 words optimal (1-3 minute videos)
  - Clear narrative arc with emotional hook in first 100 words
  - Conflict/resolution framework

### 3. Visual Optimization
- **Background Videos** (by performance):
  - Subway Surfers: 40 seconds average watch time (8x TikTok average)
  - Minecraft parkour: Second best performer
  - Satisfying/cooking videos: Aesthetic alternatives
- **Text Overlay Rules**:
  - Font: TikTok Sans with white text, black outline
  - Size: Minimum 12pt sans serif
  - Length: 10-20 words per block
  - Style: Static text (no animation)

### 4. Platform-Specific Requirements

**TikTok**:
- Resolution: 1080x1920 (9:16)
- Duration: 15 seconds - 10 minutes
- File size: Maximum 287MB
- Format: MP4, MOV
- Hashtags: 3-8 optimal
- Peak times: Tuesday-Thursday, 6-9 AM and 7-11 PM EST

**YouTube Shorts**:
- Resolution: 1080x1920 (9:16)
- Duration: Maximum 60 seconds
- Format: MP4, MOV, AVI, WMV, FLV, WebM
- Title: Must include "#Shorts"
- Peak times: Thursday-Saturday, 2-4 PM and 8-11 PM EST

**Instagram Reels**:
- Resolution: 1080x1920 (9:16)
- Duration: 15-90 seconds optimal
- File size: Maximum 4GB
- Format: MP4, MOV
- Optimal: 7-15 second videos for best completion

## Development Phases

### Phase 1: MVP Manual System (Weeks 1-2) [PRIORITY]

**Core Components to Build**:

1. **Manual Input Interface**
```python
class ContentProcessor:
    def __init__(self):
        self.quality_threshold = 0.7
        self.tts_engine = TTSEngine()
        self.video_generator = VideoGenerator()
    
    def process_manual_input(self, raw_text):
        # Clean Reddit formatting
        cleaned_text = self.clean_reddit_text(raw_text)
        
        # Quality scoring
        quality_score = self.calculate_quality_score(cleaned_text)
        
        if quality_score >= self.quality_threshold:
            # Generate video
            audio = self.tts_engine.generate(cleaned_text)
            video = self.video_generator.create(audio, cleaned_text)
            return video
        
        return None
```

2. **Quality Scoring Algorithm**
```python
def calculate_quality_score(content):
    score = 0.0
    word_count = len(content.split())
    
    # Length optimization (200-400 words ideal)
    if 200 <= word_count <= 400:
        score += 0.3
    elif 150 <= word_count <= 500:
        score += 0.2
    
    # Emotional engagement
    emotional_keywords = ["shocked", "betrayed", "furious", "devastated"]
    emotional_count = sum(1 for word in emotional_keywords if word in content.lower())
    score += min(emotional_count * 0.1, 0.3)
    
    # Story structure
    if has_clear_narrative(content):
        score += 0.2
    
    # TTS friendliness
    if is_tts_friendly(content):
        score += 0.2
    
    return min(score, 1.0)
```

3. **TTS Integration**
```python
class TTSEngine:
    def __init__(self):
        self.provider = "elevenlabs"  # or "openai"
        self.voice_id = "jessie"  # TikTok lady voice
        
    def generate(self, text, emotion="neutral"):
        # Adjust voice parameters based on emotion
        voice_params = self.get_emotion_params(emotion)
        
        # Generate audio with provider
        audio = self.provider.generate_speech(
            text=text,
            voice=self.voice_id,
            **voice_params
        )
        
        return audio
    
    def get_emotion_params(self, emotion):
        params = {
            "anger": {"speed": 1.2, "pitch": 1.1},
            "sadness": {"speed": 0.8, "pitch": 0.9},
            "excitement": {"speed": 1.15, "pitch": 1.05},
            "neutral": {"speed": 1.0, "pitch": 1.0}
        }
        return params.get(emotion, params["neutral"])
```

4. **Video Generation Pipeline**
```python
class VideoGenerator:
    def __init__(self):
        self.background_videos = {
            "anger": ["subway_surfers_1.mp4", "minecraft_parkour_1.mp4"],
            "sadness": ["rain_window.mp4", "ocean_waves.mp4"],
            "excitement": ["satisfying_compilation.mp4", "cooking_asmr.mp4"]
        }
        
    def create(self, audio, text, emotion="neutral"):
        # Select appropriate background
        background = self.select_background(emotion)
        
        # Create text overlays with timing
        overlays = self.create_text_overlays(text, audio.duration)
        
        # Combine all elements
        final_video = self.combine_elements(
            background=background,
            audio=audio,
            overlays=overlays
        )
        
        # Export in TikTok format
        return self.export_tiktok_format(final_video)
```

### Phase 2: Upload Queue & Scheduling (Weeks 3-5)

**Multi-Platform Upload System**:
```python
class UploadScheduler:
    def __init__(self):
        self.platforms = {
            "tiktok": TikTokUploader(),
            "youtube": YouTubeUploader(),
            "instagram": InstagramUploader()
        }
        self.optimal_times = {
            "tiktok": {"days": ["tuesday", "wednesday", "thursday"], 
                      "hours": [(6, 9), (19, 23)]},
            "youtube": {"days": ["thursday", "friday", "saturday"], 
                       "hours": [(14, 16), (20, 23)]},
            "instagram": {"days": ["monday", "tuesday", "wednesday"], 
                         "hours": [(11, 13), (19, 21)]}
        }
    
    def schedule_video(self, video_path, metadata):
        for platform in self.platforms:
            next_slot = self.get_next_optimal_slot(platform)
            self.queue_upload(video_path, platform, next_slot, metadata)
```

### Phase 3: Mobile App (Weeks 6-7)
- React Native app for copy-paste workflow
- Offline queue management
- Direct integration with desktop system

### Phase 4: Browser Extension (Weeks 8-9) [OPTIONAL]
- Chrome extension with "Send to TikTok Bot" button
- Only implement after proving MVP success

## File Structure
```
project/
├── src/
│   ├── content_processor.py    # Reddit text processing
│   ├── tts_engine.py           # Text-to-speech generation
│   ├── video_generator.py      # Video assembly
│   ├── upload_scheduler.py     # Multi-platform uploads
│   └── quality_scorer.py       # Content scoring algorithm
├── assets/
│   ├── backgrounds/            # Categorized background videos
│   │   ├── anger/
│   │   ├── sadness/
│   │   └── excitement/
│   └── fonts/                  # TikTok Sans and alternatives
├── output/
│   ├── scheduled/              # Videos queued for upload
│   │   ├── tiktok/
│   │   ├── youtube_shorts/
│   │   └── instagram_reels/
│   ├── published/              # Completed uploads
│   └── analytics/              # Performance tracking
└── config/
    ├── api_keys.json          # Platform API credentials
    └── settings.json          # User preferences
```

## Critical Implementation Details

### Content Validation Rules
1. **Length**: 150-500 words (60-90 second videos optimal)
2. **Completeness**: Must have beginning, middle, end
3. **Appropriateness**: No explicit content or doxxing
4. **Engagement**: Emotional hooks required
5. **Technical**: No excessive formatting or links

### A/B Testing Framework
```python
class ABTestManager:
    def __init__(self):
        self.test_variants = {
            "hooks": ["question", "preview", "curiosity_gap"],
            "voices": ["jessie", "ghostface", "male_deep"],
            "backgrounds": ["subway_surfers", "minecraft", "satisfying"]
        }
    
    def create_test_batch(self, content):
        variants = []
        for hook in self.test_variants["hooks"][:2]:  # Test 2 hooks
            video = self.generate_variant(content, hook_type=hook)
            variants.append(video)
        return variants
```

### Performance Tracking
- **Key Metrics**:
  - First-hour engagement (predicts viral success)
  - Completion rate (50%+ for short, 5-20% for 1min+)
  - Share-to-view ratio
  - Comment sentiment
- **Platform Analytics**:
  - TikTok: 365-day data window
  - YouTube: 90-day detailed metrics
  - Instagram: 30-day insights

### Legal Compliance
1. **Fair Use Requirements**:
   - Add substantial commentary/analysis
   - Limit Reddit content to necessary portions
   - Maintain transformative intent
   - Never use automated scraping

2. **Platform Compliance**:
   - Label AI-generated content as "synthetic"
   - Follow community guidelines strictly
   - Implement content moderation filters
   - Respect copyright on background content

### Monetization Strategy
1. **Platform Payouts**:
   - TikTok Creator Rewards: $0.40-$1.00 per 1,000 views
   - YouTube Shorts Fund: Variable based on performance
   - Instagram Reels Play: Regional availability

2. **Additional Revenue**:
   - Brand partnerships: $800-7,000+ per post
   - Affiliate marketing: 5.2% engagement rate
   - Product sales: Courses ($200-2,000)
   - Patreon: Exclusive content access

## Error Handling & Edge Cases

```python
class ErrorHandler:
    def handle_upload_failure(self, error, platform):
        if error.type == "rate_limit":
            self.reschedule_upload(delay_hours=1)
        elif error.type == "format_error":
            self.reprocess_video(platform_specs=platform)
        elif error.type == "content_violation":
            self.flag_for_manual_review()
            
    def handle_tts_failure(self, error):
        # Fallback to alternative provider
        if self.primary_provider == "elevenlabs":
            return self.use_openai_tts()
```

## Testing & Validation

1. **Unit Tests Required**:
   - Content scoring accuracy
   - TTS generation consistency
   - Video format compliance
   - Upload scheduling logic

2. **Integration Tests**:
   - End-to-end video generation
   - Multi-platform upload flow
   - Analytics data collection

3. **Performance Benchmarks**:
   - Video generation: <2 minutes
   - Upload processing: <30 seconds per platform
   - Quality score calculation: <100ms

## Success Metrics

### Technical KPIs
- Processing time: <2 minutes per video
- Upload success rate: >95%
- Format compliance: 100%
- System uptime: >99%

### Business KPIs
- Viral rate: 15-25% of videos
- Average views: 100K+ within 48 hours
- Follower growth: 10K+ monthly
- Revenue: $15,000+ monthly by month 6

## Immediate Action Items

1. **Week 1**:
   - Set up ElevenLabs API with Jessie voice
   - Create basic manual input interface
   - Implement quality scoring algorithm
   - Test first 10 videos manually

2. **Week 2**:
   - Add video generation pipeline
   - Implement text overlay system
   - Create output file management
   - Generate 50 test videos

3. **Week 3**:
   - Build upload scheduler
   - Add platform-specific formatting
   - Implement optimal timing logic
   - Begin multi-platform testing

Remember: Start with manual copy-paste to validate the concept before building complex automation. Focus on quality over quantity initially, then scale with proven formulas.