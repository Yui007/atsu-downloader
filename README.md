# Atsu Downloader

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CLI](https://img.shields.io/badge/interface-Typer%20%2B%20Rich-111111)](https://typer.tiangolo.com/)
[![GUI](https://img.shields.io/badge/gui-PyQt6-41CD52?logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![Site](https://img.shields.io/badge/source-atsu.moe-0f172a)](https://atsu.moe/)

Modern manga downloader for `atsu.moe` with both a full CLI and a PyQt6 desktop GUI.

Repository: `https://github.com/Yui007/atsu-downloader`

## Screenshot

Initial GUI view:

![Atsu Downloader GUI Start Screen](gui.png)

## Highlights

- Modular architecture: API client, scraper, download manager, converters, CLI, and GUI.
- Concurrent downloads for chapters and images.
- Multiple output formats: `images`, `pdf`, `cbz`.
- Retry with exponential backoff for API/image requests.
- Persistent configuration in `config.json`.
- Interactive chapter selection:
  - `all` or `a`
  - single value: `5`
  - range: `1-10`
  - mixed: `1,3,5-7`
- Duplicate chapter cleanup during parsing (prevents repeated chapter blocks in listings).

## Install

```bash
git clone https://github.com/Yui007/atsu-downloader.git
cd atsu-downloader
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

CLI interactive mode:

```bash
python main.py
```

GUI mode:

```bash
python gui_main.py
```

CLI direct mode examples:

```bash
python main.py https://atsu.moe/manga/OaKBx
python main.py https://atsu.moe/manga/OaKBx -c all
python main.py https://atsu.moe/manga/OaKBx -c 1-20 -f cbz
python main.py https://atsu.moe/manga/OaKBx -c 1,3,8-12 -f pdf -o ./downloads
python main.py https://atsu.moe/manga/OaKBx -c all -v
```

## CLI Options

`python main.py [URL] [OPTIONS]`

- `-c`, `--chapters`: Chapter selection expression (`all`, `1-10`, `1,3,5-7`)
- `-f`, `--format`: Output format (`images`, `pdf`, `cbz`)
- `-o`, `--output`: Output directory
- `-v`, `--verbose`: Enable detailed logs

## GUI Features

- Fetch manga by URL or ID.
- Chapter list with multi-select, select-all, clear, and range apply.
- Real-time progress and activity log.
- Settings tab for format, path, concurrency, retries, and logging.

## Configuration

Saved in `config.json` (auto-created).

```json
{
  "download_format": "images",
  "keep_images": true,
  "download_path": "./downloads",
  "concurrent_chapters": 3,
  "concurrent_images": 5,
  "max_display_chapters": 0,
  "max_retries": 3,
  "retry_delay": 2,
  "enable_logs": false
}
```

## Requirements

- Python `3.10+`
- `typer`
- `rich`
- `requests`
- `Pillow`
- `PyQt6`

Install with:

```bash
pip install -r requirements.txt
```

## Project Layout

```text
atsu-downloader/
|- api/           # Atsu API client + retry
|- scraper/       # URL/ID parsing + manga fetch
|- downloader/    # chapter/image download orchestration
|- converters/    # PDF/CBZ + ComicInfo.xml generation
|- cli/           # Typer + Rich CLI
|- gui/           # PyQt6 desktop app
|- models.py      # data models
|- config.py      # config load/save helpers
|- main.py        # CLI entrypoint
`- gui_main.py    # GUI entrypoint
```
