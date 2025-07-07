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
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn, MofNCompleteColumn

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

def _download_single_chapter_task(scraper: ComickScraper, downloader: Downloader, chap: dict, base_output_dir: str, chapter_index: int, convert_to_pdf: bool, delete_images_after_pdf: bool, progress: Progress, chapter_task_id):
    """Task for downloading a single chapter, to be used with ThreadPoolExecutor."""
    try:
        progress.console.print(f"\n[bold cyan]Downloading Chapter {chapter_index}: {chap['title']}[/bold cyan]")
        image_urls, user_agent = scraper.fetch_image_urls(chap['url'])
        if image_urls:
            sanitized_title = sanitize_filename(chap['title'])
            chapter_output_dir = os.path.join(base_output_dir, sanitized_title)
            downloader.download_images(image_urls, chapter_output_dir, user_agent, chap['url'])
            
            if convert_to_pdf:
                pdf_output_path = os.path.join(base_output_dir, f"{sanitized_title}.pdf")
                downloader.convert_to_pdf(chapter_output_dir, pdf_output_path)
                if delete_images_after_pdf:
                    downloader.delete_images(chapter_output_dir)
                    try:
                        os.rmdir(chapter_output_dir) # Attempt to remove empty directory
                        progress.console.print(f"🗑️ Removed empty chapter directory: {chapter_output_dir}")
                    except OSError:
                        pass # Directory might not be empty if non-image files exist
        else:
            progress.console.print(f"[bold red]Could not find any images for Chapter {chapter_index}.[/bold red]")
    except Exception as e:
        progress.console.print(f"[bold red]An unexpected error occurred while processing Chapter {chapter_index} ({chap['title']}): {e}[/bold red]")
        progress.console.print(f"[bold red]Traceback:[/bold red]\n{traceback.format_exc()}")
        raise # Re-raise to be caught by as_completed
    finally:
        progress.update(chapter_task_id, advance=1) # Ensure chapter task advances even on error

def download_from_url(url: str, output: str | None, chapters_str: str | None, convert_to_pdf: bool, delete_images_after_pdf: bool):
    """Handles the logic for downloading from a given URL."""
    # Remove URL fragment if it exists
    url = url.split('#')[0]
    console.print("[bold cyan]MangaScraper for Comick.io[/bold cyan]")
    
    scraper = ComickScraper()
    downloader = Downloader()
    
    slug = get_comic_slug(url)
    sanitized_slug = sanitize_filename(slug)
    base_output_dir = output if output else os.path.join(DEFAULT_OUTPUT_DIR, sanitized_slug)

    chapters_to_download = []
    if "/comic/" in url and "chapter" in url:
        # Single chapter URL
        console.print(f"📖 Downloading single chapter: [green]{url}[/green]")
        image_urls, user_agent = scraper.fetch_image_urls(url)
        if image_urls:
            chapter_title_match = re.search(r'chapter-([^/]+)', url)
            chapter_title = chapter_title_match.group(1) if chapter_title_match else "chapter"
            chapter_output_dir = os.path.join(base_output_dir, chapter_title)
            downloader.download_images(image_urls, chapter_output_dir, user_agent, url)

            if convert_to_pdf:
                pdf_output_path = os.path.join(base_output_dir, f"{sanitize_filename(chapter_title)}.pdf")
                downloader.convert_to_pdf(chapter_output_dir, pdf_output_path)
                if delete_images_after_pdf:
                    downloader.delete_images(chapter_output_dir)
                    try:
                        os.rmdir(chapter_output_dir)
                        console.print(f"🗑️ Removed empty chapter directory: {chapter_output_dir}")
                    except OSError:
                        pass
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
                chapters_to_download.append(chapters[i-1])
        
        if not chapters_to_download:
            console.print("[bold red]No chapters selected for download. Exiting.[/bold red]")
            return

        with Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            "•",
            TimeRemainingColumn(),
            console=console # Use the shared console
        ) as progress:
            main_chapter_task = progress.add_task("[bold green]Overall Chapter Progress", total=len(chapters_to_download))

            with ThreadPoolExecutor(max_workers=10) as executor: # Threading for chapters
                futures = []
                for chap in chapters_to_download:
                    # Pass the chapter index for logging purposes, not for direct list access
                    chapter_index = chapters.index(chap) + 1 
                    futures.append(executor.submit(_download_single_chapter_task, scraper, downloader, chap, base_output_dir, chapter_index, convert_to_pdf, delete_images_after_pdf, progress, main_chapter_task))
                
                for future in as_completed(futures):
                    try:
                        future.result() # This will re-raise any exception that occurred in the thread
                    except Exception as e:
                        progress.console.print(f"[bold red]A chapter download task failed: {e}[/bold red]")
                        progress.console.print(f"[bold red]Traceback:[/bold red]\n{traceback.format_exc()}")


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
            convert_pdf = Prompt.ask("Convert to PDF? (y/n)", choices=["y", "n"], default="n").lower() == 'y'
            delete_imgs = False
            if convert_pdf:
                delete_imgs = Prompt.ask("Delete images after PDF conversion? (y/n)", choices=["y", "n"], default="n").lower() == 'y'
            download_from_url(url, output or None, None, convert_pdf, delete_imgs)
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
                    convert_pdf = Prompt.ask("Convert to PDF? (y/n)", choices=["y", "n"], default="n").lower() == 'y'
                    delete_imgs = False
                    if convert_pdf:
                        delete_imgs = Prompt.ask("Delete images after PDF conversion? (y/n)", choices=["y", "n"], default="n").lower() == 'y'
                    download_from_url(selected_manga['url'], None, None, convert_pdf, delete_imgs)
                else:
                    console.print("[bold red]Invalid selection.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number.[/bold red]")
        elif choice == "3":
            break

