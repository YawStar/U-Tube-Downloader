import urllib.request
import json
from PySide6.QtCore import QThread, Signal
from utils.logger import get_logger

logger = get_logger(__name__)

class UpdateCheckerThread(QThread):
    # Signals: (is_update_available: bool, latest_version: str, release_notes: str, download_url: str)
    update_checked = Signal(bool, str, str, str)
    check_failed = Signal(str)

    def __init__(self, current_version: str, update_url: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version.lstrip('v')
        self.update_url = update_url

    def run(self):
        logger.info("Checking for application updates...")
        try:
            req = urllib.request.Request(
                self.update_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    # GitHub API Format: "tag_name": "v1.2.0"
                    latest_tag = data.get("tag_name", "0.0.0").lstrip('v')
                    release_notes = data.get("body", "No release notes provided.")
                    
                    # Release assets ထဲမှ exe/installer link သို့မဟုတ် html_url ကိုယူ
                    download_url = data.get("html_url", "")
                    if "assets" in data and len(data["assets"]) > 0:
                        download_url = data["assets"][0].get("browser_download_url", download_url)

                    # Version နှိုင်းယှဉ် (Simple Semantic Versioning logic)
                    is_available = self._is_newer_version(self.current_version, latest_tag)
                    
                    logger.info(f"Current: {self.current_version} | Latest: {latest_tag} | Update Available: {is_available}")
                    self.update_checked.emit(is_available, latest_tag, release_notes, download_url)
                else:
                    self.check_failed.emit(f"Server responded with status: {response.status}")

        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            self.check_failed.emit(str(e))

    def _is_newer_version(self, current: str, latest: str) -> bool:
        """ Version နှိုင်းယှဉ်ပေးတဲ့ Helper (e.g., "1.0.0" vs "1.0.1") """
        try:
            c_parts = [int(x) for x in current.split('.')]
            l_parts = [int(x) for x in latest.split('.')]
            return l_parts > c_parts
        except ValueError:
            return latest > current