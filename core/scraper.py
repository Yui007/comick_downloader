# core/scraper.py
import re
import cloudscraper
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from .config import HEADERS, BASE_URL

class ComickScraper:
    """
    Handles scraping logic for Comick.io, including bypassing Cloudflare
    and extracting image URLs from a chapter page.
    """
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(browser='chrome')

    def fetch_image_urls(self, chapter_url: str) -> tuple[list[str], str]:
        """
        Fetches all image URLs from a given Comick.io chapter URL.

        Args:
            chapter_url: The URL of the chapter to scrape.

        Returns:
            A tuple containing a list of image URLs and the user agent used.
        """
        print("🚀 Getting Cloudflare cookies using cloudscraper...")
        try:
            resp = self.scraper.get(chapter_url)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch with cloudscraper: {e}")
            return [], ""

        cookies = self.scraper.cookies.get_dict()
        user_agent = self.scraper.headers["User-Agent"]

        print("🧭 Launching Playwright with Cloudflare cookies...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=user_agent)

            cookie_list = [{"name": k, "value": v, "domain": "comick.io", "path": "/"} for k, v in cookies.items()]
            context.add_cookies(cookie_list)

            page = context.new_page()
            print(f"🌐 Visiting: {chapter_url}")
            page.goto(chapter_url, wait_until="load", timeout=60000)
            page.wait_for_timeout(5000)  # Wait for dynamic content

            print("📸 Extracting image URLs...")
            img_elements = page.query_selector_all('img[src*="meo.comick.pictures"]')
            image_urls = [img.get_attribute("src") for img in img_elements if img.get_attribute("src")]
            
            print(f"🔍 Found {len(image_urls)} images")
            browser.close()

        return image_urls, user_agent

    def fetch_chapter_list(self, manga_url: str) -> list[dict]:
        """
        Fetches the list of chapters from a manga's main page.

        Args:
            manga_url: The URL of the manga's main page.

        Returns:
            A list of dictionaries, where each dictionary represents a chapter
            and contains the 'title' and 'url'.
        """
        print("📚 Fetching chapter list...")
        chapters = {}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            current_url = manga_url
            while current_url:
                try:
                    print(f"🌐 Visiting: {current_url}")
                    page.goto(current_url, wait_until="load", timeout=60000)
                    # Wait for chapter links to be visible
                    page.wait_for_selector('a[href*="/comic/"][href*="chapter"]', timeout=60000)
                    page.wait_for_timeout(2000)

                    # Scroll to the bottom of the page to load all chapters
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(10000)  # Wait for dynamic content to load after scrolling

                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Based on the user-provided HTML, we select the table rows
                    chapter_rows = soup.select('tr.group')

                    for row in chapter_rows:
                        link_element = row.select_one('a[href*="/comic/"][href*="chapter"]')
                        if not link_element:
                            continue

                        title_span = link_element.select_one('span[title]')
                        if not title_span:
                            continue

                        # Use the 'title' attribute for the full chapter name
                        title = title_span.get('title', title_span.text.strip())
                        url = link_element['href']

                        # Find all group names within the row
                        group_links = row.select('a[href*="/group/"]')
                        group_names = [g.text.strip() for g in group_links]
                        
                        if group_names:
                            title = f"{title} [{', '.join(group_names)}]"

                        if not url.startswith('http'):
                            url = f"{BASE_URL}{url}"

                        match = re.search(r'Chapter\s*([\d.]+)', title)
                        if match:
                            chapter_num = float(match.group(1))
                            if chapter_num not in chapters:
                                chapters[chapter_num] = {"title": title, "url": url}

                    # Find the "Next" button using a more reliable selector
                    next_button = soup.select_one('nav[aria-label="pagination"] a:last-child')
                    if next_button and "Next" in next_button.text and next_button.has_attr('href'):
                        next_page_path = next_button['href']
                        current_url = f"{BASE_URL}{next_page_path}"
                    else:
                        current_url = None

                except Exception as e:
                    print(f"❌ Failed to fetch with Playwright: {e}")
                    current_url = None # Exit loop on error
            
            browser.close()

        # Sort chapters by chapter number
        sorted_chapters = [chapters[key] for key in sorted(chapters.keys())]
        
        print(f"🔍 Found {len(sorted_chapters)} unique chapters.")
        return sorted_chapters

    def search_manga(self, query: str) -> list[dict]:
        """
        Searches for manga on Comick.io.

        Args:
            query: The search term.

        Returns:
            A list of dictionaries, where each dictionary represents a manga
            and contains the 'title' and 'url'.
        """
        search_url = f"{BASE_URL}/search?q={query}"
        print(f"🔍 Searching for: {query}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(search_url, wait_until="load", timeout=60000)
                page.wait_for_timeout(5000) # Wait for dynamic content
                content = page.content()
            except Exception as e:
                print(f"❌ Failed to fetch with Playwright: {e}")
                return []
            finally:
                browser.close()

        soup = BeautifulSoup(content, 'html.parser')
        
        results = []
        # This selector is more specific to the search results page structure
        for el in soup.select('div.flex.items-center > a[href*="/comic/"]'):
            title_div = el.find('div', class_='font-bold')
            if title_div:
                title = title_div.text.strip()
                url = el.get('href')
                if title and url:
                    if not url.startswith('http'):
                        url = f"{BASE_URL}{url}"
                    results.append({"title": title, "url": url})
        
        print(f"🔍 Found {len(results)} results.")
        return results
