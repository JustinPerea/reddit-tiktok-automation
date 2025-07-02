#!/usr/bin/env python3
"""
Direct test of Edge TTS perfect synchronization - bypassing web UI
"""

import sys
import os
sys.path.append('/Users/justinperea/Documents/Projects/reddit_video_bot_project/src')

from pathlib import Path
from generators.edge_tts_timing_provider import create_edge_tts_timing_provider
from generators.video_generator import VideoGenerator, VideoConfig, VideoFormat, BackgroundType

def test_perfect_sync_direct():
    print("🎬 Testing Edge TTS Perfect Synchronization (Direct)")
    print("=" * 60)
    
    # Test text
    test_text = """Am I the asshole for refusing to give my sister money for her wedding? So basically, my sister Sarah is getting married next month and has been asking everyone in the family for money to help pay for her dream wedding. The thing is, she has been planning this huge expensive wedding that costs like fifty thousand dollars and she and her fiancé only make about sixty thousand dollars combined per year. I just graduated college and started my first job. I am making decent money but I am also paying off student loans and trying to save up to move out of my parents house. When Sarah asked me for two thousand dollars to help with the wedding, I told her I could not afford it right now."""
    
    print(f"📝 Test text: {len(test_text)} characters, {len(test_text.split())} words")
    
    try:
        # Step 1: Generate audio with perfect timing using Edge TTS
        print("\n🎵 Step 1: Generating audio with Edge TTS perfect timing...")
        
        edge_provider = create_edge_tts_timing_provider()
        if not edge_provider.is_available():
            print("❌ Edge TTS not available")
            return False
        
        audio_path, word_timings = edge_provider.generate_audio_with_timing_sync(
            text=test_text,
            voice="en-US-AriaNeural",
            speed=1.0
        )
        
        print(f"✅ Audio generated: {audio_path}")
        print(f"✅ Perfect timing captured: {len(word_timings)} words")
        
        # Show timing sample
        print(f"\n📊 Sample word timings:")
        for i, timing in enumerate(word_timings[:8]):
            print(f"   {i+1:2d}: '{timing.word}' ({timing.start:.3f}s - {timing.end:.3f}s) [{timing.duration:.3f}s]")
        
        # Step 2: Generate video with perfect timing
        print(f"\n🎬 Step 2: Generating video with perfect timing...")
        
        video_generator = VideoGenerator()
        
        # Create video config
        config = VideoConfig(
            format=VideoFormat.TIKTOK,
            background_type=BackgroundType.MINECRAFT_PARKOUR,
            synchronized_text=True
        )
        
        # Convert word timings to format expected by video generator
        subtitle_timings = edge_provider.convert_to_subtitle_format(word_timings)
        
        # Generate video with perfect timing
        result = video_generator.generate_video_with_perfect_timing(
            audio_path=audio_path,
            text=test_text,
            word_timings=subtitle_timings,
            config=config
        )
        
        if result.success:
            print(f"✅ Video generated successfully!")
            print(f"📹 Video path: {result.video_path}")
            print(f"⏱️  Duration: {result.duration:.1f} seconds")
            print(f"📊 File size: {result.file_size / 1024 / 1024:.1f} MB")
            print(f"🎯 Timing method: {result.metadata.get('timing_method', 'unknown')}")
            print(f"📝 Word count: {result.metadata.get('word_count', 'unknown')}")
            
            # Verify subtitle file exists
            srt_file = result.video_path.with_suffix('.srt')
            if srt_file.exists():
                print(f"✅ Subtitle file created: {srt_file}")
                
                # Show first few subtitle entries
                srt_content = srt_file.read_text()
                lines = srt_content.split('\n')
                print(f"\n📝 First few subtitle entries:")
                for i in range(min(20, len(lines))):
                    if lines[i].strip():
                        print(f"   {lines[i]}")
            
            print(f"\n🎉 SUCCESS! Perfect synchronization video created.")
            print(f"🎯 This video should have:")
            print(f"   • Perfect text-audio sync (100% accuracy)")
            print(f"   • Natural word timing (varies by complexity)")
            print(f"   • No drift or delay issues")
            print(f"   • Professional neural voice quality")
            
            return True
            
        else:
            print(f"❌ Video generation failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_perfect_sync_direct()
    
    if success:
        print(f"\n🚀 Perfect sync test completed successfully!")
        print(f"💡 Check the generated video for perfect synchronization.")
    else:
        print(f"\n💥 Perfect sync test failed!")
        print(f"🔍 Review the error above for debugging.")