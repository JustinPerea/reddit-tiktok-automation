"""
Command-line interface for testing the content processing engine.
"""

import sys
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from loguru import logger

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from processors.content_processor import ContentProcessor
from generators.hybrid_tts import HybridTTSEngine
from generators.video_generator import VideoGenerator, VideoConfig, VideoFormat, BackgroundType
from utils.logger import setup_logging


console = Console()


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """Reddit-to-TikTok Content Processing CLI."""
    if debug:
        setup_logging("DEBUG")
    else:
        setup_logging("INFO")


@cli.command()
@click.option('--text', '-t', help='Text to process directly')
@click.option('--file', '-f', type=click.Path(exists=True), help='File containing text to process')
@click.option('--url', '-u', help='Source URL for attribution')
def process(text, file, url):
    """Process Reddit content for video generation."""
    
    if not text and not file:
        console.print("[red]Error: Please provide either --text or --file[/red]")
        return
    
    # Get content
    if file:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        console.print(f"[blue]Processing content from file: {file}[/blue]")
    else:
        content = text
        console.print("[blue]Processing provided text...[/blue]")
    
    # Process content
    processor = ContentProcessor()
    
    with console.status("[bold green]Processing content..."):
        result = processor.process(content, url)
    
    if result is None:
        console.print("[red]❌ Content processing failed![/red]")
        
        # Try to get validation details
        validation = processor.validate_content(content)
        if validation.issues:
            console.print("\n[red]Issues found:[/red]")
            for issue in validation.issues:
                console.print(f"  • {issue}")
        
        if validation.recommendations:
            console.print("\n[yellow]Recommendations:[/yellow]")
            for rec in validation.recommendations:
                console.print(f"  • {rec}")
        return
    
    # Display results
    console.print("\n[green]✅ Content processed successfully![/green]")
    
    # Quality metrics table
    table = Table(title="Quality Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")
    
    validation = result.validation
    table.add_row(
        "Quality Score", 
        f"{validation.quality_score:.3f}", 
        "✅ Pass" if validation.quality_score >= 0.7 else "⚠️ Low"
    )
    table.add_row(
        "Word Count", 
        str(validation.word_count), 
        "✅ Optimal" if 200 <= validation.word_count <= 400 else "⚠️ Suboptimal"
    )
    table.add_row(
        "Estimated Duration", 
        f"{result.estimated_duration}s", 
        "✅ Good" if 60 <= result.estimated_duration <= 90 else "⚠️ Check"
    )
    
    console.print(table)
    
    # Metadata table
    meta_table = Table(title="Content Metadata")
    meta_table.add_column("Property", style="cyan")
    meta_table.add_column("Value", style="magenta")
    
    for key, value in result.metadata.items():
        if value is not None:
            meta_table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(meta_table)
    
    # Show processed text
    console.print("\n" + Panel(
        result.tts_optimized_text,
        title="[bold green]TTS-Optimized Text[/bold green]",
        border_style="green"
    ))
    
    # Show recommendations if any
    if validation.recommendations:
        console.print("\n[yellow]💡 Recommendations for improvement:[/yellow]")
        for rec in validation.recommendations:
            console.print(f"  • {rec}")


@cli.command()
def demo():
    """Run a demo with sample Reddit content."""
    sample_content = """
    AITA for refusing to give my sister money for her wedding?
    
    So basically, my sister Sarah (28F) is getting married next month and has been asking everyone in the family for money to help pay for her "dream wedding." The thing is, she's been planning this huge expensive wedding that costs like $50,000 and she and her fiancé only make about $60,000 combined per year.
    
    I (25M) just graduated college and started my first job. I'm making decent money but I'm also paying off student loans and trying to save up to move out of my parents' house. When Sarah asked me for $2,000 to help with the wedding, I told her I couldn't afford it right now.
    
    She completely lost it and started yelling at me, saying I was being selfish and that "family should support each other." She said I was ruining her special day and that I obviously don't care about her happiness. My parents are now pressuring me to give her the money because "it's her wedding and she'll only get married once."
    
    But here's the thing - Sarah has always been terrible with money. She's constantly buying expensive clothes and going on vacations she can't afford, and then asks the family to bail her out. I'm tired of enabling her bad financial decisions.
    
    I told her that if she wanted a cheaper wedding, she could have one, but I'm not going to go into debt to fund her expensive taste. Now half the family is mad at me and saying I'm being an asshole.
    
    AITA for refusing to give my sister money for her wedding?
    
    Edit: Thanks for all the responses. I talked to my parents and they agreed that Sarah needs to learn financial responsibility.
    """
    
    console.print("[bold blue]🎬 Reddit-to-TikTok Content Processing Demo[/bold blue]\n")
    console.print("Processing sample AITA story...\n")
    
    # Process the content
    processor = ContentProcessor()
    
    with console.status("[bold green]Processing content..."):
        result = processor.process(sample_content)
    
    if result:
        console.print("[green]✅ Demo completed successfully![/green]")
        console.print(f"Quality Score: {result.validation.quality_score:.3f}")
        console.print(f"Story Type: {result.metadata['story_type']}")
        console.print(f"Suggested Voice: {result.metadata['suggested_voice']}")
        console.print(f"Estimated Duration: {result.estimated_duration} seconds")
    else:
        console.print("[red]❌ Demo failed - content did not meet quality standards[/red]")


