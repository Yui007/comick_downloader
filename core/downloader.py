# core/downloader.py
import os
import requests
from rich.progress import Progress, BarColumn, TextColumn, TransferSpeedColumn, TimeRemainingColumn
from .config import HEADERS

class Downloader:
    """
    Handles downloading and saving images from a list of URLs with a progress bar.
    """
    def download_images(self, image_urls: list[str], output_dir: str, user_agent: str, chapter_url: str):
        """
        Downloads images from the given URLs and saves them to the output directory,
        displaying a progress bar.

        Args:
            image_urls: A list of image URLs to download.
            output_dir: The directory to save the images in.
            user_agent: The User-Agent to use for the request headers.
            chapter_url: The original chapter URL for the Referer header.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        headers = HEADERS.copy()
        headers["User-Agent"] = user_agent
        headers["Referer"] = chapter_url

        with Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("[bold green]Downloading", total=len(image_urls))

            for idx, url in enumerate(image_urls, start=1):
                try:
                    ext = url.split(".")[-1].split("?")[0]
                    filename = os.path.join(output_dir, f"{idx:03d}.{ext}")
                    
                    img_res = requests.get(url, headers=headers, stream=True)
                    img_res.raise_for_status()

                    if not img_res.headers.get("Content-Type", "").startswith("image"):
                        print(f"⚠️ Skipped non-image: {url}")
                        progress.update(task, advance=1)
                        continue

                    total_size = int(img_res.headers.get('content-length', 0))
                    
                    with open(filename, "wb") as f:
                        for chunk in img_res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    progress.update(task, advance=1)

                except requests.exceptions.RequestException as e:
                    print(f"❌ Error downloading {url}: {e}")
                    progress.update(task, advance=1) # Still advance progress
