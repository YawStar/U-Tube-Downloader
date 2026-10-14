# -*- coding: utf-8 -*-
"""
Thumbnail Service (Qt-only version)

QNetworkAccessManager တစ်ခုတည်းဖြင့်
- Preview thumbnail (async, signal-based)
- HD thumbnail Save As (sync via QEventLoop)

နှစ်မျိုးလုံးကို လုပ်ဆောင်ပေးသည်။ `requests` မလိုအပ်တော့ပါ။

Proxy support:
- System proxy သုံးလိုပါက QNetworkProxyFactory.setUseSystemConfiguration(True)
  ကို QApplication ဖန်တီးပြီးချင်း ခေါ်ပါ။
- Manual proxy သုံးလိုပါက ThumbnailService.set_proxy(...) ကို ခေါ်ပါ။

Changelog (improvements):
- Timer တစ်ခုတည်း reuse (leak မဖြစ်တော့)
- HTTP status code ကို log မှာ ပြသ
- Save dialog မှာ QPixmap.save() ဖြင့် format conversion (WebP → JPG/PNG)
- thumbnail_cancelled signal ကို သင့်လျော်စွာ emit
- logging ကို utils.logger ဖြင့် သုံး
- _build_fallback_urls မှာ ?v=VIDEO_ID pattern ပါ ဖမ်း
- reply deleteLater logic ပိုစိတ်ချရ
"""

import os
import re

