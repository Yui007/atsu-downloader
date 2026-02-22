"""Download worker for async concurrent chapter downloading."""

from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from config import get_config
from downloader import DownloadManager
from models import MangaInfo, DownloadResult, Chapter


class DownloadWorker(QThread):
    """Worker thread for concurrent chapter downloading without blocking UI."""
    
    progress = pyqtSignal(int, int, str)  # current, total, status
    chapter_complete = pyqtSignal(object)  # DownloadResult
    finished = pyqtSignal(list)  # List[DownloadResult]
    error = pyqtSignal(str)
    
    def __init__(self, manga: MangaInfo, chapters: List[Chapter], parent=None):
        super().__init__(parent)
        self.manga = manga
        self.chapters = chapters
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation of download."""
        self._cancelled = True
    
    def run(self):
        """Download chapters concurrently in background thread."""
        try:
            config = get_config()
            results: List[DownloadResult] = []
            total = len(self.chapters)
            completed = 0
            
            chapters = self.chapters
            
            self.progress.emit(0, total, "Starting concurrent downloads...")
            
            with DownloadManager() as manager:
                # Use ThreadPoolExecutor for concurrent chapter downloads
                with ThreadPoolExecutor(max_workers=config.concurrent_chapters) as executor:
                    # Submit all chapter downloads
                    future_to_chapter = {
                        executor.submit(
                            manager.download_chapter,
                            self.manga,
                            chapter,
                            Path(config.download_path)
                        ): chapter 
                        for chapter in chapters
                    }
                    
                    # Process completed downloads as they finish
                    for future in as_completed(future_to_chapter):
                        if self._cancelled:
                            # Cancel remaining futures
                            for f in future_to_chapter:
                                f.cancel()
                            break
                        
                        chapter = future_to_chapter[future]
                        try:
                            result = future.result()
                            results.append(result)
                            self.chapter_complete.emit(result)
                        except Exception as e:
                            # Create failed result
                            result = DownloadResult(
                                success=False,
                                chapter=chapter,
                                output_path="",
                                error=str(e)
                            )
                            results.append(result)
                            self.chapter_complete.emit(result)
                        
                        completed += 1
                        self.progress.emit(
                            completed, 
                            total, 
                            f"Downloaded {completed}/{total} chapters"
                        )
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))
