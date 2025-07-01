"""
Core application factory and configuration.
"""

from typing import Dict, Any
from config.settings import Settings


def create_app(settings: Settings) -> Dict[str, Any]:
    """
    Create and configure the application.
    
    Args:
        settings: Application settings
        
    Returns:
        Configured application instance
    """
    app_config = {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "settings": settings
    }
    
    return app_config