from PySide6.QtCore import (
    QObject,
    Signal,
    QUrl,
    QTimer,
    QEventLoop,
    Qt,
)
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply,
    QNetworkProxy,
    QNetworkProxyFactory,
)
from PySide6.QtWidgets import QFileDialog

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:  # logger မရှိရင် fallback
    import logging
    logger = logging.getLogger(__name__)


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
    thumbnail_cancelled = Signal()             # request ID mismatch / cancel

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------
    DEFAULT_TIMEOUT_MS = 10000   # 10 seconds (preview)
    SAVE_TIMEOUT_MS = 15000      # Save As sync download
    SCALED_WIDTH = 340
    SCALED_HEIGHT = 190

    # ⭐ User-Agent ကို constant အဖြစ် ထား (req တိုင်း ပြန်ဖန်တီးစရာ မလို)
    USER_AGENT = b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # ⭐ YouTube video ID pattern (၁၁ လုံး)
    _YT_ID_PATTERN = re.compile(r"([a-zA-Z0-9_-]{11})")

    # ------------------------------------------------------------------
    # Class-level network manager (save_thumbnail_dialog static အတွက်)
    # ------------------------------------------------------------------
    _manager: QNetworkAccessManager | None = None

    # ------------------------------------------------------------------
    # Proxy helpers (class method — app စတင်ချိန် ခေါ်ရန်)
    # ------------------------------------------------------------------
    @classmethod
    def use_system_proxy(cls, enable: bool = True) -> None:
        """
        Qt ကို system proxy configuration (Windows Internet Settings /
        macOS Network Settings / env var) သုံးခိုင်း

        QApplication ဖန်တီးပြီးချင်း၊ QNetworkAccessManager မဖန်တီးခင်
        ခေါ်ရပါမယ်။
        """
        QNetworkProxyFactory.setUseSystemConfiguration(enable)

    @classmethod
    def set_proxy(
        cls,
        host: str | None = None,
        port: int = 0,
        proxy_type: QNetworkProxy.ProxyType = QNetworkProxy.ProxyType.HttpProxy,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        """
        Manual proxy သတ်မှတ်

        Args:
            host: proxy host (None ဖြစ်ပါက NoProxy သို့ ပြန်ထား)
            port: proxy port
            proxy_type: HttpProxy / Socks5Proxy / ...
            user / password: authentication လိုအပ်ပါက
        """
        if cls._manager is None:
            raise RuntimeError(
                "ThumbnailService ကို မဆောက်ရသေးပါ။ "
                "MainWindow မှာ ThumbnailService(...) ကို အရင် ဖန်တီးပါ။"
            )

        if not host:
            cls._manager.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
            return

        proxy = QNetworkProxy()
        proxy.setType(proxy_type)
        proxy.setHostName(host)
        proxy.setPort(port)
        if user:
            proxy.setUser(user)
        if password:
            proxy.setPassword(password)
        cls._manager.setProxy(proxy)

    # ------------------------------------------------------------------
    # __init__
    # ------------------------------------------------------------------
    def __init__(self, network_manager: QNetworkAccessManager, parent=None):
        """
        Args:
            network_manager: MainWindow မှ ဖန်တီးထားသော QNetworkAccessManager
            parent: Qt parent (MainWindow)
        """
        super().__init__(parent)
        self.network_manager = network_manager
        ThumbnailService._manager = network_manager  # static save အတွက် သိမ်း

        # ⭐ System proxy ကို auto enable (QApplication ဖန်တီးပြီးသားဖြစ်ရမယ်)
        try:
            QNetworkProxyFactory.setUseSystemConfiguration(True)
        except Exception as e:
            logger.debug(f"System proxy auto-enable failed: {e}")

        self.network_manager.finished.connect(self._on_reply_finished)

        # State
        self.current_request_id = 0
        self.current_reply: QNetworkReply | None = None
        self._fallback_urls: list[str] = []

        # ⭐ Timer တစ်ခုတည်း — reuse လုပ် (leak မဖြစ်တော့)
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._on_timeout)

        # ⭐ ဘယ် request အတွက် timeout လဲ သိမ်း
        self._timeout_request_id: int = 0

    # ------------------------------------------------------------------
    # Request lifecycle (Preview)
    # ------------------------------------------------------------------
    def request(self, url: str, request_id: int | None = None) -> int:
        """
        Thumbnail download စတင် (preview အတွက် — async)

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

        # အရင် reply ရှိရင် abort (cancel signal ကို ဒီနေရာမှာ မ emit)
        self._cancel_internal()

        if not url:
            self.thumbnail_failed.emit("Empty thumbnail URL")
            return request_id

        # Build Fallback URLs list
        self._fallback_urls = self._build_fallback_urls(url)
        self._start_next_download(request_id)
        return request_id

    def _build_fallback_urls(self, primary_url: str) -> list[str]:
        """primary_url 404 ဖြစ်ပါက အစားထိုးသုံးရန် fallback list ပြုလုပ်"""
        urls = [primary_url]
        vid = self._extract_youtube_video_id(primary_url)

        if vid:
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

    @classmethod
    def _extract_youtube_video_id(cls, url: str) -> str | None:
        """
        YouTube video ID ကို URL မှ ထုတ်ယူ

        Patterns:
            i.ytimg.com/vi/VIDEO_ID/...
            i.ytimg.com/vi_webp/VIDEO_ID/...
            ...?v=VIDEO_ID
        """
        if not url:
            return None

        # Pattern 1: /vi/VIDEO_ID/ or /vi_webp/VIDEO_ID/
        m = re.search(r"/(?:vi_webp|vi)/([a-zA-Z0-9_-]{11})(?:/|$|\?)", url)
        if m:
            return m.group(1)

        # Pattern 2: ?v=VIDEO_ID or &v=VIDEO_ID
        m = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})(?:[&\s]|$)", url)
        if m:
            return m.group(1)

        return None

    def _start_next_download(self, request_id: int) -> None:
        """List ထဲမှ နောက် URL တစ်ခုကို စတင် ဒေါင်းလုဒ်လုပ်"""
        if not self._fallback_urls:
            self.thumbnail_failed.emit(
                "All thumbnail fallback URLs failed (404/Error)"
            )
            return

        current_url = self._fallback_urls.pop(0)

        try:
            req = QNetworkRequest(QUrl(str(current_url)))
            req.setRawHeader(b"User-Agent", self.USER_AGENT)
            req.setAttribute(
                QNetworkRequest.Attribute.RedirectPolicyAttribute,
                QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
            )

            reply = self.network_manager.get(req)
            reply.setProperty("thumbnail_request_id", request_id)
            self.current_reply = reply

            # ⭐ Timer ကို restart (တစ်ခုတည်း reuse)
            self._timeout_request_id = request_id
            self.timeout_timer.start(self.DEFAULT_TIMEOUT_MS)

        except Exception as e:
            logger.error(f"Thumbnail request error: {e}")
            self.thumbnail_failed.emit(f"Request error: {e}")

    def cancel(self) -> None:
        """လက်ရှိ download ကိုရပ် (cancel signal emit မယ်)"""
        self._cancel_internal()
        self.thumbnail_cancelled.emit()

    def _cancel_internal(self) -> None:
        """
        အတွင်းပိုင်း cancel (signal မပို့)

        request အသစ်စတဲ့အခါ အရင် reply ကို abort လုပ်ဖို့ သုံး —
        user က "cancel" မဟုတ်တဲ့အတွက် signal မပို့သင့်။
        """
        self._fallback_urls.clear()

        if self.timeout_timer is not None and self.timeout_timer.isActive():
            self.timeout_timer.stop()

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

        ⭐ Timer ကို stop() ခေါ်ဖို့ မမေ့
        """
        if self.timeout_timer is not None and self.timeout_timer.isActive():
            self.timeout_timer.stop()

        self.current_reply = None
        self._fallback_urls.clear()
        self._timeout_request_id = 0

    # ------------------------------------------------------------------
    # Reply handling (Preview)
    # ------------------------------------------------------------------
    def _on_reply_finished(self, reply: QNetworkReply) -> None:
        """QNetworkAccessManager.finished signal မှ ခေါ်မယ်"""
        reply_request_id = reply.property("thumbnail_request_id")

        # ဒီ reply က တခြား service ရဲ့ ဖြစ်နိုင် — ဒါဆို ဒီ service က မကိုင်တွယ်ဘူး
        # (တခြား service က သူ့ဟာသူ deleteLater လုပ်မယ်)
        if reply_request_id is None:
            return

        # int cast (property က string ဖြစ်နိုင်)
        try:
            reply_request_id = int(reply_request_id)
        except (TypeError, ValueError):
            reply.deleteLater()
            return

        # အရင် fetch ၏ reply ဖြစ်ပါက ignore + delete
        if reply_request_id != self.current_request_id:
            reply.deleteLater()
            return

        # Timer ရပ်
        if self.timeout_timer is not None and self.timeout_timer.isActive():
            self.timeout_timer.stop()

        # Network error ဖြစ်ပါက နောက် Fallback URL သို့ ပြောင်းဆွဲမည်
        if reply.error() != QNetworkReply.NetworkError.NoError:
            error_str = reply.errorString()
            http_status = reply.attribute(
                QNetworkRequest.Attribute.HttpStatusCodeAttribute
            )
            logger.debug(
                f"Thumbnail failed (HTTP {http_status}): "
                f"{reply.url().toString()} — {error_str}. Trying fallback..."
            )
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
                logger.debug(
                    "Thumbnail data invalid (not an image). Trying fallback..."
                )
                self.current_reply = None
                reply.deleteLater()
                self._start_next_download(reply_request_id)
                return

            # Success
            self._fallback_urls.clear()
            self.current_reply = None
            reply.deleteLater()
            self.thumbnail_ready.emit(pixmap)

        except Exception as e:
            logger.error(f"Error processing downloaded thumbnail: {e}")
            self.current_reply = None
            reply.deleteLater()
            self._start_next_download(reply_request_id)

    def _on_timeout(self) -> None:
        """
        Timer timeout ဖြစ်ပါက Fallback သို့ ဆက်သွားမယ်

        ⭐ Timer တစ်ခုတည်း reuse ဖြစ်တဲ့အတွက် parameter မလိုတော့ —
        _timeout_request_id ကို စစ်
        """
        request_id = self._timeout_request_id

        if request_id != self.current_request_id:
            return

        logger.debug("Thumbnail download timeout. Trying fallback...")

        if self.current_reply is not None:
            try:
                if not self.current_reply.isFinished():
                    self.current_reply.abort()
            except Exception:
                pass
            self.current_reply = None

        self._start_next_download(request_id)

    # ------------------------------------------------------------------
    # Scaling helper (View အတွက်)
    # ------------------------------------------------------------------
    @staticmethod
    def scale_for_label(pixmap: QPixmap) -> QPixmap:
        """Label size (340x190) အတွက် scale + center crop"""
        scaled_pixmap = pixmap.scaled(
            ThumbnailService.SCALED_WIDTH,
            ThumbnailService.SCALED_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        x = max(0, (scaled_pixmap.width() - ThumbnailService.SCALED_WIDTH) // 2)
        y = max(0, (scaled_pixmap.height() - ThumbnailService.SCALED_HEIGHT) // 2)

        return scaled_pixmap.copy(
            x,
            y,
            ThumbnailService.SCALED_WIDTH,
            ThumbnailService.SCALED_HEIGHT,
        )

    # ------------------------------------------------------------------
    # Internal: synchronous download via QEventLoop (Qt-only)
    # ------------------------------------------------------------------
    @classmethod
    def _sync_download(cls, url: str, timeout_ms: int) -> bytes | None:
        """
        Qt ဖြင့် sync download (QEventLoop သုံး)

        Returns:
            bytes (success) / None (fail)
        """
        if cls._manager is None:
            logger.warning("_sync_download: network manager not initialized")
            return None

        req = QNetworkRequest(QUrl(str(url)))
        req.setRawHeader(b"User-Agent", cls.USER_AGENT)
        req.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )

        reply = cls._manager.get(req)

        loop = QEventLoop()
        reply.finished.connect(loop.quit)

        # Timeout guard
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(timeout_ms)

        loop.exec()

        # Cleanup timer
        if timer.isActive():
            timer.stop()

        data: bytes | None = None
        if (
            reply.error() == QNetworkReply.NetworkError.NoError
            and reply.isFinished()
        ):
            raw = reply.readAll()
            data = bytes(raw.data())

        reply.deleteLater()
        return data

    # ------------------------------------------------------------------
    # Save HD thumbnail (Save As dialog — Qt-only)
    # ------------------------------------------------------------------
    @classmethod
    def save_thumbnail_dialog(
        cls,
        parent_widget,
        info: dict,
        default_dir: str,
        status_callback=None,
    ) -> str | None:
        """
        HD Thumbnail ကို Save As dialog ဖြင့်သိမ်းမယ် (Qt-only)

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
            logger.info(msg)

        if not info:
            return None

        # 1. Best thumbnail URL candidates
        thumbnail_urls: list[str] = []
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
                f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            ])

        # Deduplicate (order preserve)
        seen: set[str] = set()
        thumbnail_urls = [
            u for u in thumbnail_urls if not (u in seen or seen.add(u))
        ]

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

        # Extension ကို filter မှ ဆုံးဖြတ်
        ext = ".webp"
        if "jpg" in selected_filter.lower() or "jpeg" in selected_filter.lower():
            ext = ".jpg"
        elif "png" in selected_filter.lower():
            ext = ".png"

        if not file_path.lower().endswith((".webp", ".jpg", ".jpeg", ".png")):
            file_path += ext

        # ⭐ Qt save format
        qt_format = "WEBP"
        if ext == ".jpg":
            qt_format = "JPEG"
        elif ext == ".png":
            qt_format = "PNG"

        # 4. Qt-only sync download loop through candidates
        for t_url in thumbnail_urls:
            data = cls._sync_download(t_url, cls.SAVE_TIMEOUT_MS)
            if not data:
                continue

            # Verify image validity
            pixmap = QPixmap()
            if not pixmap.loadFromData(data):
                continue

            # ⭐ QPixmap.save() ဖြင့် format conversion (WebP data → JPG/PNG)
            try:
                if pixmap.save(file_path, qt_format):
                    status(f"Thumbnail saved to: {file_path}")
                    return file_path
                else:
                    status(f"Failed to save image to {file_path}")
                    return None
            except Exception as e:
                status(f"Failed to write file: {e}")
                return None

        status("Failed to download thumbnail image.")
        return None