@cli.command()
@click.argument('text')
def analyze(text):
    """Analyze text quality without full processing."""
    processor = ContentProcessor()
    
    console.print(f"[blue]Analyzing text quality...[/blue]\n")
    
    validation = processor.validate_content(text)
    
    # Get detailed quality analysis
    detailed_analysis = processor.quality_scorer.get_detailed_analysis(text)
    
    # Display detailed scores
    table = Table(title="Detailed Quality Analysis")
    table.add_column("Component", style="cyan")
    table.add_column("Score", style="magenta") 
    table.add_column("Weight", style="yellow")
    table.add_column("Contribution", style="green")
    
    weights = {
        "length_score": 0.30,
        "emotional_score": 0.25,
        "structure_score": 0.20,
        "readability_score": 0.15,
        "engagement_score": 0.10
    }
    
    for component, score in detailed_analysis.items():
        if component != "overall_score":
            weight = weights.get(component, 0.0)
            contribution = score * weight
            table.add_row(
                component.replace("_", " ").title(),
                f"{score:.3f}",
                f"{weight:.0%}",
                f"{contribution:.3f}"
            )
    
    table.add_row(
        "[bold]Overall Score[/bold]",
        f"[bold]{detailed_analysis['overall_score']:.3f}[/bold]",
        "[bold]100%[/bold]",
        f"[bold]{detailed_analysis['overall_score']:.3f}[/bold]"
    )
    
    console.print(table)
    
    # Show improvement suggestions
    suggestions = processor.quality_scorer.suggest_improvements(text)
    if suggestions:
        console.print("\n[yellow]💡 Suggestions for improvement:[/yellow]")
        for suggestion in suggestions:
            console.print(f"  • {suggestion}")


@cli.command()
def test_tts():
    """Test the hybrid TTS system with available providers."""
    console.print("[bold blue]🎙️ Testing Hybrid TTS System[/bold blue]\n")
    
    # Initialize TTS engine
    tts_engine = HybridTTSEngine()
    
    # Check available providers
    available_providers = tts_engine.tts_engine.get_available_providers()
    
    if not available_providers:
        console.print("[red]❌ No TTS providers available![/red]")
        console.print("\n[yellow]Install TTS providers:[/yellow]")
        console.print("pip install gtts edge-tts pyttsx3")
        console.print("pip install TTS  # For Coqui TTS")
        return
    
    # Show available providers
    console.print("[green]✅ Available TTS Providers:[/green]")
    for provider in available_providers:
        console.print(f"  • {provider.value}")
    
    # Get setup recommendations
    recommendations = tts_engine.get_recommended_setup()
    
    console.print(f"\n[cyan]📋 Recommendations:[/cyan]")
    console.print(f"Primary: {recommendations['primary_provider']}")
    console.print(f"Fallback: {recommendations['fallback_provider']}")
    console.print(f"Quality Rating: {recommendations['quality_rating']}")
    
    if recommendations['setup_commands']:
        console.print(f"\n[yellow]💡 Install additional providers:[/yellow]")
        for cmd in recommendations['setup_commands']:
            console.print(f"  {cmd}")
    
    # Test synthesis
    test_text = "Hello! This is a test of the Reddit to TikTok automation system. The quality of this voice will determine how engaging our videos will be."
    
    console.print(f"\n[blue]🎵 Testing synthesis with sample text...[/blue]")
    
    # Create fake content analysis for testing
    content_analysis = {
        "quality_score": 0.8,
        "story_type": "aita",
        "word_count": 250,
        "emotional_score": 0.6,
        "dominant_emotion": "neutral"
    }
    
    with console.status("[bold green]Generating speech..."):
        result = tts_engine.synthesize_with_fallback(test_text, content_analysis)
    
    if result.success:
        console.print(f"[green]✅ TTS Success![/green]")
        console.print(f"Provider: {result.provider_used.value}")
        console.print(f"Quality Score: {result.quality_score:.2f}")
        console.print(f"Duration: {result.duration:.1f} seconds")
        console.print(f"Audio File: {result.audio_path}")
        
        if result.metadata:
            console.print("\n[cyan]Metadata:[/cyan]")
            for key, value in result.metadata.items():
                console.print(f"  {key}: {value}")
    else:
        console.print(f"[red]❌ TTS Failed: {result.error_message}[/red]")


