"""Typer CLI application for Atsu Downloader."""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer

from config import get_config, save_config
from scraper import MangaScraper
from downloader import DownloadManager
from downloader.manager import parse_chapter_selection

from .display import (
    console,
    display_banner,
    display_main_menu,
    display_manga_info,
    display_chapters,
    display_success,
    display_error,
    display_info,
    display_warning,
    create_download_progress,
    display_download_results,
)
from .prompts import (
    prompt_main_menu,
    prompt_url,
    prompt_chapter_selection,
    prompt_settings_menu,
    confirm_download,
    prompt_scanlator_selection,
)

# Create Typer app
app = typer.Typer(
    name="atsu",
    help="Download manga from atsu.moe with style",
    add_completion=False,
)


def setup_logging() -> None:
    """Configure logging based on settings."""
    config = get_config()
    
    if config.enable_logs:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        # Disable all logging
        logging.basicConfig(level=logging.CRITICAL)
        logging.disable(logging.CRITICAL)


def download_manga(url: str) -> None:
    """Handle the download manga flow."""
    config = get_config()
    
    # Fetch manga info
    display_info("Fetching manga information...")
    
    with MangaScraper() as scraper:
        manga = scraper.fetch_manga(url)
    
    if not manga:
        display_error("Failed to fetch manga. Please check the URL and try again.")
        return
    
    # Display manga info
    display_manga_info(manga)
    
    # Filter by scanlator if multiple choices
    filtered_chapters = manga.chapters
    if len(manga.scanlators) > 1:
        scan_id = prompt_scanlator_selection(manga.scanlators)
        if scan_id == "cancelled":
            display_warning("Download cancelled")
            return
        if scan_id:
            filtered_chapters = [c for c in manga.chapters if c.scanlation_manga_id == scan_id]
            display_info(f"Filtered to [yellow]{len(filtered_chapters)}[/yellow] chapters from selected scanlator")

    # Display chapters (already in descending order if we reverse them)
    # We reverse them here so display_chapters and prompt_chapter_selection use the same order.
    filtered_chapters.reverse()
    
    display_chapters(filtered_chapters, limit=config.max_display_chapters)
    
    # Get chapter selection
    selection = prompt_chapter_selection(filtered_chapters)

    if not selection:
        display_warning("Download cancelled")
        return
    
    # Parse selection
    indices = parse_chapter_selection(selection, len(filtered_chapters))
    if not indices:
        display_error("Invalid chapter selection")
        return
    
    display_info(f"Selected {len(indices)} chapter(s)")
    
    # Confirm download
    if not confirm_download(len(indices)):
        display_warning("Download cancelled")
        return
    
    # Start download with progress
    successful = 0
    failed = 0
    
    with create_download_progress() as progress:
        # Main task for chapters
        chapter_task = progress.add_task(
            "[cyan]Downloading chapters concurrently...",
            total=len(indices)
        )
        
        with DownloadManager() as manager:
            # We need to map filtered indices back to original indices IF download_chapters expects manga.chapters indices.
            # However, looking at the code, it's safer to just provide a list of chapters sometimes, but let's see.
            # Actually, manager.download_chapters(manga, indices) uses manga.chapters[idx].
            # So we SHOULD handle the mapping.
            
            original_indices = []
            for idx in indices:
                chapter = filtered_chapters[idx]
                # Find index in original manga.chapters
                for i, c in enumerate(manga.chapters):
                    if c.id == chapter.id:
                        original_indices.append(i)
                        break
            
            # Use concurrent download
            results = manager.download_chapters(manga, original_indices)

            
            for result in results:
                if result.success:
                    successful += 1
                else:
                    failed += 1
                progress.advance(chapter_task)
        
        progress.update(chapter_task, description="[green]Download complete!")
    
    # Display results
    output_path = str(Path(config.download_path) / manga.title)
    display_download_results(successful, failed, output_path)


def interactive_mode() -> None:
    """Run the interactive CLI mode."""
    setup_logging()
    
    while True:
        console.clear()
        display_banner()
        display_main_menu()
        
        choice = prompt_main_menu()
        
        if choice == 1:
            # Download Manga
            url = prompt_url()
            if url:
                try:
                    download_manga(url)
                except KeyboardInterrupt:
                    display_warning("\nDownload interrupted")
                except Exception as e:
                    display_error(f"Error: {e}")
            
            # Wait for user to see results
            console.print()
            typer.prompt("Press Enter to continue", default="", show_default=False)
            
        elif choice == 2:
            # Settings
            prompt_settings_menu()
            
        elif choice == 3:
            # Exit
            console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]\n")
            break


@app.command()
def main(
    url: Optional[str] = typer.Argument(
        None,
        help="Manga URL or ID to download"
    ),
    chapters: Optional[str] = typer.Option(
        None,
        "--chapters", "-c",
        help="Chapter selection (e.g., 'all', '1-10', '1,3,5')"
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format", "-f",
        help="Download format (images, pdf, cbz)"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory path"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable detailed logging"
    ),
) -> None:
    """
    Atsu Downloader - Download manga from atsu.moe
    
    Run without arguments for interactive mode, or provide URL for direct download.
    """
    config = get_config()
    
    # Apply command-line options
    if verbose:
        config.enable_logs = True
        save_config()
    
    if format and format in ("images", "pdf", "cbz"):
        config.download_format = format
        save_config()
    
    if output:
        config.download_path = output
        save_config()
    
    setup_logging()
    
    if url:
        # Direct download mode
        display_banner()
        
        if chapters:
            # Non-interactive download
            display_info(f"Downloading from: {url}")
            
            with MangaScraper() as scraper:
                manga = scraper.fetch_manga(url)
            
            if not manga:
                display_error("Failed to fetch manga")
                raise typer.Exit(1)
            
            # Reverse chapters for consistent display/selection
            manga.chapters.reverse()
            display_manga_info(manga)
            
            indices = parse_chapter_selection(chapters, len(manga.chapters))
            if not indices:
                display_error("Invalid chapter selection")
                raise typer.Exit(1)
            
            display_info(f"Downloading {len(indices)} chapter(s)...")
            
            successful = 0
            failed = 0
            
            with create_download_progress() as progress:
                task = progress.add_task("Downloading...", total=len(indices))
                
                with DownloadManager() as manager:
                    results = manager.download_chapters(manga, indices)
                    
                    for result in results:
                        if result.success:
                            successful += 1
                        else:
                            failed += 1
                        progress.advance(task)
            
            output_path = str(Path(config.download_path) / manga.title)
            display_download_results(successful, failed, output_path)
        else:
            # URL provided but no chapters - show info and prompt
            download_manga(url)
    else:
        # Interactive mode
        try:
            interactive_mode()
        except KeyboardInterrupt:
            console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]\n")


if __name__ == "__main__":
    app()
