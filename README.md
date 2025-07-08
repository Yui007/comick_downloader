#  MangaScraper for Comick.io

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An elegant and powerful tool to scrape and download manga chapters from [Comick.io](https://comick.io/). This project provides both a feature-rich Command Line Interface (CLI) and a sleek, user-friendly Graphical User Interface (GUI).

## ✨ GUI Showcase

![Comick Downloader GUI](https://raw.githubusercontent.com/Yui007/comick_downloader/main/gui/GUI.PNG)

## 🌟 Key Features

- **Dual Interface**: Choose between a powerful CLI for scripting and automation, or an intuitive GUI for ease of use.
- **Flexible Downloading**: Download single chapters, multiple chapters, or entire manga series.
- **Powerful Search**: Easily find any manga on Comick.io by name.
- **Direct URL Support**: Paste a manga or chapter URL to start downloading immediately.
- **PDF Conversion**: Automatically convert downloaded chapters into high-quality PDF files.
- **Smart Cleanup**: Option to delete individual image files after PDF conversion to save space.
- **Robust and Resilient**:
  - Bypasses Cloudflare protection using `cloudscraper` and `playwright`.
  - Parallel downloading for both chapters and images for maximum speed.
  - Automatic retry mechanism for failed downloads.

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.9 or higher.
- `git` for cloning the repository.

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Yui007/comick_downloader.git
    cd comick_downloader
    ```

2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers:**
    This is a one-time setup to download the necessary browser binaries for Playwright.
    ```bash
    playwright install
    ```

## 🖥️ Usage

You can interact with the Comick Downloader through the GUI or the CLI.

### 🎨 Graphical User Interface (GUI)

The GUI provides an intuitive and visual way to download your favorite manga.

**To launch the GUI, run:**
```bash
python gui/main.py
```

For a detailed guide on all GUI features, please see the [**GUI Usage Guide**](./GUI_USAGE.md).

### ⌨️ Command Line Interface (CLI)

The CLI is perfect for power users, scripting, and automation. It supports both an interactive menu and direct commands with arguments.

**To start the interactive CLI, run:**
```bash
python cli/main.py
```

**Examples of direct commands:**

-   **Search for a manga:**
    ```bash
    python cli/main.py search "Solo Leveling"
    ```

-   **Download all chapters of a manga:**
    ```bash
    python cli/main.py download "https://comick.io/comic/solo-leveling" --chapters "all"
    ```

-   **Download a specific range of chapters to a custom directory and convert to PDF:**
    ```bash
    python cli/main.py download "https://comick.io/comic/solo-leveling" --chapters "1-5" --output "my_manga" --pdf
    ```

For a complete list of commands and options, please see the [**CLI Usage Guide**](./CLI_USAGE.md).

## 📁 Project Structure

```
.comick_downloader
├── cli/                 # CLI logic
├── gui/                 # GUI logic and assets
├── core/                # Core scraping and downloading logic
├── utils/               # Utility functions
├── requirements.txt
├── README.md
└── ...
```

## ⚖️ Disclaimer

This tool is intended for educational purposes and for creating personal, offline backups of manga you have legal access to. Please respect the content creators and publishers. Do not use this tool for piracy or distribution.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