@cli.command()
@click.option('--text', '-t', default="This is a test of our TTS system.", help='Text to synthesize')
@click.option('--provider', '-p', help='Specific provider to test (gtts, edge_tts, coqui, pyttsx3)')
def synthesize(text, provider):
    """Synthesize speech from text using the hybrid TTS system."""
    console.print("[bold blue]🎙️ Speech Synthesis[/bold blue]\n")
    
    # Initialize processors
    content_processor = ContentProcessor()
    tts_engine = HybridTTSEngine()
    
    # Process content for analysis
    with console.status("[bold green]Analyzing content..."):
        processed_content = content_processor.process(text)
    
    if not processed_content:
        console.print("[red]❌ Content processing failed![/red]")
        return
    
    # Prepare content analysis
    content_analysis = {
        "quality_score": processed_content.validation.quality_score,
        "story_type": processed_content.metadata.get("story_type", "general"),
        "word_count": processed_content.validation.word_count,
        "emotional_score": 0.6,  # Would come from emotional analyzer
        "dominant_emotion": "neutral"
    }
    
    # Show content analysis
    console.print("[cyan]📊 Content Analysis:[/cyan]")
    console.print(f"Quality Score: {content_analysis['quality_score']:.2f}")
    console.print(f"Story Type: {content_analysis['story_type']}")
    console.print(f"Word Count: {content_analysis['word_count']}")
    
    # Override provider if specified
    if provider:
        from generators.tts_engine import TTSProvider
        provider_map = {
            "gtts": TTSProvider.GTTS,
            "edge_tts": TTSProvider.EDGE_TTS,
            "coqui": TTSProvider.COQUI,
            "pyttsx3": TTSProvider.PYTTSX3
        }
        
        if provider in provider_map:
            # Force specific provider
            strategy = tts_engine.get_strategy_for_content(content_analysis)
            strategy.provider_priorities = [provider_map[provider]]
            console.print(f"[yellow]🎯 Using specified provider: {provider}[/yellow]")
        else:
            console.print(f"[red]❌ Unknown provider: {provider}[/red]")
            return
    
    # Synthesize speech
    with console.status("[bold green]Generating speech..."):
        result = tts_engine.synthesize_with_fallback(
            processed_content.tts_optimized_text, 
            content_analysis
        )
    
    if result.success:
        console.print(f"\n[green]✅ Speech synthesis successful![/green]")
        
        # Results table
        table = Table(title="TTS Results")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Provider Used", result.provider_used.value)
        table.add_row("Quality Score", f"{result.quality_score:.2f}")
        table.add_row("Duration", f"{result.duration:.1f} seconds")
        table.add_row("Audio File", str(result.audio_path))
        
        if result.metadata:
            for key, value in result.metadata.items():
                table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(table)
        
        # Show processed text
        console.print("\n" + Panel(
            processed_content.tts_optimized_text,
            title="[bold green]Synthesized Text[/bold green]",
            border_style="green"
        ))
        
    else:
        console.print(f"[red]❌ Speech synthesis failed: {result.error_message}[/red]")


@cli.command()
@click.option('--text', '-t', help='Text content for video')
@click.option('--audio', '-a', type=click.Path(exists=True), help='Path to audio file')
@click.option('--background', '-b', 
              type=click.Choice(['geometric_patterns', 'minecraft_parkour', 'subway_surfers', 
                               'satisfying_slime', 'cooking_asmr', 'nature_scenes',
                               'slime_mixing', 'kinetic_sand', 'soap_cutting',
                               'rain_window', 'ocean_waves', 'fireplace',
                               'color_gradients', 'particle_effects', 'coffee_brewing']),
              default='geometric_patterns', help='Background style')
@click.option('--format', '-f',
              type=click.Choice(['tiktok', 'instagram_reel', 'youtube_short', 'square']),
              default='tiktok', help='Video format')
