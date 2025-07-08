import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QListWidget, QLabel, QProgressBar,
                             QListWidgetItem, QFileDialog, QMessageBox, QStatusBar, 
                             QGraphicsOpacityEffect, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSlot, QPropertyAnimation, QEasingCurve
from gui.controllers import GuiController
from core.config import DEFAULT_OUTPUT_DIR

class MangaDownloaderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = GuiController()
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setWindowTitle('Comick Downloader')
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Search layout
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter Manga Name or URL...")
        self.search_button = QPushButton("Search")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        # Results and Chapters layout
        self.results_list = QListWidget()
        self.results_list.setAlternatingRowColors(True)
        main_layout.addWidget(QLabel("Search Results:"))
        main_layout.addWidget(self.results_list)

        self.chapters_list = QListWidget()
        self.chapters_list.setAlternatingRowColors(True)
        self.chapters_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        chapter_selection_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.deselect_all_button = QPushButton("Deselect All")
        chapter_selection_layout.addWidget(self.select_all_button)
        chapter_selection_layout.addWidget(self.deselect_all_button)

        main_layout.addWidget(QLabel("Chapters:"))
        main_layout.addLayout(chapter_selection_layout)
        main_layout.addWidget(self.chapters_list)

        # Output directory layout
        output_layout = QHBoxLayout()
        self.output_dir_label = QLabel(f"Output: {os.path.abspath(DEFAULT_OUTPUT_DIR)}")
        self.select_dir_button = QPushButton("Select Folder")
        output_layout.addWidget(self.output_dir_label)
        output_layout.addWidget(self.select_dir_button)
        main_layout.addLayout(output_layout)

        # Download options
        download_options_layout = QHBoxLayout()
        self.pdf_checkbox = QCheckBox("Convert to PDF")
        self.pdf_checkbox.setChecked(True)
        self.delete_images_checkbox = QCheckBox("Delete images after conversion")
        self.delete_images_checkbox.setChecked(True)
        download_options_layout.addWidget(self.pdf_checkbox)
        download_options_layout.addWidget(self.delete_images_checkbox)
        main_layout.addLayout(download_options_layout)

        # Download layout
        download_layout = QHBoxLayout()
        self.download_button = QPushButton("Download Selected Chapters")
        self.progress_bar = QProgressBar()
        download_layout.addWidget(self.download_button)
        download_layout.addWidget(self.progress_bar)
        main_layout.addLayout(download_layout)

        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)

        self.apply_stylesheet()

        self.output_dir = os.path.abspath(DEFAULT_OUTPUT_DIR)

    def connect_signals(self):
        self.search_button.clicked.connect(self.on_search_clicked)
        self.results_list.itemClicked.connect(self.on_manga_selected)
        self.select_dir_button.clicked.connect(self.on_select_dir_clicked)
        self.download_button.clicked.connect(self.on_download_clicked)
        self.select_all_button.clicked.connect(self.select_all_chapters)
        self.deselect_all_button.clicked.connect(self.deselect_all_chapters)

        self.controller.searchResultsReady.connect(self.update_search_results)
        self.controller.chaptersReady.connect(self.update_chapter_list)
        self.controller.downloadProgress.connect(self.update_progress_bar)
        self.controller.downloadFinished.connect(self.on_download_finished)

    def on_search_clicked(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self.results_list.clear()
        self.chapters_list.clear()

        if "comick.io/comic/" in query:
            # This regex is a bit more robust for identifying chapter URLs
            if re.search(r"/(c\d+|chapter-[\w-]+)", query):
                self.results_list.addItem(f"Directly downloading chapter from URL...")
                convert_to_pdf = self.pdf_checkbox.isChecked()
                delete_images = self.delete_images_checkbox.isChecked()
                self.controller.download_single_chapter_from_url(query, self.output_dir, convert_to_pdf, delete_images)
            else:
                self.results_list.addItem(f"Fetching chapters from URL...")
                self.controller.fetch_chapters_from_url(query)
        else:
            self.results_list.addItem("Searching...")
            self.controller.start_search(query)

    def on_manga_selected(self, item):
        row = self.results_list.row(item)
        self.chapters_list.clear()
        self.chapters_list.addItem("Fetching chapters...")
        self.controller.fetch_chapters(row)

    def on_select_dir_clicked(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_dir)
        if path:
            self.output_dir = path
            self.output_dir_label.setText(f"Output: {self.output_dir}")

    def on_download_clicked(self):
        selected_items = self.chapters_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Chapters Selected", "Please select one or more chapters to download.")
            return

        selected_indices = [self.chapters_list.row(item) for item in selected_items]
        
        convert_to_pdf = self.pdf_checkbox.isChecked()
        delete_images = self.delete_images_checkbox.isChecked()

        self.download_button.setEnabled(False)
        self.status_bar.showMessage("Starting download...")
        self.controller.start_download(selected_indices, self.output_dir, convert_to_pdf, delete_images)

    def select_all_chapters(self):
        for i in range(self.chapters_list.count()):
            self.chapters_list.item(i).setSelected(True)

    def deselect_all_chapters(self):
        for i in range(self.chapters_list.count()):
            self.chapters_list.item(i).setSelected(False)

    @pyqtSlot(int)
    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(f"Downloading... {value}%")

    @pyqtSlot(str)
    def on_download_finished(self, output_dir):
        self.progress_bar.setValue(100)
        self.status_bar.showMessage("Download complete.")
        self.download_button.setEnabled(True)
        QMessageBox.information(self, "Download Complete", f"All selected chapters have been downloaded to:\n{output_dir}")
        self.progress_bar.setValue(0)


    @pyqtSlot(list)
    def update_search_results(self, results):
        self.results_list.clear()
        if not results:
            self.results_list.addItem("No results found.")
            return
        for result in results:
            self.results_list.addItem(result['title'])
        self.fade_in(self.results_list)

    @pyqtSlot(list)
    def update_chapter_list(self, chapters):
        self.chapters_list.clear()
        if not chapters:
            self.chapters_list.addItem("No chapters found.")
            return
        for chapter in chapters:
            item = QListWidgetItem(chapter['title'])
            self.chapters_list.addItem(item)
        self.fade_in(self.chapters_list)

    def fade_in(self, widget):
        self.opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(self.opacity_effect)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: "Segoe UI", sans-serif;
            }
            QLineEdit {
                background-color: #34495e;
                border: 1px solid #2c3e50;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QListWidget {
                background-color: #34495e;
                border: 1px solid #2c3e50;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:alternate {
                background-color: #2c3e50;
            }
            QListWidget::item:selected {
                background-color: #e74c3c;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
            }
            QProgressBar {
                border: 1px solid #2c3e50;
                border-radius: 5px;
                text-align: center;
                background-color: #34495e;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 4px;
            }
        """)

def main():
    app = QApplication(sys.argv)
    gui = MangaDownloaderGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
