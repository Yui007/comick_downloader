# cli/main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import typer
from rich.console import Console
from rich.prompt import Prompt
from core.scraper import ComickScraper
from core.downloader import Downloader
from core.config import DEFAULT_OUTPUT_DIR
from utils.sanitizer import sanitize_filename
import re
import os

app = typer.Typer()
console = Console()

def get_comic_slug(url: str) -> str:
    """Extracts the comic slug from the URL for the output directory name."""
    match = re.search(r'/comic/([^/]+)', url)
    return match.group(1) if match else "manga"

def parse_chapter_selection(selection: str, max_chapters: int) -> list[int]:
    """Parses a chapter selection string (e.g., '1,3-5,all')."""
    if selection.lower() == 'all':
        return list(range(1, max_chapters + 1))
    
    indices = set()
    parts = selection.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            indices.update(range(start, end + 1))
        else:
            indices.add(int(part))
    return sorted(list(indices))

def download_from_url(url: str, output: str | None, chapters_str: str | None):
    """Handles the logic for downloading from a given URL."""
    # Remove URL fragment if it exists
    url = url.split('#')[0]
    console.print("[bold cyan]MangaScraper for Comick.io[/bold cyan]")
    
    scraper = ComickScraper()
    downloader = Downloader()
    
    slug = get_comic_slug(url)
    sanitized_slug = sanitize_filename(slug)
    base_output_dir = output if output else os.path.join(DEFAULT_OUTPUT_DIR, sanitized_slug)

    if "/comic/" in url and "chapter" in url:
        # Single chapter URL
        console.print(f"📖 Downloading single chapter: [green]{url}[/green]")
        image_urls, user_agent = scraper.fetch_image_urls(url)
        if image_urls:
            chapter_title_match = re.search(r'chapter-([^/]+)', url)
            chapter_title = chapter_title_match.group(1) if chapter_title_match else "chapter"
            chapter_output_dir = os.path.join(base_output_dir, chapter_title)
            downloader.download_images(image_urls, chapter_output_dir, user_agent, url)
        else:
            console.print("[bold red]Could not find any images to download.[/bold red]")
    else:
        # Manga URL, fetch chapter list
        chapters = scraper.fetch_chapter_list(url)
        if not chapters:
            console.print("[bold red]Could not fetch chapter list. Exiting.[/bold red]")
            return

        console.print(f"[bold yellow]Found {len(chapters)} chapters:[/bold yellow]")
        for i, chap in enumerate(chapters, 1):
            console.print(f"{i}: {chap['title']}")

        if not chapters_str:
            selection = Prompt.ask("\nWhich chapters do you want to download? (e.g., '1,3-5', 'all')")
        else:
            selection = chapters_str
            
        selected_indices = parse_chapter_selection(selection, len(chapters))
        
        for i in selected_indices:
            if 1 <= i <= len(chapters):
                chap = chapters[i-1]
                console.print(f"\n[bold cyan]Downloading Chapter {i}: {chap['title']}[/bold cyan]")
                image_urls, user_agent = scraper.fetch_image_urls(chap['url'])
                if image_urls:
                    sanitized_title = sanitize_filename(chap['title'])
                    chapter_output_dir = os.path.join(base_output_dir, sanitized_title)
                    downloader.download_images(image_urls, chapter_output_dir, user_agent, chap['url'])
                else:
                    console.print(f"[bold red]Could not find any images for Chapter {i}.[/bold red]")

    console.print("\n[bold green]✅ All selected chapters downloaded![/bold green]")

def main_menu():
    """Displays the main menu and handles user choices."""
    scraper = ComickScraper()
    while True:
        console.print("\n[bold yellow]Select an option:[/bold yellow]")
        console.print("1: Download from Manga URL")
        console.print("2: Search for a Manga")
        console.print("3: Exit")
        
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3"], default="1")

        if choice == "1":
            url = Prompt.ask("Enter the Manga or Chapter URL")
            output = Prompt.ask("Enter the output directory (optional, press Enter for default)")
            download_from_url(url, output or None, None)
        elif choice == "2":
            query = Prompt.ask("Enter the name of the manga to search for")
            results = scraper.search_manga(query)
            if not results:
                console.print("[bold red]No results found.[/bold red]")
                continue
            
            console.print("\n[bold yellow]Search Results:[/bold yellow]")
            for i, res in enumerate(results, 1):
                console.print(f"{i}: {res['title']}")
            
            selection = Prompt.ask("\nSelect a manga to download (enter the number)")
            try:
                selected_index = int(selection) - 1
                if 0 <= selected_index < len(results):
                    selected_manga = results[selected_index]
                    download_from_url(selected_manga['url'], None, None)
                else:
                    console.print("[bold red]Invalid selection.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number.[/bold red]")
        elif choice == "3":
            break

@app.command()
def main(
    url: str = typer.Argument(None, help="The URL of the Comick.io manga or chapter."),
    output: str = typer.Option(None, "--output", "-o", help=f"The base directory to save the downloaded chapters."),
    chapters: str = typer.Option(None, "--chapters", "-c", help="A string specifying chapters to download (e.g., '1,3-5', 'all').")
):
    """
    Downloads manga chapters from Comick.io.
    Run without arguments for an interactive menu.
    """
    if url:
        download_from_url(url, output, chapters)
    else:
        main_menu()

if __name__ == "__main__":
    app()
