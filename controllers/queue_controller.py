# -*- coding: utf-8 -*-
"""
Queue Controller

Playlist သို့မဟုတ် Multi-item Download Tasks များကို Queue စနစ်ဖြင့် တစ်ပုဒ်ပြီးတစ်ပုဒ်
(သို့မဟုတ် Sequential/Parallel) စီမံခန့်ခွဲပေးသည့် Controller Class
"""

from PySide6.QtCore import QObject, Signal
from controllers.download_controller import DownloadController


class DownloadTask:
    """ Queue ထဲရှိ Download Task တစ်ခု၏ Data Structure """
    def __init__(self, title: str, url: str, duration: str = ""):
        self.title = title
        self.url = url
        self.duration = duration
        self.status = "Pending"  # Pending, Downloading, Completed, Failed, Cancelled
        self.progress = 0
        self.status_text = "Waiting in queue..."


class QueueController(QObject):
    # Signals
    task_added = Signal(DownloadTask)
    task_updated = Signal(int, DownloadTask)  # index, task
    queue_started = Signal()
    queue_completed = Signal()
    all_tasks_finished = Signal()

    def __init__(self, download_controller: DownloadController, parent=None):
        super().__init__(parent)
        self.download_controller = download_controller
        self.tasks: list[DownloadTask] = []
        self.current_index = -1
        self._is_running = False
        self._is_cancelled = False
        self._settings = {}
        self._selected_format_id = None
        self._gui_overrides = {}
        self._is_windows = False

        # Download Controller Signals များနှင့် ချိတ်ဆက်ခြင်း
        self.download_controller.download_progress.connect(self._on_download_progress)
        self.download_controller.download_completed.connect(self._on_download_completed)
        self.download_controller.download_failed.connect(self._on_download_failed)
        self.download_controller.download_cancelled.connect(self._on_download_cancelled)

    def add_tasks(self, task_list: list[DownloadTask]):
        """ Tasks အများအပြားကို Queue ထဲသို့ ထည့်သွင်းမည် """
        for task in task_list:
            self.tasks.append(task)
            self.task_added.emit(task)

    def clear_queue(self):
        """ Queue ကို ရှင်းထုတ်မည် """
        if not self._is_running:
            self.tasks.clear()
            self.current_index = -1

    def start_queue(self, settings: dict, selected_format_id: str = None, gui_overrides: dict = None, is_windows: bool = False):
        """ Queue Process ကို စတင်မည် """
        if self._is_running or not self.tasks:
            return

        self._is_running = True
        self._is_cancelled = False  # ✨ စတင်ချိန်တွင် Cancel flag ကို False ပြန်လုပ်မည်
        self._settings = settings
        self._selected_format_id = selected_format_id
        self._gui_overrides = gui_overrides
        self._is_windows = is_windows
        self.current_index = -1

        self.queue_started.emit()
        self._process_next_task()

    def stop_queue(self):
        """ Queue ကို ရပ်တန့်မည် """
        self._is_running = False
        self._is_cancelled = True  # User Cancel ဖြစ်ကြောင်း မှတ်သားရန်
        if self.download_controller.is_running():
            self.download_controller.cancel()

    def is_running(self) -> bool:
        """ Queue တစ်ခုခု ဒေါင်းလုဒ်လုပ်နေဆဲ ဟုတ်မဟုတ် စစ်ဆေးရန် """
        return self._is_running

    def _process_next_task(self):
        """ နောက်တစ်ပုဒ်သို့ ကူးပြောင်း၍ ဒေါင်းလုဒ်စတင်မည် """
        if not self._is_running:
            return

        self.current_index += 1

        # Queue အားလုံးပြီးသွားပါက
        if self.current_index >= len(self.tasks):
            self._is_running = False
            self.all_tasks_finished.emit()
            return

        current_task = self.tasks[self.current_index]
        
        # မပြီးသေးသော Task (Pending) ဆိုမှ ဒေါင်းမည်
        if current_task.status in ["Completed", "Cancelled"]:
            self._process_next_task()
            return

        current_task.status = "Downloading"
        current_task.status_text = "Preparing..."
        self.task_updated.emit(self.current_index, current_task)

        # Download Controller ဖြင့် Download စတင်
        self.download_controller.start(
            url=current_task.url,
            settings=self._settings,
            selected_format_id=self._selected_format_id,
            gui_overrides=self._gui_overrides,
            is_windows=self._is_windows
        )

    def _on_download_progress(self, percent: int, status_text: str):
        if 0 <= self.current_index < len(self.tasks):
            task = self.tasks[self.current_index]
            task.progress = percent
            task.status_text = status_text
            self.task_updated.emit(self.current_index, task)

    def _on_download_completed(self, final_path: str):
        if 0 <= self.current_index < len(self.tasks):
            task = self.tasks[self.current_index]
            task.status = "Completed"
            task.progress = 100
            task.status_text = "Completed"
            self.task_updated.emit(self.current_index, task)
        self._process_next_task()

    def _on_download_failed(self, error_msg: str):
        if 0 <= self.current_index < len(self.tasks):
            task = self.tasks[self.current_index]
            task.status = "Failed"
            task.status_text = f"Error: {error_msg[:30]}"
            self.task_updated.emit(self.current_index, task)
        self._process_next_task()

    def _on_download_cancelled(self):
        if 0 <= self.current_index < len(self.tasks):
            task = self.tasks[self.current_index]
            task.status = "Cancelled"
            task.status_text = "Cancelled"
            self.task_updated.emit(self.current_index, task)
        self._is_running = False