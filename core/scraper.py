# core/scraper.py
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
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
            page.goto(chapter_url, wait_until="load", timeout=5000)
            page.wait_for_timeout(3000)  # Wait for dynamic content

            print("📸 Extracting image URLs...")
            img_elements = page.query_selector_all('img[src*="meo.comick.pictures"]')
            image_urls = [img.get_attribute("src") for img in img_elements if img.get_attribute("src")]
            
            print(f"🔍 Found {len(image_urls)} images")
            browser.close()

        return image_urls, user_agent

    def fetch_chapter_list(self, manga_url: str) -> list[dict]:
        """
        Fetches the list of chapters from a manga's main page, handling pagination.

        Args:
            manga_url: The URL of the manga's main page.

        Returns:
            A list of dictionaries, where each dictionary represents a chapter
            and contains the 'title' and 'url'.
        """
        print("📚 Fetching chapter list...")
        chapters = {}
        page_num = 1
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            while True:
                # Construct URL with page number
                parts = urlparse(manga_url)
                query = parse_qs(parts.query)
                query['page'] = page_num
                new_query = urlencode(query, doseq=True)
                # Remove fragment and update query
                current_url = urlunparse(parts._replace(query=new_query, fragment=''))

                print(f"🌐 Visiting page {page_num}: {current_url}")
                
                try:
                    page.goto(current_url, wait_until="networkidle", timeout=5000)
                    # Wait for chapter links to be visible
                    page.wait_for_selector('a[href*="/comic/"][href*="chapter"]', timeout=5000)
                except Exception:
                    # This can happen if the page doesn't exist or has no chapters, which is our exit condition
                    print(f"✅ No more chapters found on page {page_num}. Assuming end of list.")
                    break

                try:
                    # Scroll to the bottom of the page to load all chapters
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(3000)  # Wait for dynamic content

                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    chapter_rows = soup.select('tr.group')

                    if not chapter_rows:
                        print(f"✅ No chapters found on page {page_num}. Finalizing list.")
                        break # Exit condition: no more chapters on the page

                    new_chapters_found_on_page = 0
                    for row in chapter_rows:
                        link_element = row.select_one('a[href*="/comic/"][href*="chapter"]')
                        if not link_element:
                            continue

                        title_span = link_element.select_one('span[title]')
                        if not title_span:
                            continue

                        title = title_span.get('title', title_span.text.strip())
                        url = link_element['href']

                        group_links = row.select('a[href*="/group/"]')
                        group_names = [g.text.strip() for g in group_links]
                        
                        if group_names:
                            title = f"{title} ({', '.join(group_names)})"

                        if not url.startswith('http'):
                            url = f"{BASE_URL}{url}"

                        match = re.search(r'Chapter\s*([\d.]+)', title, re.IGNORECASE)
                        if match:
                            chapter_num = float(match.group(1))
                            if chapter_num not in chapters:
                                chapters[chapter_num] = {"title": title, "url": url}
                                new_chapters_found_on_page += 1
                    
                    if new_chapters_found_on_page == 0 and page_num > 1:
                        print(f"✅ No new chapters on page {page_num}. Assuming end of list.")
                        break

                    print(f"Found {new_chapters_found_on_page} new chapters on page {page_num}.")
                    page_num += 1

                except Exception as e:
                    print(f"❌ An error occurred while processing page {page_num}: {e}")
                    break # Exit loop on error
            
            browser.close()

        # Sort chapters by chapter number
        sorted_chapters = [chapters[key] for key in sorted(chapters.keys())]
        
        print(f"🔍 Found a total of {len(sorted_chapters)} unique chapters.")
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

        print("🚀 Getting Cloudflare cookies using cloudscraper...")
        try:
            resp = self.scraper.get(search_url)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch with cloudscraper: {e}")
            return []

        cookies = self.scraper.cookies.get_dict()
        user_agent = self.scraper.headers["User-Agent"]

        print("🧭 Launching Playwright with Cloudflare cookies...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(user_agent=user_agent)

            cookie_list = [{"name": k, "value": v, "domain": "comick.io", "path": "/"} for k, v in cookies.items()]
            context.add_cookies(cookie_list)

            page = context.new_page()
            print(f"🌐 Visiting: {search_url}")
            page.goto(search_url, wait_until="networkidle")
            
            results = []
            last_height = page.evaluate("document.body.scrollHeight")
            
            while True:
                # Scroll down
                page.evaluate("window.scrollBy(0, 500)") # Scroll by 500px
                page.wait_for_timeout(1000)

                # Parse content
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                for link_element in soup.select('a[href*="/comic/"]'):
                    title_element = link_element.find('p', class_='font-bold')
                    if title_element:
                        title = title_element.text.strip()
                        url = link_element['href']
                        if title and url:
                            if not url.startswith('http'):
                                url = f"{BASE_URL}{url}"
                            # Avoid duplicates
                            if not any(d.get('url') == url for d in results):
                                 results.append({"title": title, "url": url})

                # Check if we've reached the bottom
                new_height = page.evaluate("document.body.scrollHeight")
                if page.evaluate("window.pageYOffset + window.innerHeight") >= new_height:
                    break
            
            browser.close()
        
        print(f"🔍 Found {len(results)} results.")
        return results
