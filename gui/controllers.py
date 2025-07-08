from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from core.scraper import ComickScraper
from core.downloader import Downloader
import os
from utils.sanitizer import sanitize_filename
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class Worker(QObject):
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        result = self.fn(*self.args, **self.kwargs)
        self.finished.emit(result)

class GuiController(QObject):
    # Signals to update the GUI
    searchResultsReady = pyqtSignal(list)
    chaptersReady = pyqtSignal(list)
    downloadProgress = pyqtSignal(int)
    downloadFinished = pyqtSignal(str) # PDF path

    def __init__(self):
        super().__init__()
        self.scraper = ComickScraper()
        self.downloader = Downloader()
        self.manga_list = []
        self.chapter_list = []
        self.thread = None
        self.worker = None

    def _run_in_thread(self, fn, on_finish, *args, **kwargs):
        self.thread = QThread()
        self.worker = Worker(fn, *args, **kwargs)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(on_finish)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @pyqtSlot(str)
    def start_search(self, query):
        """Starts a search for manga in a worker thread."""
        print(f"Controller: Searching for {query}")
        self._run_in_thread(self.scraper.search_manga, self.on_search_finished, query)

    def on_search_finished(self, results):
        self.manga_list = results
        self.searchResultsReady.emit(results)

    @pyqtSlot(int)
    def fetch_chapters(self, manga_index):
        """Fetches chapters for a selected manga in a worker thread."""
        if 0 <= manga_index < len(self.manga_list):
            manga = self.manga_list[manga_index]
            print(f"Controller: Fetching chapters for {manga['title']}")
            self._run_in_thread(self.scraper.fetch_chapter_list, self.on_chapters_finished, manga['url'])

    def on_chapters_finished(self, chapters):
        self.chapter_list = chapters
        self.chaptersReady.emit(chapters)

    @pyqtSlot(str)
    def fetch_chapters_from_url(self, url):
        """Fetches chapters directly from a manga URL."""
        print(f"Controller: Fetching chapters from URL {url}")
        self._run_in_thread(self.scraper.fetch_chapter_list, self.on_chapters_finished, url)

    @pyqtSlot(list, str, bool, bool)
    def start_download(self, selected_indices, output_dir, convert_to_pdf, delete_images):
        """Starts downloading selected chapters in a worker thread."""
        chapters_to_download = [self.chapter_list[i] for i in selected_indices]
        if not chapters_to_download:
            return

        print(f"Controller: Download requested for {len(chapters_to_download)} chapters.")
        self._run_in_thread(self._perform_download, self.on_download_finished, chapters_to_download, output_dir, convert_to_pdf, delete_images)

    def _perform_download(self, chapters, output_dir, convert_to_pdf, delete_images):
        total_chapters = len(chapters)
        completed_chapters = 0
        progress_lock = threading.Lock()

        def _download_chapter_worker(chapter):
            nonlocal completed_chapters
            try:
                print(f"Downloading chapter: {chapter['title']}")
                
                chapter_folder_name = sanitize_filename(chapter['title'])
                chapter_output_dir = os.path.join(output_dir, chapter_folder_name)

                image_urls, user_agent = self.scraper.fetch_image_urls(chapter['url'])
                if image_urls:
                    self.downloader.download_images(image_urls, chapter_output_dir, user_agent, chapter['url'])
                    
                    if convert_to_pdf:
                        pdf_path = os.path.join(output_dir, f"{chapter_folder_name}.pdf")
                        self.downloader.convert_to_pdf(chapter_output_dir, pdf_path)
                        if delete_images:
                            self.downloader.delete_images(chapter_output_dir)
                            os.rmdir(chapter_output_dir)
            except Exception as e:
                print(f"Error downloading chapter {chapter.get('title', 'N/A')}: {e}")
            finally:
                with progress_lock:
                    completed_chapters += 1
                    progress = int((completed_chapters / total_chapters) * 100)
                    self.downloadProgress.emit(progress)

        with ThreadPoolExecutor(max_workers=10) as executor: # 5 chapters at a time
            futures = [executor.submit(_download_chapter_worker, chapter) for chapter in chapters]
            for future in as_completed(futures):
                future.result() # Wait for all to complete and raise exceptions if any

        return output_dir

    def on_download_finished(self, output_dir):
        print("Controller: Download finished.")
        self.downloadFinished.emit(output_dir)

    @pyqtSlot(str, str, bool, bool)
    def download_single_chapter_from_url(self, url, output_dir, convert_to_pdf, delete_images):
        """Downloads a single chapter directly from a URL."""
        print(f"Controller: Downloading single chapter from {url}")
        self._run_in_thread(self._perform_single_download, self.on_download_finished, url, output_dir, convert_to_pdf, delete_images)

    def _perform_single_download(self, url, output_dir, convert_to_pdf, delete_images):
        """Helper method to download a single chapter."""
        # Create a mock chapter object for the downloader
        # A bit of a hack, but it lets us reuse the existing download logic
        chapter_title = url.split("/")[-1] # Simple title extraction
        chapter = {"title": chapter_title, "url": url}
        
        self._perform_download([chapter], output_dir, convert_to_pdf, delete_images)
        return output_dir
