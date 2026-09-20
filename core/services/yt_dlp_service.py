# -*- coding: utf-8 -*-
"""
yt-dlp Command Builder Service

main.py ထဲက:
    • on_get_info_clicked()  →  args = [...] (fetch info)
    • on_download_clicked()  →  args = [...] (download)

နှစ်ခုလုံးမှာ ထပ်ခါတလဲလဲ ရေးနေရတဲ့ yt-dlp args ဆောက်တဲ့ logic ကို
ဒီ file ထဲ စုစည်းထားသည်။

⚠️ ဒီ class က PySide6/Qt ကို လုံးဝ မမှီခိုပါ။
    Pure Python — Unit Test လုပ်ရလွယ်သည်။
"""
import os
from typing import Any


class YtDlpService:
    """
    yt-dlp executable အတွက် command-line arguments များ ဆောက်ပေးသည်။

    Attributes:
        tools_dir: yt-dlp / ffmpeg / deno တည်ရှိရာ folder (TPT_DIR)
        bin_ext:   ".exe" (Windows) သို့မဟုတ် "" (Linux/macOS)
        manual_cookies_path: manual cookies ကို ခေတ္တသိမ်းမည့် file path
    """

    # ------------------------------------------------------------------
    # Progress template — main.py မှ တိုက်ရိုက် ကူး (format တူညီ)
    # ------------------------------------------------------------------
    PROGRESS_TEMPLATE = (
        'download:[download]%(progress._percent_str)s|'
        '%(progress._total_bytes_str)s|'
        '%(progress._speed_str)s|'
        '%(progress._eta_str)s|'
        '%(progress._downloaded_bytes_str)s|'
        '%(progress._elapsed_str)s|'
        '%(progress._total_bytes_str)s'
    )

    def __init__(
        self,
        tools_dir: str,
        bin_ext: str = "",
        manual_cookies_path: str = "",
    ):
        self.tools_dir = tools_dir
        self.bin_ext = bin_ext
        self.manual_cookies_path = manual_cookies_path

    # ------------------------------------------------------------------
    # Executable Paths
    # ------------------------------------------------------------------
    @property
    def yt_dlp_path(self) -> str:
        """yt-dlp executable ၏ full path"""
        return os.path.join(self.tools_dir, f"yt-dlp{self.bin_ext}")

    @property
    def ffmpeg_path(self) -> str:
        """ffmpeg executable ၏ full path"""
        return os.path.join(self.tools_dir, f"ffmpeg{self.bin_ext}")

    @property
    def deno_path(self) -> str:
        """deno executable ၏ full path"""
        return os.path.join(self.tools_dir, f"deno{self.bin_ext}")

    # ------------------------------------------------------------------
    # Dependency Check
    # ------------------------------------------------------------------
    def check_necessary_files(self) -> tuple[int, list[str]]:
        """
        လိုအပ်သော binary ဖိုင်များ ရှိ/မရှိ စစ်ဆေးသည်။

        main.py ရဲ့ MainWindow.check_necessary_files() ရဲ့
        logic ကို ကွက်တိ ကူးထားသည်။

        Returns:
            (missing_count, missing_names)
            missing_count == 0 → အားလုံး ရှိပြီ
        """
        checks = {
            "yt-dlp": self.yt_dlp_path,
            "ffmpeg": self.ffmpeg_path,
            "deno":   self.deno_path,
        }
        missing = [name for name, path in checks.items() if not os.path.exists(path)]
        return len(missing), missing

    # ------------------------------------------------------------------
    # FETCH INFO args
    # ------------------------------------------------------------------
    def build_info_args(self, url: str, settings: dict[str, Any]) -> list[str]:
        """
        yt-dlp --dump-json အတွက် args ဆောက်သည်။

        main.py → on_get_info_clicked() ထဲက args = [...] ကို
        ကွက်တိ အစားထိုးသည်။

        Args:
            url: ရှာဖွေမည့် URL
            settings: config.json မှ ဖတ်ထားသော settings

        Returns:
            yt-dlp command-line args list
        """
        args: list[str] = [
            "--quiet",
            "--no-warnings",
            "--no-playlist",
            "--ignore-config",
            "--socket-timeout", "15",
            "--retries", "3",
            "--extractor-retries", "2",
            "--dump-json",
        ]

        # Cookies (main.py ရဲ့ if/elif block ကို service method ဖြင့် အစားထိုး)
        args += self._build_cookies_args(settings)

        # Proxy
        args += self._build_proxy_args(settings)

        # URL — နောက်ဆုံးမှာ ထည့်
        args.append(url)
        return args

    # ------------------------------------------------------------------
    # DOWNLOAD args
    # ------------------------------------------------------------------
    def build_download_args(
        self,
        url: str,
        settings: dict[str, Any],
        selected_format_id: str | None = None,
        gui_overrides: dict[str, bool] | None = None,
        is_windows: bool = False,
    ) -> list[str]:
        """
        yt-dlp download အတွက် args ဆောက်သည်။

        main.py → on_download_clicked() ထဲက args = [...] ကို
        ကွက်တိ အစားထိုးသည်။

        Args:
            url: ဒေါင်းလုဒ်လုပ်မည့် URL
            settings: config.json မှ ဖတ်ထားသော settings
            selected_format_id: FormatDialog မှ ရွေးထားသော ID
                                (ဥပမာ "137+140" သို့မဟုတ် "22")
                                None ဖြစ်ပါက format-sort သုံးမည်
            gui_overrides: Checkbox များမှ override လုပ်လိုသော တန်ဖိုးများ
                           key: "embed_thumbnail", "embed_chapters",
                                "embed_subtitles", "embed_metadata", "use_mtime"
            is_windows: True ဖြစ်ပါက --windows-filenames ထည့်မည်

        Returns:
            yt-dlp command-line args list
        """
        gui_overrides = gui_overrides or {}

        def get(key: str, default=None):
            """GUI override ကို settings ထက် ဦးစားပေး"""
            if key in gui_overrides:
                return gui_overrides[key]
            return settings.get(key, default)

        # ---- Config မှ တန်ဖိုးများ ----
        download_path       = settings.get("download_path", "")
        use_speed_limit     = settings.get("use_speed_limit", False)
        speed_limit_val     = settings.get("speed_limit_val", 500)

        resolution          = settings.get("resolution", 1080)
        video_ext           = settings.get("video_ext", "mp4")
        audio_ext           = settings.get("audio_ext", "m4a")
        video_codec         = settings.get("video_codec", "h264")
        audio_codec         = settings.get("audio_codec", "aac")

        # GUI override ဦးစားပေး
        embed_thumbnail     = get("embed_thumbnail", False)
        embed_subtitle      = get("embed_subtitles", False)
        embed_chapters      = get("embed_chapters", False)
        embed_metadata      = get("embed_metadata", False)
        use_mtime           = get("use_mtime", True)
        force_overwrite     = get("force_overwrite", False)

        # ---- Base args ----
        args: list[str] = [
            "--no-playlist",
            "--no-warnings",
            "--ignore-config",
            "--js-runtimes", "deno",
            "--progress-template", self.PROGRESS_TEMPLATE,
        ]

        # ---- ForceOverwrite options ----
        if force_overwrite:
            args.append("--force-overwrite")
        else:
            args.append("--continue")

        # ---- Embed options (main.py ရဲ့ if block တွေနဲ့ တူ) ----
        if embed_chapters:
            args.append("--embed-chapters")
        if embed_subtitle:
            args.append("--embed-subs")
        if embed_thumbnail:
            args.append("--embed-thumbnail")
        if embed_metadata:
            args.append("--embed-metadata")

        # Live chat ပိတ် (main.py နဲ့ တူ)
        args += ["--compat-options", "no-live-chat"]

        # ---- Speed limit ----
        if use_speed_limit:
            args += ["--limit-rate", f"{speed_limit_val}K"]

        # ---- Cookies ----
        args += self._build_cookies_args(settings)

        # ---- Proxy ----
        args += self._build_proxy_args(settings)

        # ---- Encoding ----
        args += ["--encoding", "UTF-8"]

        # ---- Format selection ----
        if selected_format_id:
            # FormatDialog မှ ရွေးထားသော ID (ဥပမာ "137+140")
            args += ["--format", selected_format_id]
        else:
            # set default values
            if resolution == "none": resolution = 1080
            if video_ext == "none": video_ext = "mp4"
            if video_codec == "none": video_codec = "h264"
            if audio_ext == "none": audio_ext = "m4a"
            if audio_codec == "none": audio_codec = "aac"

            # Default format-sort string (main.py နဲ့ တူ)
            format_sort = (
                f"res:{resolution},vext:{video_ext},aext:{audio_ext},"
                f"fps,vcodec:{video_codec},acodec:{audio_codec}"
            )
            args += ["--format-sort", format_sort]

        # ---- FFmpeg location ----
        args += ["--ffmpeg-location", self.ffmpeg_path]

        # ---- Download path ----
        args += ["--paths", download_path]

        # ---- Windows filename safe ----
        if is_windows:
            args.append("--windows-filenames")

        # ---- mtime ----
        args.append("--mtime" if use_mtime else "--no-mtime")

        # ---- Output template (main.py နဲ့ တူ) ----
        args += ["--output", "%(title).200s.%(ext)s"]

        # ---- URL ---- (အမြဲ နောက်ဆုံး)
        args.append(url)
        return args

    # ------------------------------------------------------------------
    # Private: Cookies
    # ------------------------------------------------------------------
    def _build_cookies_args(self, settings: dict[str, Any]) -> list[str]:
        """
        Cookies type အလိုက် yt-dlp args ပြန်ပေးသည်။

        main.py ရဲ့ on_get_info_clicked() နဲ့ on_download_clicked()
        နှစ်ခုလုံးထဲက cookies if/elif block ကို စုစည်းထားသည်။

        Type များ:
            "file"    → --cookies <path> (ဖိုင်ရှိမှ ထည့်)
            "browser" → --cookies-from-browser <name.lower()>
            "manual"  → manual_cookies_path ဖိုင်ဆောက်ပြီး --cookies ထည့်
            အခြား    → ဘာမှ မထည့်
        """
        cookies_type = settings.get("cookies_type", "")

        if cookies_type == "file":
            cookies_path = settings.get("cookies_path", "")
            if cookies_path and os.path.exists(cookies_path):
                return ["--cookies", cookies_path]
            return []

        if cookies_type == "browser":
            # main.py က .lower() လုပ်တယ်
            browser_name = str(
                settings.get("cookies_browser_name", "chrome")
            ).lower()
            return ["--cookies-from-browser", browser_name]

        if cookies_type == "manual":
            manual_text = settings.get("cookies_manual_text", "")
            if manual_text and self.manual_cookies_path:
                try:
                    # main.py ရဲ့ logic အတိုင်း — အရင်ဖိုင်ရှိရင် ဖျက်
                    if os.path.exists(self.manual_cookies_path):
                        os.remove(self.manual_cookies_path)
                    # ဖိုင်အသစ် ရေး (UTF-8)
                    with open(
                        self.manual_cookies_path, "w", encoding="utf-8"
                    ) as f:
                        f.write(manual_text)
                    return ["--cookies", self.manual_cookies_path]
                except OSError as e:
                    print(f"Manual cookies save failed: {e}")
                    return []
            return []

        # "none" သို့မဟုတ် အခြား — ဘာမှ မထည့်
        return []

    # ------------------------------------------------------------------
    # Private: Proxy
    # ------------------------------------------------------------------
    def _build_proxy_args(self, settings: dict[str, Any]) -> list[str]:
        """Proxy settings ရှိပါက --proxy arg ပြန်ပေးသည်။"""
        if not settings.get("use_proxy", False):
            return []
        host = settings.get("proxy_host", "127.0.0.1")
        port = settings.get("proxy_port", 10808)
        return ["--proxy", f"{host}:{port}"]