@app.command()
def search(
    query: str = typer.Argument(..., help="The search query for the manga."),
    output: str = typer.Option(None, "--output", "-o", help="The base directory to save the downloaded chapters."),
    chapters: str = typer.Option(None, "--chapters", "-c", help="A string specifying chapters to download (e.g., '1,3-5', 'all')."),
    pdf: bool = typer.Option(False, "--pdf", "-p", help="Convert downloaded images to PDF."),
    delete_images_after_pdf: bool = typer.Option(False, "--delete-images", "-d", help="Delete images after PDF conversion.")
):
    """
    Searches for a manga and downloads selected chapters.
    """
    scraper = ComickScraper()
    results = scraper.search_manga(query)
    if not results:
        console.print("[bold red]No results found.[/bold red]")
        return

    console.print("\n[bold yellow]Search Results:[/bold yellow]")
    for i, res in enumerate(results, 1):
        console.print(f"{i}: {res['title']}")

    selection = Prompt.ask("\nSelect a manga to download (enter the number)")
    try:
        selected_index = int(selection) - 1
        if 0 <= selected_index < len(results):
            selected_manga = results[selected_index]
            download_from_url(selected_manga['url'], output, chapters, pdf, delete_images_after_pdf)
        else:
            console.print("[bold red]Invalid selection.[/bold red]")
    except ValueError:
        console.print("[bold red]Invalid input. Please enter a number.[/bold red]")

@app.command(name="download")
def download_command(
    url: str = typer.Argument(..., help="The URL of the Comick.io manga or chapter."),
    output: str = typer.Option(None, "--output", "-o", help=f"The base directory to save the downloaded chapters."),
    chapters: str = typer.Option(None, "--chapters", "-c", help="A string specifying chapters to download (e.g., '1,3-5', 'all')."),
    pdf: bool = typer.Option(False, "--pdf", "-p", help="Convert downloaded images to PDF."),
    delete_images_after_pdf: bool = typer.Option(False, "--delete-images", "-d", help="Delete images after PDF conversion.")
):
    """
    Downloads manga chapters from Comick.io directly via arguments.
    """
    download_from_url(url, output, chapters, pdf, delete_images_after_pdf)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    MangaScraper for Comick.io.
    Run without arguments for an interactive menu.
    """
    if ctx.invoked_subcommand is None:
        main_menu()

if __name__ == "__main__":
    app()
