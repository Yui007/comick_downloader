# Comick Downloader CLI Usage

This document provides detailed instructions on how to use the command-line interface (CLI) of the Comick Downloader.

## 🚀 Running the Scraper

You can run the scraper in two modes: interactive menu mode or direct command mode using arguments.

### Interactive Menu

To run the scraper in interactive mode, simply execute the script without any arguments:

```bash
python cli/main.py
```

This will present you with a menu of options:

1.  **Download from Manga URL**: Prompts you to enter a manga or chapter URL, output directory, whether to convert to PDF, delete images after PDF, and the number of concurrent threads.
2.  **Search for a Manga**: Prompts you to enter a search query to find a manga, then allows you to select a manga and specify download options including output directory, chapters, whether to convert to PDF, delete images after PDF, and the number of concurrent threads.
3.  **Exit**: Exits the application.

### Direct Commands

You can also use the CLI by providing commands and arguments directly. This is useful for scripting and automation.

There are two main commands: `download` and `search`.

#### Downloading from a URL

The `download` command allows you to download chapters directly from a manga or chapter URL.

**Usage:**

```bash
python cli/main.py download [URL] [OPTIONS]
```

**Arguments:**

-   `URL`: The URL of the manga or chapter you want to download. This is a required argument.

**Options:**

-   `--output, -o`: The directory where the downloaded chapters will be saved. If not provided, a default `downloads` directory will be used.
-   `--chapters, -c`: A string specifying which chapters to download. This can be a single number, a comma-separated list, a range, or "all".
-   `--pdf, -p`: Convert downloaded images to PDF.
-   `--delete-images, -d`: Delete images after PDF conversion (only applicable if `--pdf` is used).
-   `--threads, -t`: Number of concurrent download threads (default: 10).

**Examples:**

-   Download all chapters of a manga:
    ```bash
    python cli/main.py download "https://comick.io/comic/solo-leveling" --chapters "all"
    ```

-   Download a specific range of chapters with 5 threads:
    ```bash
    python cli/main.py download "https://comick.io/comic/00-solo-leveling" --chapters "1-1" --threads 5
    ```

-   Download selected chapters to a custom directory, convert to PDF, and delete images:
    ```bash
    python cli/main.py download "https://comick.io/comic/solo-leveling" --chapters "1,5,10" --output "my_manga" --pdf --delete-images
    ```

-   Download a single chapter URL:
    ```bash
    python cli/main.py download "https://comick.io/comic/solo-leveling/chapter-1-en"
    ```

#### Searching for a Manga

The `search` command allows you to search for a manga and then download chapters.

**Usage:**

```bash
python cli/main.py search [QUERY] [OPTIONS]
```

**Arguments:**

-   `QUERY`: The search term for the manga you want to find. This is a required argument.

**Options:**

-   `--output, -o`: The directory where the downloaded chapters will be saved.
-   `--chapters, -c`: A string specifying which chapters to download after selecting a manga from the search results.

**Examples:**

-   Search for a manga and then interactively select chapters to download:
    ```bash
    python cli/main.py search "Solo Leveling"
    ```

-   Search for a manga and download all chapters to a custom directory:
    ```bash
    python cli/main.py search "Solo Leveling" --output "my_manga" --chapters "all"
    ```

-   Search for a manga and download a range of chapters:
    ```bash
    python cli/main.py search "Solo Leveling" --chapters "1-5"
