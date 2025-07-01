# Audio-Video Synchronization Strategy

## Overview

This document outlines our pivot from basic audio analysis to professional-grade forced alignment for achieving TikTok-quality word-by-word subtitle synchronization.

## Problem Analysis

### Current Implementation Issues
1. **Text Content Mismatch**
   - TTS audio uses processed text: "(28F)" → "28 female"
   - Subtitles display original text: "(28F)"
   - Result: Audio says different words than subtitles show

2. **Timing Imprecision**
   - Current approach: ~0.4 seconds average per word
   - Real speech: Variable word durations (0.1s - 1.2s)
   - Cumulative drift over 60-120 second videos

3. **Artificial Segmentation**
   - Forcing 267 words into 55-105 detected audio segments
   - Multiple words per segment causing batch reveals
   - Not true word-by-word synchronization

## Research-Based Solution

### WhisperX Forced Alignment
**Selected Tool**: WhisperX (OpenAI Whisper + wav2vec2 alignment)

**Key Benefits**:
- 95% accuracy on clean audio
- <100ms timing precision
- 70x real-time processing speed
- Free and self-hosted
- GPU acceleration support

### Implementation Architecture

#### Phase 1: WhisperX Integration
```python
# New module: src/generators/whisperx_aligner.py
class WhisperXAligner:
    def __init__(self):
        self.model = None
        self.align_model = None
    
    def get_word_level_timestamps(self, audio_path: Path, expected_text: str):
        """Extract precise word timing from actual TTS audio"""
        # Load audio and transcribe
        audio = whisperx.load_audio(str(audio_path))
        result = self.model.transcribe(audio)
        
        # Force align for word-level precision
        result = whisperx.align(
            result["segments"], 
            self.align_model, 
            self.metadata, 
            audio, 
            device="cuda"
        )
        
        return self.extract_word_timings(result)
```

#### Phase 2: Bidirectional Text Normalization
```python
# Enhanced: src/processors/text_normalizer.py
class BidirectionalTextNormalizer:
    def process_for_sync(self, original_text: str):
        """Create mappings between original and TTS-optimized text"""
        return {
            'original_text': original_text,           # For subtitles
            'tts_text': self.normalize_for_tts(original_text),  # For audio
            'word_mappings': self.create_alignment_map(original_text)
        }
    
    def normalize_for_tts(self, text: str):
        """Apply TTS-friendly transformations"""
        # Context-aware normalization
        if "(28F)" in text and self.detect_age_context(text):
            return text.replace("(28F)", "28 female")
        return text
```

#### Phase 3: VidGear Performance Optimization
```python
# New module: src/generators/vidgear_renderer.py
from vidgear.gears import VideoGear, WriteGear

class OptimizedVideoRenderer:
    def render_word_reveals(self, word_timings, background_video):
        """3-4x faster than current FFmpeg subprocess approach"""
        # Pre-calculate frame-to-word mapping
        word_timeline = {}
        for word, start_time, end_time in word_timings:
            start_frame = int(start_time * 30)  # 30fps
            end_frame = int(end_time * 30)
            for frame_num in range(start_frame, end_frame + 1):
                word_timeline[frame_num] = word.upper()
        
        # Process video frame-by-frame with word overlays
        stream = VideoGear(source=background_video).start()
        writer = WriteGear(output="final_video.mp4")
        
        frame_count = 0
        while True:
            frame = stream.read()
            if frame is None:
                break
            
            # Add current word overlay
            if frame_count in word_timeline:
                frame = self.add_word_overlay(frame, word_timeline[frame_count])
            
            writer.write(frame)
            frame_count += 1
```

## Expected Performance Improvements

### Accuracy
- **Current**: ~0.4s average timing, cumulative drift
- **Target**: <100ms precision, no drift

### Processing Speed
- **Current**: FFmpeg subprocess approach
- **Target**: 3-4x faster with VidGear

### Synchronization Quality
- **Current**: Multiple words per timing segment
- **Target**: Individual word reveals with frame-perfect timing

## Implementation Timeline

### Week 1: Core Foundation
- [ ] Install WhisperX dependencies
- [ ] Create WhisperXAligner module
- [ ] Replace current audio analysis method
- [ ] Test basic word-level timing extraction

### Week 2: Text Normalization
- [ ] Implement bidirectional text mapping
- [ ] Fix "(28F)" vs "28 female" mismatch
- [ ] Create context-aware normalization rules
- [ ] Test TTS-subtitle synchronization

### Week 3: Performance Optimization
- [ ] Integrate VidGear for video processing
- [ ] Implement frame-accurate word reveals
- [ ] Benchmark performance improvements
- [ ] Optimize for production use

### Week 4: Quality Assurance
- [ ] Comprehensive testing with various content types
- [ ] Performance benchmarking
- [ ] Documentation updates
- [ ] Prepare for production deployment

## Success Metrics

1. **Timing Accuracy**: <100ms deviation from actual speech
2. **Text Matching**: 100% correspondence between audio and subtitle content
3. **Processing Speed**: 3-4x improvement over current approach
4. **Quality Score**: >95% word alignment confidence from WhisperX
5. **User Experience**: TikTok-quality word-by-word reveals

## Risk Mitigation

### GPU Requirements
- **Risk**: WhisperX optimal performance requires GPU
- **Mitigation**: Implement CPU fallback mode for development/testing

### Model Download Size
- **Risk**: WhisperX models are large (1-3GB)
- **Mitigation**: Download once, cache locally, provide size warnings

### Processing Time
- **Risk**: Initial model loading may be slow
- **Mitigation**: Model warming, persistent loading for batch processing

## Conclusion

This research-backed approach addresses the root causes of our synchronization issues:
- Precise timing through forced alignment
- Text consistency through bidirectional normalization  
- Performance optimization through modern video processing libraries

The result will be professional-quality word-by-word subtitle synchronization suitable for viral TikTok content.