@click.option('--output', '-o', type=click.Path(), help='Output video path')
def create_video(text, audio, background, format, output):
    """Generate a complete video from text and audio."""
    console.print("[bold blue]🎬 Video Generation[/bold blue]\n")
    
    if not text and not audio:
        console.print("[red]❌ Please provide either --text or --audio file![/red]")
        return
    
    # Initialize processors
    content_processor = ContentProcessor()
    tts_engine = HybridTTSEngine()
    video_generator = VideoGenerator()
    
    try:
        audio_path = None
        
        if audio:
            # Use provided audio file
            audio_path = Path(audio)
            console.print(f"[blue]Using audio file: {audio_path}[/blue]")
        elif text:
            # Generate audio from text
            console.print(f"[blue]Processing text and generating audio...[/blue]")
            
            with console.status("[bold green]Processing content..."):
                processed_content = content_processor.process(text)
            
            if not processed_content:
                console.print("[red]❌ Content processing failed![/red]")
                return
            
            # Prepare content analysis
            content_analysis = {
                "quality_score": processed_content.validation.quality_score,
                "story_type": processed_content.metadata.get("story_type", "general"),
                "word_count": processed_content.validation.word_count,
                "emotional_score": 0.6,
                "dominant_emotion": "neutral"
            }
            
            with console.status("[bold green]Generating speech..."):
                tts_result = tts_engine.synthesize_with_fallback(
                    processed_content.tts_optimized_text,
                    content_analysis
                )
            
            if not tts_result.success:
                console.print(f"[red]❌ TTS failed: {tts_result.error_message}[/red]")
                return
            
            audio_path = tts_result.audio_path
            text = processed_content.tts_optimized_text
            console.print(f"[green]✅ Audio generated: {audio_path}[/green]")
        
        # Configure video generation - expanded background options
        background_map = {
            'geometric_patterns': BackgroundType.GEOMETRIC_PATTERNS,
            'minecraft_parkour': BackgroundType.MINECRAFT_PARKOUR,
            'subway_surfers': BackgroundType.SUBWAY_SURFERS,
            'satisfying_slime': BackgroundType.SATISFYING_SLIME,
            'cooking_asmr': BackgroundType.COOKING_ASMR,
            'nature_scenes': BackgroundType.NATURE_SCENES,
            # New enhanced backgrounds (map to closest legacy type for compatibility)
            'slime_mixing': BackgroundType.SATISFYING_SLIME,
            'kinetic_sand': BackgroundType.SATISFYING_SLIME,
            'soap_cutting': BackgroundType.SATISFYING_SLIME,
            'rain_window': BackgroundType.NATURE_SCENES,
            'ocean_waves': BackgroundType.NATURE_SCENES,
            'fireplace': BackgroundType.NATURE_SCENES,
            'color_gradients': BackgroundType.GEOMETRIC_PATTERNS,
            'particle_effects': BackgroundType.GEOMETRIC_PATTERNS,
            'coffee_brewing': BackgroundType.COOKING_ASMR
        }
        
        format_map = {
            'tiktok': VideoFormat.TIKTOK,
            'instagram_reel': VideoFormat.INSTAGRAM_REEL,
            'youtube_short': VideoFormat.YOUTUBE_SHORT,
            'square': VideoFormat.SQUARE
        }
        
        config = VideoConfig(
            format=format_map[format],
            background_type=background_map[background]
        )
        
        # Generate video
        console.print(f"[blue]Generating {format} video with {background} background...[/blue]")
        
        output_path = Path(output) if output else None
        
        with console.status("[bold green]Creating video... (this may take a few minutes)"):
            video_result = video_generator.generate_video(
                audio_path=audio_path,
                text=text if text else "Generated Video",
                config=config,
                output_path=output_path
            )
        
        if video_result.success:
            console.print("[green]✅ Video generation successful![/green]")
            
            # Results table
            table = Table(title="Video Generation Results")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Video File", str(video_result.video_path))
            table.add_row("Duration", f"{video_result.duration:.1f} seconds")
            table.add_row("Format", video_result.format.value)
            table.add_row("File Size", f"{video_result.file_size / (1024*1024):.1f} MB")
            
            if video_result.metadata:
                table.add_row("Resolution", f"{video_result.metadata.get('width', 0)}x{video_result.metadata.get('height', 0)}")
                table.add_row("FPS", str(video_result.metadata.get('fps', 0)))
                table.add_row("Video Codec", video_result.metadata.get('video_codec', 'N/A'))
                table.add_row("Audio Codec", video_result.metadata.get('audio_codec', 'N/A'))
            
            console.print(table)
        else:
            console.print(f"[red]❌ Video generation failed: {video_result.error_message}[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--no-reload', is_flag=True, help='Disable auto-reload')
def web(host, port, no_reload):
    """Start the web interface for Reddit-to-TikTok automation."""
    console.print(f"[bold blue]🌐 Starting Web Interface[/bold blue]")
    console.print(f"[green]Access your application at:[/green] [bold]http://{host}:{port}[/bold]")
    console.print("[yellow]Press Ctrl+C to stop the server[/yellow]\n")
    
    try:
        from web_app import run_web_app
        run_web_app(host=host, port=int(port), reload=not no_reload)
    except ImportError:
        console.print("[red]❌ Web app dependencies missing![/red]")
        console.print("Install with: pip install uvicorn fastapi")
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Web server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error starting web server: {e}[/red]")


if __name__ == "__main__":
    cli()