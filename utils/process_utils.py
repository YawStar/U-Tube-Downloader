# -*- coding: utf-8 -*-
"""
Process ဆိုင်ရာ helper များ။

QProcess + psutil ပေါင်းစပ်ပြီး process tree (parent + children) ကို
OS မရွေး kill လုပ်ပေးသည်။ yt-dlp/ffmpeg ကဲ့သို့ child process များ
ကျန်ခဲ့ခြင်းမှ ကာကွယ်ရန် အသုံးပြုသည်။
"""
import psutil
from PySide6.QtCore import QProcess


def kill_process_tree(process_obj: QProcess) -> None:
    """
    QProcess ရဲ့ parent ရော child (yt-dlp/ffmpeg) အားလုံးကို kill လုပ်သည်။

    main.py ရဲ့ MainWindow.kill_process_tree() method ရဲ့ logic အတိုင်း
    အတိအကျ ကူးထားသည်။ Behavior မပြောင်းပါ။

    Args:
        process_obj: ရပ်တန့်လိုသော QProcess instance
    """
    # Process မ run နေရင် ဘာမှ မလုပ်ပါ
    if process_obj.state() != QProcess.ProcessState.Running:
        return

    pid = process_obj.processId()
    if pid <= 0:
        # PID မရရင် QProcess ၏ kill() ကိုပဲ ခေါ်
        process_obj.kill()
        return

    try:
        parent = psutil.Process(pid)

        # 🎯 Child processes (yt-dlp/ffmpeg) ကို အရင် kill
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                # ဒီ child က ပြီးသွားပြီ
                pass
            except psutil.AccessDenied:
                # Permission မရ — ကျော်လိုက်
                pass

        # Parent ကို kill
        try:
            parent.kill()
        except psutil.NoSuchProcess:
            pass

    except psutil.NoSuchProcess:
        # Process က ပြီးသွားပြီးဖြစ်နိုင် — QProcess ၏ kill() ကို ခေါ်
        process_obj.kill()
    except Exception as e:
        # psutil မှာ ဘာပဲဖြစ်ဖြစ် QProcess ၏ kill() ကို fallback
        print(f"kill_process_tree error: {e}")
        process_obj.kill()