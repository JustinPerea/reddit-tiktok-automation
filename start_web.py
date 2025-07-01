#!/usr/bin/env python3
"""
Simple launcher script for the Reddit-to-TikTok web interface.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    from src.web_app import run_web_app
    
    print("🎬 Reddit-to-TikTok Automation System")
    print("=" * 50)
    print("🌐 Starting web interface...")
    print("📱 Access at: http://127.0.0.1:8000")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        run_web_app(host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n👋 Web server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)