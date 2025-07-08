# core/downloader.py
import os
import requests
import time
from rich.progress import Progress, BarColumn, TextColumn, TransferSpeedColumn, TimeRemainingColumn, TaskID
from .config import HEADERS
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import io

class Downloader:
    """
    Handles downloading and saving images from a list of URLs with a progress bar.
    """
    def _download_image(self, url: str, headers: dict, output_dir: str, idx: int, total_images: int, max_retries: int = 3):
        """Helper function to download a single image with retries."""
        for attempt in range(max_retries):
            try:
                ext = url.split(".")[-1].split("?")[0]
                filename = os.path.join(output_dir, f"{idx:03d}.{ext}")
                
                img_res = requests.get(url, headers=headers, stream=True, timeout=15) # 15-second timeout
                img_res.raise_for_status()

                if not img_res.headers.get("Content-Type", "").startswith("image"):
                    print(f"⚠️ Skipped non-image: {url}")
                    return None

                with open(filename, "wb") as f:
                    for chunk in img_res.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded image {idx}/{total_images} for {os.path.basename(output_dir)}")
                return filename
            except requests.exceptions.RequestException as e:
                print(f"❌ Error downloading {url} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"❌ Failed to download {url} after {max_retries} attempts.")
                    return None

    def download_images(self, image_urls: list[str], output_dir: str, user_agent: str, chapter_url: str):
        """
        Downloads images from the given URLs in parallel and saves them to the output directory.

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

        total_images = len(image_urls)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self._download_image, url, headers, output_dir, idx, total_images): url for idx, url in enumerate(image_urls, start=1)}
            
            for future in as_completed(futures):
                try:
                    future.result() # Re-raise exceptions from threads
                except Exception as e:
                    print(f"[bold red]Error in image download thread: {e}[/bold red]")
        
    def convert_to_pdf(self, image_folder: str, output_pdf_path: str):
        """
        Converts all images in a folder to a single high-quality PDF.

        Args:
            image_folder: The folder containing the downloaded images.
            output_pdf_path: The path to save the output PDF.
        """
        images = []
        img_files = sorted([f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))])

        for filename in img_files:
            try:
                img_path = os.path.join(image_folder, filename)
                image = Image.open(img_path).convert("RGB")
                images.append(image)
            except IOError:
                print(f"⚠️ Could not open {filename}, skipping.")

        if images:
            images[0].save(
                output_pdf_path,
                save_all=True,
                append_images=images[1:],
                quality=95,  # High quality
                optimize=True
            )
            print(f"✅ PDF saved to {output_pdf_path}")

    def delete_images(self, image_folder: str):
        """
        Deletes all image files from a folder.

        Args:
            image_folder: The folder containing the images to delete.
        """
        for filename in os.listdir(image_folder):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                os.remove(os.path.join(image_folder, filename))
        print(f"🗑️ Deleted images from {image_folder}")
