# Reddit-to-TikTok Automation System

A comprehensive system for converting Reddit stories into TikTok-ready videos through manual content curation and automated video production.

## 🎯 Project Overview

This system enables content creators to efficiently transform Reddit stories into engaging TikTok videos while maintaining legal compliance and quality control. The project uses manual content selection combined with automated video generation to create compelling short-form content.

## ✨ Key Features

- **Manual Content Input**: Copy-paste Reddit stories with intelligent formatting detection
- **Automated Video Generation**: Text-to-speech, background videos, and text overlays
- **Multi-Platform Support**: TikTok, YouTube Shorts, and Instagram Reels optimization
- **Quality Scoring**: AI-powered content validation and viral potential assessment
- **Upload Scheduling**: Optimal timing algorithms for maximum engagement
- **Legal Compliance**: No automated scraping, proper attribution, and platform compliance

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/reddit-tiktok-automation.git
cd reddit-tiktok-automation

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
python src/main.py

# Test the content processing engine
PYTHONPATH=. python src/cli.py demo
PYTHONPATH=. python src/cli.py analyze "Your Reddit story here..."

# Run tests
PYTHONPATH=. python -m pytest tests/unit/ -v
```

## 📁 Project Structure

```
reddit-tiktok-automation/
├── src/                    # Source code
├── tests/                  # Test files
├── docs/                   # Documentation
├── assets/                 # Static assets
├── output/                 # Generated videos
├── config/                 # Configuration files
├── scripts/                # Utility scripts
└── requirements.txt        # Python dependencies
```

## 🛠 Technology Stack

- **Backend**: Python 3.8+, FastAPI
- **Video Processing**: FFmpeg, MoviePy
- **Text-to-Speech**: OpenAI TTS, ElevenLabs
- **AI/ML**: Transformers, BERT
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Electron (desktop), React Native (mobile)

## 📋 Development Phases

### Phase 1: MVP Manual System (Weeks 1-3) - 🚧 IN PROGRESS
- [x] Project setup and core infrastructure
- [x] Content processing engine with quality scoring
- [x] Reddit formatting and TTS optimization
- [x] CLI interface and comprehensive testing
- [ ] TTS integration (OpenAI/ElevenLabs)
- [ ] Basic video generation pipeline

### Phase 2: Enhanced Interface (Weeks 4-7)
- [ ] Multi-platform optimization
- [ ] Upload queue and scheduling
- [ ] Desktop GUI application
- [ ] Analytics integration

### Phase 3: Mobile Integration (Weeks 8-9)
- [ ] Cross-platform mobile app
- [ ] Offline content management
- [ ] Sync capabilities

### Phase 4: Browser Extension (Weeks 10-11)
- [ ] Chrome extension
- [ ] Reddit integration
- [ ] Content extraction

## 🔧 Configuration

The system uses environment variables for configuration:

```env
# API Keys
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Platform APIs
TIKTOK_API_KEY=your_tiktok_key
YOUTUBE_API_KEY=your_youtube_key
INSTAGRAM_API_KEY=your_instagram_key

# Processing Settings
DEFAULT_TTS_PROVIDER=openai
VIDEO_OUTPUT_FORMAT=mp4
QUALITY_THRESHOLD=0.7
```

## 🧠 Content Processing Engine

Our AI-powered content processing engine analyzes Reddit stories for viral potential:

### Quality Scoring Algorithm (0.0-1.0)
- **Length Optimization** (30%): 200-400 words optimal for 60-90 second videos
- **Emotional Engagement** (25%): Detects anger, surprise, joy for maximum engagement
- **Story Structure** (20%): Validates narrative arc (setup, conflict, resolution)
- **Readability** (15%): Optimizes for text-to-speech and mobile consumption
- **Engagement Hooks** (10%): Identifies viral patterns and audience interaction triggers

### Reddit-Specific Optimization
- **Abbreviation Expansion**: AITA → "Am I the jerk", TL;DR → "Too long, didn't read"
- **Format Cleanup**: Removes edits, updates, meta content, and Reddit markup
- **TTS Enhancement**: Expands contractions, adds natural pauses, fixes pronunciations
- **Story Classification**: Auto-detects AITA, relationship, workplace, family, TIFU content

### CLI Testing Interface
```bash
# Analyze content quality
PYTHONPATH=. python src/cli.py analyze "Your story here..."

# Run full processing demo
PYTHONPATH=. python src/cli.py demo

# Process custom content
PYTHONPATH=. python src/cli.py process --text "Your Reddit story" --url "source_url"
```

## 📊 Success Metrics

- Content processing time: <2 minutes per video
- Upload success rate: >95% across all platforms
- Video approval rate: >90% of generated content
- System uptime: >99% availability
- **Quality prediction accuracy: 80%+ viral potential detection**

## ⚖️ Legal Compliance

- Manual content selection (no automated Reddit scraping)
- Proper attribution and source crediting
- Platform-specific content labeling
- GDPR and privacy compliance
- Fair use and transformative content guidelines

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Reddit community for inspiring content
- OpenAI and ElevenLabs for TTS services
- FFmpeg community for video processing tools
- Platform APIs for distribution capabilities

## 📞 Support

For questions and support, please open an issue on GitHub or contact the development team.

---

**Note**: This project is designed for educational and legitimate content creation purposes. Users are responsible for ensuring compliance with all applicable laws and platform terms of service.