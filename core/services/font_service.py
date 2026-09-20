# -*- coding: utf-8 -*-
"""
Font Service

Qt resource ထဲက custom fonts (.ttf) ကို App runtime မှာ load လုပ်ပေးသည်။

System install မလိုဘဲ font ကို သုံးနိုင်စေရန် QFontDatabase.addApplicationFont()
ကို အသုံးပြုသည်။

Features:
    • Resource path မှ font load
    • File path မှ font load
    • Load ပြီးသား font family names return

Usage:
    from core.services.font_service import FontService

    loaded = FontService.load_resource_fonts([
        ":/fonts/pyidaungsu.ttf"
    ])
    # loaded = {"Pyidaungsu": "Pyidaungsu"}
"""
from PySide6.QtGui import QFontDatabase


class FontService:
    """Custom fonts ကို App ထဲ load လုပ်သည်။"""

    # Load ပြီးသား fonts cache
    _loaded_fonts: dict = {}

    @classmethod
    def load_font(cls, font_path: str) -> list[str]:
        """
        Font file တစ်ခုကို load လုပ်သည်။

        Args:
            font_path: resource path (":/fonts/x.ttf") သို့မဟုတ် file path

        Returns:
            Font family names list (empty ဖြစ်နိုင် — fail)
        """
        if font_path in cls._loaded_fonts:
            return cls._loaded_fonts[font_path]

        font_id = QFontDatabase.addApplicationFont(font_path)

        if font_id == -1:
            # Load fail
            print(f"Font load failed: {font_path}")
            cls._loaded_fonts[font_path] = []
            return []

        families = QFontDatabase.applicationFontFamilies(font_id)
        cls._loaded_fonts[font_path] = families

        print(f"Font loaded: {font_path} → {families}")
        return families

    @classmethod
    def load_resource_fonts(cls, font_paths: list[str]) -> dict:
        """
        Resource fonts အများကြီးကို load လုပ်သည်။

        Args:
            font_paths: resource paths list

        Returns:
            {path: [family_names], ...}
        """
        result = {}
        for path in font_paths:
            result[path] = cls.load_font(path)
        return result

    @classmethod
    def get_family(cls, font_path: str, fallback: str = "") -> str:
        """
        Font family name ကို ရယူသည်။

        Args:
            font_path: resource path
            fallback: fail ဖြစ်ရင် ပြန်ပေးမည့် family name

        Returns:
            Font family name (သို့) fallback
        """
        families = cls.load_font(font_path)
        return families[0] if families else fallback

    @classmethod
    def is_loaded(cls, font_path: str) -> bool:
        """Font load ဖြစ်ပြီးလား စစ်"""
        return font_path in cls._loaded_fonts and bool(cls._loaded_fonts[font_path])