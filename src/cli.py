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


if __name__ == "__main__":
    cli()