# Comick Downloader - GUI Usage Guide

This guide explains how to use the graphical user interface (GUI) for the Comick Downloader.

## 🚀 Getting Started

### 1. Installation

Before running the GUI, ensure you have all the necessary dependencies installed. You can do this by running the following command in your terminal:

```bash
pip install -r requirements.txt
```

### 2. Running the GUI

To start the application, run the following command from the root directory of the project:

```bash
python gui/main.py
```

This will open the main window of the Comick Downloader.

## ✨ Features

The GUI provides a user-friendly way to download manga from Comick.io. Here's a breakdown of its features:

### 🔍 Searching for Manga

You can search for any manga by typing its name into the search bar at the top of the window and clicking the "Search" button. The search results will appear in the "Search Results" list.

### 🔗 Using URLs

The application can also handle direct URLs from Comick.io:

- **Manga URL**: If you enter the URL of a manga's main page (e.g., `https://comick.io/comic/some-manga`), the application will skip the search and directly fetch the list of chapters for that manga.
- **Chapter URL**: If you enter the URL of a specific chapter, the application will immediately download that single chapter with the currently selected download options.

### 📚 Chapter Selection

Once you have a list of chapters, you can select the ones you want to download:

- **Single Chapter**: Click on any chapter in the "Chapters" list to select it.
- **Multiple Chapters**: Hold down the `Ctrl` key (or `Cmd` on macOS) and click on multiple chapters to select them.
- **Select All / Deselect All**: Use the "Select All" and "Deselect All" buttons to quickly manage your selection.

### ⚙️ Download Options

Before starting a download, you can configure the following options:

- **Convert to PDF**: When this checkbox is ticked, the application will convert the downloaded images of each chapter into a single PDF file.
- **Delete images after conversion**: If "Convert to PDF" is also ticked, this option will delete the individual image files after the PDF has been created, saving disk space.

### 📂 Output Directory

The application will save downloaded files to a `downloads` folder in the project directory by default. You can choose a different location by clicking the "Select Folder" button and navigating to your desired directory.

### 📊 Download Progress

When you start a download, the progress bar at the bottom of the window will show the overall progress of the download queue. The status bar will provide messages about the current state of the application, such as "Downloading..." or "Download complete."
