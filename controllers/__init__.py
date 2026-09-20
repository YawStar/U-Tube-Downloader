# -*- coding: utf-8 -*-
"""
Controller layer — QProcess logic နှင့် state management။

Controller တွေက View (MainWindow) ကို Signal ဖြင့် notify လုပ်သည်။
View က Controller ရဲ့ method ကို ခေါ်ပြီး request လုပ်သည်။
"""
from controllers.fetch_controller import FetchController
from controllers.download_controller import DownloadController

__all__ = [
    "FetchController",
    "DownloadController",
]