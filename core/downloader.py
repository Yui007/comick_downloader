# core/downloader.py
import os
import requests
from .config import HEADERS

class Downloader:
    """
    Handles downloading and saving images from a list of URLs.
    """
    def download_images(self, image_urls: list[str], output_dir: str, user_agent: str, chapter_url: str):
        """
        Downloads images from the given URLs and saves them to the output directory.

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

        for idx, url in enumerate(image_urls, start=1):
            try:
                ext = url.split(".")[-1].split("?")[0]
                filename = os.path.join(output_dir, f"{idx:03d}.{ext}")
                print(f"⬇️ Downloading {filename}")

                img_res = requests.get(url, headers=headers)
                img_res.raise_for_status()

                if not img_res.headers.get("Content-Type", "").startswith("image"):
                    print(f"⚠️ Skipped non-image: {url}")
                    continue

                with open(filename, "wb") as f:
                    f.write(img_res.content)

                print(f"✅ Saved: {filename}")

            except requests.exceptions.RequestException as e:
                print(f"❌ Error downloading {url}: {e}")