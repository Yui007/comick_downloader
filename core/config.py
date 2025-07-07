# core/config.py

# Base URL for the website
BASE_URL = "https://comick.io"

# Headers for requests, User-Agent will be updated by cloudscraper
HEADERS = {
    "Referer": BASE_URL,
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"
}

# Default output directory
DEFAULT_OUTPUT_DIR = "downloads"