"""Download frame - main download interface with clean layout."""

from typing import List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QProgressBar,
    QGroupBox, QTextEdit, QAbstractItemView, QMessageBox,
    QFrame, QScrollArea, QSplitter, QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from downloader.manager import parse_chapter_selection
from models import MangaInfo, Chapter
from gui.workers import ScraperWorker, DownloadWorker
from gui.theme import COLORS


class DownloadFrame(QWidget):
    """Main download interface with URL input, chapter list, and progress."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manga: Optional[MangaInfo] = None
        self.scraper_worker: Optional[ScraperWorker] = None
        self.download_worker: Optional[DownloadWorker] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the download interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(32, 32, 32, 32)
        
        # ─────────────────────────────────────────────────────────────
        # HEADER SECTION
        # ─────────────────────────────────────────────────────────────
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        title = QLabel("📥 Download Manga")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Enter a manga URL from atsu.moe to get started")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; background: transparent;")
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header_widget)
        
        # ─────────────────────────────────────────────────────────────
        # URL INPUT SECTION
        # ─────────────────────────────────────────────────────────────
        url_container = QFrame()
        url_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        url_layout = QHBoxLayout(url_container)
        url_layout.setContentsMargins(20, 16, 20, 16)
        url_layout.setSpacing(16)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://atsu.moe/manga/OaKBx")
        self.url_input.setMinimumHeight(44)
        self.url_input.setFont(QFont("Segoe UI", 12))
        self.url_input.returnPressed.connect(self.fetch_manga)
        url_layout.addWidget(self.url_input)
        
        self.fetch_btn = QPushButton("🔍 Fetch Manga")
        self.fetch_btn.setMinimumHeight(44)
        self.fetch_btn.setMinimumWidth(140)
        self.fetch_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fetch_btn.clicked.connect(self.fetch_manga)
        url_layout.addWidget(self.fetch_btn)
        
        main_layout.addWidget(url_container)
        
        # ─────────────────────────────────────────────────────────────
        # CONTENT AREA (Manga Info + Chapters)
        # ─────────────────────────────────────────────────────────────
        self.content_widget = QWidget()
        self.content_widget.setVisible(False)
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)
        
        # LEFT SIDE - Manga Info Card
        info_card = QFrame()
        info_card.setFixedWidth(320)
        info_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(24, 24, 24, 24)
        info_layout.setSpacing(16)
        
        info_header = QLabel("📖 Manga Info")
        info_header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        info_header.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        info_layout.addWidget(info_header)
        
        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {COLORS['border']};")
        info_layout.addWidget(divider)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        info_layout.addWidget(self.title_label)
        
        # Type
        self.type_label = QLabel()
        self.type_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; background: transparent;")
        info_layout.addWidget(self.type_label)
        
        # Chapter count badge
        self.chapter_count_widget = QFrame()
        self.chapter_count_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['accent']};
                border-radius: 8px;
                padding: 8px 16px;
            }}
        """)
        count_layout = QHBoxLayout(self.chapter_count_widget)
        count_layout.setContentsMargins(12, 8, 12, 8)
        self.chapters_count_label = QLabel()
        self.chapters_count_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.chapters_count_label.setStyleSheet(f"color: {COLORS['bg_dark']}; background: transparent;")
        count_layout.addWidget(self.chapters_count_label)
        info_layout.addWidget(self.chapter_count_widget)
        
        info_layout.addStretch()
        
        # Download section in info card
        download_section = QFrame()
        download_section.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_input']};
                border-radius: 8px;
            }}
        """)
        download_section_layout = QVBoxLayout(download_section)
        download_section_layout.setContentsMargins(16, 16, 16, 16)
        download_section_layout.setSpacing(12)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(24)
        download_section_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Select chapters to download")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; background: transparent;")
        self.status_label.setWordWrap(True)
        download_section_layout.addWidget(self.status_label)
        
        # Download buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        self.download_btn = QPushButton("⬇ Download")
        self.download_btn.setMinimumHeight(44)
        self.download_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4cc764;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_secondary']};
            }}
        """)
        self.download_btn.clicked.connect(self.start_download)
        btn_row.addWidget(self.download_btn, stretch=1)
        
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setFixedSize(54, 54)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setToolTip("Cancel download")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: #ff6b6b;
            }}
        """)
        self.cancel_btn.clicked.connect(self.cancel_download)
        btn_row.addWidget(self.cancel_btn)
        
        download_section_layout.addLayout(btn_row)
        
        info_layout.addWidget(download_section)
        
        content_layout.addWidget(info_card)
        
        # RIGHT SIDE - Chapter List
        chapters_card = QFrame()
        chapters_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        chapters_layout = QVBoxLayout(chapters_card)
        chapters_layout.setContentsMargins(24, 24, 24, 24)
        chapters_layout.setSpacing(16)
        
        # Chapter header with selection buttons
        chapter_header_layout = QHBoxLayout()
        
        chapter_title = QLabel("📚 Chapters")
        chapter_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        chapter_title.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        chapter_header_layout.addWidget(chapter_title)
        
        chapter_header_layout.addStretch()
        
        self.selected_count_label = QLabel("0 selected")
        self.selected_count_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        chapter_header_layout.addWidget(self.selected_count_label)
        
        chapters_layout.addLayout(chapter_header_layout)
        
        # Selection toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_input']};
                border-radius: 8px;
            }}
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 10, 12, 10)
        toolbar_layout.setSpacing(10)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setMinimumHeight(36)
        self.select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: {COLORS['bg_dark']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        self.select_all_btn.clicked.connect(self.select_all)
        toolbar_layout.addWidget(self.select_all_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setObjectName("secondary")
        self.clear_btn.clicked.connect(self.clear_selection)
        toolbar_layout.addWidget(self.clear_btn)
        
        toolbar_layout.addSpacing(20)
        
        range_label = QLabel("Range:")
        range_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        toolbar_layout.addWidget(range_label)
        
        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("e.g. 1-10 or 1,3,5")
        self.range_input.setFixedWidth(150)
        self.range_input.setMinimumHeight(36)
        toolbar_layout.addWidget(self.range_input)
        
        self.select_range_btn = QPushButton("Apply")
        self.select_range_btn.setMinimumHeight(36)
        self.select_range_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_range_btn.setObjectName("secondary")
        self.select_range_btn.clicked.connect(self.select_range)
        toolbar_layout.addWidget(self.select_range_btn)
        
        toolbar_layout.addStretch()
        
        scanlator_label = QLabel("Filter Scanlator:")
        scanlator_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        toolbar_layout.addWidget(scanlator_label)
        
        self.scanlator_filter = QComboBox()
        self.scanlator_filter.setMinimumHeight(36)
        self.scanlator_filter.setMinimumWidth(150)
        self.scanlator_filter.addItem("All Scanlators", None)
        self.scanlator_filter.currentIndexChanged.connect(self.update_chapter_list)
        toolbar_layout.addWidget(self.scanlator_filter)
        
        chapters_layout.addWidget(toolbar)

        
        # Chapter list
        self.chapter_list = QListWidget()
        self.chapter_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.chapter_list.setSpacing(2)
        self.chapter_list.setFont(QFont("Segoe UI", 11))
        self.chapter_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.chapter_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 12px 16px;
                border-radius: 6px;
                margin: 2px 0;
                background-color: {COLORS['bg_input']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent']};
                color: {COLORS['bg_dark']};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {COLORS['border']};
            }}
        """)
        chapters_layout.addWidget(self.chapter_list)
        
        content_layout.addWidget(chapters_card)
        
        main_layout.addWidget(self.content_widget)
        
        # ─────────────────────────────────────────────────────────────
        # LOG SECTION (Collapsible)
        # ─────────────────────────────────────────────────────────────
        self.log_widget = QFrame()
        self.log_widget.setVisible(False)
        self.log_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        log_layout = QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(20, 16, 20, 16)
        log_layout.setSpacing(12)
        
        log_header = QLabel("📋 Activity Log")
        log_header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        log_header.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        log_layout.addWidget(log_header)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(self.log_widget)
        
        main_layout.addStretch()
    
    def log(self, message: str, level: str = "info"):
        """Add a message to the log."""
        colors = {
            "info": COLORS['text_primary'],
            "success": COLORS['success'],
            "error": COLORS['error'],
            "warning": COLORS['warning'],
        }
        color = colors.get(level, COLORS['text_primary'])
        self.log_text.append(f'<span style="color: {color};">• {message}</span>')
        self.log_widget.setVisible(True)
    
    def on_selection_changed(self):
        """Update download button state based on selection."""
        count = len(self.get_selected_chapters())
        self.selected_count_label.setText(f"{count} selected")
    
    def fetch_manga(self):
        """Start fetching manga info."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a manga URL")
            return
        
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("⏳ Loading...")
        self.log(f"Fetching manga from: {url}")
        
        self.scraper_worker = ScraperWorker(url, self)
        self.scraper_worker.finished.connect(self.on_manga_fetched)
        self.scraper_worker.error.connect(self.on_fetch_error)
        self.scraper_worker.start()
    
    def on_manga_fetched(self, manga: MangaInfo):
        """Handle successful manga fetch."""
        self.manga = manga
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("🔍 Fetch Manga")
        
        # Update info panel
        self.title_label.setText(manga.title)
        self.type_label.setText(f"📁 Type: {manga.manga_type}")
        self.chapters_count_label.setText(f"📚 {len(manga.chapters)} Chapters")
        
        # Invalidate current scanlator filter
        self.scanlator_filter.blockSignals(True)
        self.scanlator_filter.clear()
        self.scanlator_filter.addItem("All Scanlators", None)
        for scanlator in manga.scanlators:
            self.scanlator_filter.addItem(scanlator.name, scanlator.id)
        self.scanlator_filter.blockSignals(False)
        
        # Populate chapter list
        self.update_chapter_list()
        
        self.content_widget.setVisible(True)
        self.log(f"✓ Found {len(manga.chapters)} chapters", "success")

    def update_chapter_list(self):
        """Filter and display chapters based on selected scanlator."""
        if not self.manga:
            return
            
        selected_scan_id = self.scanlator_filter.currentData()
        self.chapter_list.clear()
        
        for chapter in self.manga.chapters:
            if selected_scan_id and chapter.scanlation_manga_id != selected_scan_id:
                continue
                
            item_text = f"Chapter {chapter.number}  •  {chapter.title}  •  {chapter.page_count} pages"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, chapter)
            self.chapter_list.addItem(item)
            
        self.on_selection_changed()

    
    def on_fetch_error(self, error: str):
        """Handle fetch error."""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("🔍 Fetch Manga")
        self.log(f"✗ Error: {error}", "error")
        QMessageBox.critical(self, "Error", error)
    
    def select_all(self):
        """Select all chapters."""
        self.chapter_list.selectAll()
    
    def clear_selection(self):
        """Clear chapter selection."""
        self.chapter_list.clearSelection()
    
    def select_range(self):
        """Select chapters by range."""
        range_text = self.range_input.text().strip()
        if not range_text or not self.manga:
            return
        
        self.chapter_list.clearSelection()
        
        indices = parse_chapter_selection(range_text, self.chapter_list.count())
        
        for idx in indices:
            if idx < self.chapter_list.count():
                item = self.chapter_list.item(idx)
                if item:
                    item.setSelected(True)
        
        self.log(f"Selected {len(indices)} chapters")
    
    def get_selected_chapters(self) -> List[Chapter]:
        """Get selected chapter objects."""
        chapters = []
        for i in range(self.chapter_list.count()):
            item = self.chapter_list.item(i)
            if item and item.isSelected():
                chapter = item.data(Qt.ItemDataRole.UserRole)
                if chapter:
                    chapters.append(chapter)
        return chapters
    
    def start_download(self):
        """Start downloading selected chapters."""
        if not self.manga:
            return
        
        selected_chapters = self.get_selected_chapters()
        if not selected_chapters:
            QMessageBox.warning(self, "No Selection", "Please select at least one chapter to download.")
            return
        
        self.download_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setMaximum(len(selected_chapters))
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting download...")
        
        self.log(f"Starting download of {len(selected_chapters)} chapters...")
        
        self.download_worker = DownloadWorker(self.manga, selected_chapters, self)
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.chapter_complete.connect(self.on_chapter_complete)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.start()
    
    def cancel_download(self):
        """Cancel ongoing download."""
        if self.download_worker:
            self.download_worker.cancel()
            self.log("Download cancelled by user", "warning")
            self.status_label.setText("Download cancelled")
    
    def on_download_progress(self, current: int, total: int, status: str):
        """Update download progress."""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"[{current}/{total}] {status}")
    
    def on_chapter_complete(self, result):
        """Handle chapter download complete."""
        if result.success:
            self.log(f"✓ {result.chapter.title}", "success")
        else:
            self.log(f"✗ {result.chapter.title}: {result.error}", "error")
    
    def on_download_finished(self, results):
        """Handle all downloads complete."""
        self.download_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText(f"✓ Complete: {successful} downloaded, {failed} failed")
        self.log(f"Download finished: {successful}/{len(results)} successful", 
                 "success" if failed == 0 else "warning")
        
        if failed == 0:
            QMessageBox.information(self, "Download Complete", 
                f"Successfully downloaded {successful} chapters!")
    
    def on_download_error(self, error: str):
        """Handle download error."""
        self.download_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.status_label.setText(f"Error: {error}")
        self.log(f"✗ Error: {error}", "error")
        QMessageBox.critical(self, "Download Error", error)
