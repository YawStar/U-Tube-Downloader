# -*- coding: utf-8 -*-
"""
Thumbnail Service

QNetworkAccessManager ကို အသုံးပြုပြီး Video Thumbnail ကို
Async download လုပ်ပေး

main.py ထဲက logic များ:

    • display_video_info() ထဲက QNetworkRequest + reply.setProperty
    • on_thumbnail_downloaded() — reply handling
    • on_thumbnail_timeout() — 10s timeout
    • save_thumbnail() — Save As dialog + HD download

Request ID စနစ်ကို ထိန်းသိမ်းထား — အရင် fetch ၏ thumbnail
နောက်ကျရောက်လာလျှင် လက်ရှိ fetch ကို မထိခိုက်စေရန်
"""
import os
import re
import requests
from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply,
)
from PySide6.QtWidgets import QFileDialog


class ThumbnailService(QObject):
    """
    Video Thumbnail ကို background မှ download လုပ်ပြီး
    View ကို signals ဖြင့် notify လုပ်
    """

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    thumbnail_ready = Signal(QPixmap)          # download အောင်မြင်
    thumbnail_failed = Signal(str)             # reason
    thumbnail_cancelled = Signal()             # request ID mismatch/timeout

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------
    DEFAULT_TIMEOUT_MS = 10000   # 10 seconds
    SCALED_WIDTH = 340
    SCALED_HEIGHT = 190

    def __init__(self, network_manager: QNetworkAccessManager, parent=None):
        """
        Args:
            network_manager: MainWindow မှ ဖန်တီးထားသော QNetworkAccessManager
            parent: Qt parent (MainWindow)
        """
        super().__init__(parent)
        self.network_manager = network_manager
        # network_manager.finished signal ကို service က ဖမ်းမယ်
        self.network_manager.finished.connect(self._on_reply_finished)

        # State
        self.current_request_id = 0
        self.current_reply: QNetworkReply | None = None
        self.timeout_timer: QTimer | None = None
        self._fallback_urls: list[str] = []

    # ------------------------------------------------------------------
    # Request lifecycle
    # ------------------------------------------------------------------
    def request(self, url: str, request_id: int | None = None) -> int:
        """
        Thumbnail download စတင်

        Args:
            url: Thumbnail URL
            request_id: လက်ရှိ fetch ၏ ID (None ဖြစ်ပါက auto-increment)

        Returns:
            request_id — caller က သိမ်းထားရန်
        """
        if request_id is None:
            self.current_request_id += 1
            request_id = self.current_request_id
        else:
            self.current_request_id = request_id

        # အရင် reply ရှိရင် abort
        self.cancel()

        if not url:
            self.thumbnail_failed.emit("Empty thumbnail URL")
            return request_id

        # Build Fallback URLs list if it's a YouTube URL
        self._fallback_urls = self._build_fallback_urls(url)

        self._start_next_download(request_id)
        return request_id

    def _build_fallback_urls(self, primary_url: str) -> list[str]:
        """ primary_url 404 ဖြစ်ပါက အစားထိုးသုံးရန် fallback list ပြုလုပ် """
        urls = [primary_url]
        
        # YouTube Video ID ကို extraction လုပ်ခြင်း
        vid_match = re.search(r"/(?:vi_webp|vi)/([a-zA-Z0-9_-]{11})/", primary_url)
        if not vid_match:
            vid_match = re.search(r"vi=([a-zA-Z0-9_-]{11})", primary_url)

        if vid_match:
            vid = vid_match.group(1)
            candidates = [
                f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
                f"https://i.ytimg.com/vi/{vid}/sddefault.jpg",
                f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg",
            ]
            for c in candidates:
                if c not in urls:
                    urls.append(c)

        return urls

    def _start_next_download(self, request_id: int) -> None:
        """ List ထဲမှ နောက် URL တစ်ခုကို စတင် ဒေါင်းလုဒ်လုပ် """
        if not self._fallback_urls:
            self.thumbnail_failed.emit("All thumbnail fallback URLs failed (404/Error)")
            return

        current_url = self._fallback_urls.pop(0)

        try:
            req = QNetworkRequest(QUrl(str(current_url)))
            req.setRawHeader(b"User-Agent", b"Mozilla/5.0")

            reply = self.network_manager.get(req)
            reply.setProperty("thumbnail_request_id", request_id)

            self.current_reply = reply

            # Timeout timer
            self.timeout_timer = QTimer(self)
            self.timeout_timer.setSingleShot(True)
            self.timeout_timer.timeout.connect(
                lambda rid=request_id: self._on_timeout(rid)
            )
            self.timeout_timer.start(self.DEFAULT_TIMEOUT_MS)

        except Exception as e:
            self.thumbnail_failed.emit(f"Request error: {e}")

    def cancel(self) -> None:
        """ လက်ရှိ download ကိုရပ် """
        self._fallback_urls.clear()

        if self.timeout_timer is not None:
            try:
                if self.timeout_timer.isActive():
                    self.timeout_timer.stop()
            except Exception:
                pass
            self.timeout_timer = None

        if self.current_reply is not None:
            try:
                if not self.current_reply.isFinished():
                    self.current_reply.abort()
            except Exception:
                pass
            # Reply ကို deleteLater ကို _on_reply_finished မှ လုပ်မယ်

    def reset_state(self) -> None:
        """
        Fetch အသစ် မစခင်မှာ state ကို ရှင်း
        (request() က ဒါကို auto လုပ်ပေး — manual လိုအပ်ရင် ခေါ်သုံး)
        """
        self.current_reply = None
        self.timeout_timer = None
        self._fallback_urls.clear()

    # ------------------------------------------------------------------
    # Reply handling
    # ------------------------------------------------------------------
    def _on_reply_finished(self, reply: QNetworkReply) -> None:
        """
        QNetworkAccessManager.finished signal မှ ခေါ်မယ်
        ဒါပေမယ့် thumbnail reply မဟုတ်ရင် ignore လုပ်မယ်
        """
        reply_request_id = reply.property("thumbnail_request_id")
        if reply_request_id is None:
            # ဒီ reply က thumbnail service ရဲ့ မဟုတ် — ignore
            return

        # အရင် fetch ၏ reply ဖြစ်ပါက ignore
        if reply_request_id != self.current_request_id:
            reply.deleteLater()
            return

        # Timer ရပ်
        if self.timeout_timer is not None:
            try:
                if self.timeout_timer.isActive():
                    self.timeout_timer.stop()
            except Exception:
                pass
            self.timeout_timer = None

        # Network error ဖြစ်ပါက နောက် Fallback URL သို့ ပြောင်းဆွဲမည်
        if reply.error() != QNetworkReply.NetworkError.NoError:
            error_str = reply.errorString()
            print(f"Thumbnail URL failed ({reply.url().toString()}): {error_str}. Trying fallback...")
            self.current_reply = None
            reply.deleteLater()
            self._start_next_download(reply_request_id)
            return

        # Data ဖတ်
        try:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)

            if pixmap.isNull():
                print("Thumbnail download failed: invalid image data. Trying fallback...")
                self.current_reply = None
                reply.deleteLater()
                self._start_next_download(reply_request_id)
                return

            # Success
            self._fallback_urls.clear()
            self.thumbnail_ready.emit(pixmap)
            self.current_reply = None
            reply.deleteLater()

        except Exception as e:
            print(f"Error processing downloaded thumbnail: {e}")
            self.current_reply = None
            reply.deleteLater()
            self._start_next_download(reply_request_id)

    def _on_timeout(self, request_id: int) -> None:
        """ Timeout ဖြစ်ပါက Fallback သို့ ဆက်သွားမယ် """
        if request_id != self.current_request_id:
            return

        print("Thumbnail download timeout. Trying fallback...")

        # Reply abort
        if self.current_reply is not None:
            try:
                if not self.current_reply.isFinished():
                    self.current_reply.abort()
            except Exception:
                pass
            self.current_reply = None

        self.timeout_timer = None
        self._start_next_download(request_id)

    # ------------------------------------------------------------------
    # Scaling helper (View အတွက်)
    # ------------------------------------------------------------------
    @staticmethod
    def scale_for_label(pixmap: QPixmap) -> QPixmap:
        """ Label size (340x190) အတွက် scale """
        from PySide6.QtCore import Qt

        # KeepAspectRatioByExpanding ဖြင့် 340x190 ထက် မငယ်အောင် အပြည့်ဖြည့်
        scaled_pixmap = pixmap.scaled(
            ThumbnailService.SCALED_WIDTH,
            ThumbnailService.SCALED_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        # ပိုထွက်နေသော အစွန်းများကို Center Crop ပြုလုပ်၍ 340x190 ကွက်တိဖြတ်ယူ
        x = (scaled_pixmap.width() - ThumbnailService.SCALED_WIDTH) // 2
        y = (scaled_pixmap.height() - ThumbnailService.SCALED_HEIGHT) // 2

        return scaled_pixmap.copy(
            x,
            y,
            ThumbnailService.SCALED_WIDTH,
            ThumbnailService.SCALED_HEIGHT,
        )

    # ------------------------------------------------------------------
    # Save HD thumbnail (Save As dialog + requests)
    # ------------------------------------------------------------------
    @staticmethod
    def save_thumbnail_dialog(
        parent_widget,
        info: dict,
        default_dir: str,
        status_callback=None,
    ) -> str | None:
        """
        HD Thumbnail ကို Save As dialog ဖြင့်သိမ်းမယ်

        main.py ရဲ့ save_thumbnail() method ကို static utility
        အဖြစ် ပြောင်းထားတဲ့ (UI dialog လိုအပ်တာကြောင့် static မဖြစ်နိုင်
        ပေမယ့် parent_widget ကို လက်ခံနိုင်တယ်)။

        Args:
            parent_widget: QFileDialog ၏ parent
            info: yt-dlp info dict (self.info)
            default_dir: သိမ်းမယ့် folder
            status_callback: status bar သို့ message ပို့ရန် callback(str)

        Returns:
            Saved file path (cancel ဖြစ်ပါက None)
        """
        def status(msg: str):
            if status_callback:
                try:
                    status_callback(msg)
                except Exception:
                    pass
            else:
                print(msg)

        if not info:
            return None

        # 1. Best thumbnail URL
        thumbnail_urls = []
        thumbnails = info.get("thumbnails", [])
        if thumbnails:
            sorted_thumbs = sorted(
                [t for t in thumbnails if t.get("url")],
                key=lambda x: (x.get("width") or 0, x.get("height") or 0),
                reverse=True,
            )
            thumbnail_urls = [t.get("url") for t in sorted_thumbs if t.get("url")]

        video_id = info.get("id")
        if video_id:
            thumbnail_urls.extend([
                f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            ])

        if not thumbnail_urls:
            status("Thumbnail URL not found.")
            return None

        # 2. Default filename
        default_filename = "thumbnail"
        title = info.get("title", "")
        if title:
            clean_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
            if clean_title:
                default_filename = clean_title

        initial_path = os.path.join(default_dir, f"{default_filename}.webp")

        # 3. Save dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            parent_widget,
            "Save Thumbnail As",
            initial_path,
            "WebP Image (*.webp);;JPEG Image (*.jpg);;PNG Image (*.png)",
        )

        if not file_path:
            return None

        # Extension
        ext = ".webp"
        if "jpg" in selected_filter.lower() or "jpeg" in selected_filter.lower():
            ext = ".jpg"
        elif "png" in selected_filter.lower():
            ext = ".png"

        if not file_path.lower().endswith((".webp", ".jpg", ".jpeg", ".png")):
            file_path += ext

        # 4. Download + save (Loop through candidates until success)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }
        
        for t_url in thumbnail_urls:
            try:
                response = requests.get(t_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    status(f"Thumbnail saved to: {file_path}")
                    return file_path
            except Exception:
                continue

        status("Failed to download thumbnail image.")
        return None