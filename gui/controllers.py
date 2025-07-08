from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from core.scraper import ComickScraper
from core.downloader import Downloader
import os
from utils.sanitizer import sanitize_filename

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
        for i, chapter in enumerate(chapters):
            print(f"Downloading chapter {i+1}/{total_chapters}: {chapter['title']}")
            
            # Sanitize chapter title for folder name
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

            progress = int(((i + 1) / total_chapters) * 100)
            self.downloadProgress.emit(progress)
        
        return output_dir # Return the main output directory

    def on_download_finished(self, output_dir):
        print("Controller: Download finished.")
        self.downloadFinished.emit(output_dir)
