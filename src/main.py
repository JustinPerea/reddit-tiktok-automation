"""
Main entry point for the Reddit-to-TikTok Automation System.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from core.app import create_app
from utils.logger import setup_logging
from config.settings import get_settings


async def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    
    # Load settings
    settings = get_settings()
    
    # Create and run the application
    app = create_app(settings)
    
    print(f"🚀 Reddit-to-TikTok Automation System v{settings.VERSION}")
    print(f"📝 Starting in {settings.ENVIRONMENT} mode")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    
    # For now, just print startup message
    # In Phase 1, this will be a CLI interface
    # In Phase 2, this will launch the FastAPI server
    print("✅ System ready for Phase 1 development")


if __name__ == "__main__":
    asyncio.run(main())