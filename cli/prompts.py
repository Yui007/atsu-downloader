"""Interactive prompts for the CLI."""

from typing import List, Optional, Tuple

from rich.prompt import Prompt, IntPrompt, Confirm

from config import get_config, save_config
from models import Chapter, Scanlator


def prompt_scanlator_selection(scanlators: List[Scanlator]) -> Optional[str]:
    """Prompt for scanlator selection.
    
    Returns:
    - ID of the selected scanlator
    - None for "All Scanlators"
    - "cancelled" if user interrupts
    """
    if not scanlators:
        return None
        
    console.print()
    console.print("[bold cyan]Scanlator Filter:[/bold cyan]")
    console.print("  [yellow]0[/yellow]: All Scanlators")
    for i, scan in enumerate(scanlators, 1):
        console.print(f"  [yellow]{i}[/yellow]: {scan.name}")
    console.print()
    
    try:
        choices = ["0"] + [str(i) for i in range(1, len(scanlators) + 1)]
        choice = IntPrompt.ask(
            "[bold cyan]Select scanlator to filter by[/bold cyan]",
            choices=choices,
            default=0
        )
        
        if choice == 0:
            return None
        return scanlators[choice - 1].id
    except KeyboardInterrupt:
        return "cancelled"


from .display import console, display_error, display_success


def prompt_main_menu() -> int:
    """Prompt for main menu selection.
    
    Returns:
        Selected option (1-3)
    """
    while True:
        try:
            choice = Prompt.ask(
                "[bold cyan]Select option[/bold cyan]",
                choices=["1", "2", "3"],
                default="1"
            )
            return int(choice)
        except (ValueError, KeyboardInterrupt):
            return 3  # Exit on interrupt


def prompt_url() -> Optional[str]:
    """Prompt for manga URL.
    
    Returns:
        URL string or None if cancelled
    """
    try:
        url = Prompt.ask(
            "\n[bold cyan]Enter manga URL or ID[/bold cyan]",
            default=""
        )
        if not url.strip():
            display_error("URL cannot be empty")
            return None
        return url.strip()
    except KeyboardInterrupt:
        return None


def prompt_chapter_selection(chapters: List[Chapter]) -> Optional[str]:
    """Prompt for chapter selection.
    
    Examples:
    - "all" or "a": All chapters
    - "5": Single chapter 5
    - "1-10": Chapters 1 through 10  
    - "1,3,5-7": Chapters 1, 3, and 5-7
    
    Returns:
        Selection string or None if cancelled
    """
    console.print()
    console.print("[bold cyan]Chapter Selection Options:[/bold cyan]")
    console.print("  • [yellow]all[/yellow] or [yellow]a[/yellow] - Download all chapters")
    console.print("  • [yellow]5[/yellow] - Download single chapter 5")
    console.print("  • [yellow]1-10[/yellow] - Download chapters 1 through 10")
    console.print("  • [yellow]1,3,5-7[/yellow] - Download chapters 1, 3, and 5-7")
    console.print()
    
    try:
        selection = Prompt.ask(
            "[bold cyan]Enter chapter selection[/bold cyan]",
            default="all"
        )
        return selection.strip() if selection else None
    except KeyboardInterrupt:
        return None


def prompt_settings_menu() -> None:
    """Interactive settings modification menu."""
    config = get_config()
    
    while True:
        from .display import display_settings
        display_settings(config)
        
        try:
            choice = Prompt.ask(
                "\n[bold cyan]Select setting to modify (0 to go back)[/bold cyan]",
                choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
                default="0"
            )
        except KeyboardInterrupt:
            break
        
        if choice == "0":
            break
            
        elif choice == "1":
            # Download Format
            format_choice = Prompt.ask(
                "Select download format",
                choices=["images", "pdf", "cbz"],
                default=config.download_format
            )
            config.download_format = format_choice
            display_success(f"Download format set to: {format_choice.upper()}")
            
        elif choice == "2":
            # Keep Images
            config.keep_images = Confirm.ask(
                "Keep images after PDF/CBZ conversion?",
                default=config.keep_images
            )
            display_success(f"Keep images: {'Yes' if config.keep_images else 'No'}")
            
        elif choice == "3":
            # Download Path
            path = Prompt.ask(
                "Enter download path",
                default=config.download_path
            )
            config.download_path = path
            display_success(f"Download path set to: {path}")
            
        elif choice == "4":
            # Concurrent Chapters
            try:
                value = IntPrompt.ask(
                    "Concurrent chapters (1-10)",
                    default=config.concurrent_chapters
                )
                config.concurrent_chapters = max(1, min(10, value))
                display_success(f"Concurrent chapters set to: {config.concurrent_chapters}")
            except ValueError:
                display_error("Invalid number")
                
        elif choice == "5":
            # Concurrent Images
            try:
                value = IntPrompt.ask(
                    "Concurrent images (1-20)",
                    default=config.concurrent_images
                )
                config.concurrent_images = max(1, min(20, value))
                display_success(f"Concurrent images set to: {config.concurrent_images}")
            except ValueError:
                display_error("Invalid number")
                
        elif choice == "6":
            # Max Display Chapters
            try:
                value = IntPrompt.ask(
                    "Max chapters to display (0 = All)",
                    default=config.max_display_chapters
                )
                config.max_display_chapters = max(0, value)
                display_success(f"Max display chapters: {'All' if value == 0 else value}")
            except ValueError:
                display_error("Invalid number")
                
        elif choice == "7":
            # Max Retries
            try:
                value = IntPrompt.ask(
                    "Max retries (1-10)",
                    default=config.max_retries
                )
                config.max_retries = max(1, min(10, value))
                display_success(f"Max retries set to: {config.max_retries}")
            except ValueError:
                display_error("Invalid number")
                
        elif choice == "8":
            # Retry Delay
            try:
                value = IntPrompt.ask(
                    "Base retry delay in seconds (1-30)",
                    default=config.retry_delay
                )
                config.retry_delay = max(1, min(30, value))
                display_success(f"Retry delay set to: {config.retry_delay}s")
            except ValueError:
                display_error("Invalid number")
                
        elif choice == "9":
            # Enable Logs
            config.enable_logs = Confirm.ask(
                "Enable detailed logging?",
                default=config.enable_logs
            )
            display_success(f"Logging: {'Enabled' if config.enable_logs else 'Disabled'}")
        
        # Save after each change
        save_config()


def confirm_download(chapter_count: int) -> bool:
    """Confirm download of selected chapters.
    
    Args:
        chapter_count: Number of chapters to download
        
    Returns:
        True if confirmed, False otherwise
    """
    try:
        return Confirm.ask(
            f"\n[bold cyan]Download {chapter_count} chapter(s)?[/bold cyan]",
            default=True
        )
    except KeyboardInterrupt:
        return False
