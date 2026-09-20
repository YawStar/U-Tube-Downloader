# -*- coding: utf-8 -*-
"""
File Opener Service

OS default file manager ကို အသုံးပြုပြီး folder/file ဖွင့်ပေးသည်။

main.py ထဲက ဒီ logic တွေကို စုစည်းထားသည်:
    • open_downloaded_folder() — Windows COM + macOS + Linux

Features:
    • Windows: Explorer ရှိပြီးသားထဲမှာ file ကို highlight (အသစ်မပွင့်)
    • macOS: Finder reveal (-R)
    • Linux: DBus ShowItems (GNOME/KDE) + xdg-open fallback
"""
import os
import platform
import subprocess


class FileOpenerService:
    """OS file manager ဖြင့် folder/file ဖွင့်ပေးသည်။"""

    # ------------------------------------------------------------------
    # Open folder only
    # ------------------------------------------------------------------
    @staticmethod
    def open_folder(folder_path: str) -> bool:
        """
        Folder ကို OS default file manager ဖြင့် ဖွင့်သည်။

        Args:
            folder_path: ဖွင့်လိုသော folder path

        Returns:
            True — ဖွင့်အောင်မြင်ပြီ
            False — path မရှိ / error
        """
        if not folder_path:
            return False

        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
            except OSError as e:
                print(f"Cannot create folder: {e}")
                return False

        current_os = platform.system()

        try:
            if current_os == "Windows":
                os.startfile(os.path.abspath(folder_path))
            elif current_os == "Darwin":
                subprocess.run(["open", folder_path], check=False)
            else:
                subprocess.run(["xdg-open", folder_path], check=False)
            return True
        except Exception as e:
            print(f"open_folder error: {e}")
            return False

    # ------------------------------------------------------------------
    # Open folder + select file
    # ------------------------------------------------------------------
    @staticmethod
    def open_folder_and_select_file(file_path: str) -> bool:
        """
        File တည်ရှိရာ folder ကို ဖွင့်ပြီး file ကို highlight လုပ်သည်။

        Windows: Shell.Application COM ဖြင့် ရှိပြီးသား Explorer
                 ထဲမှာ file ကို select (အသစ်မပွင့်)
        macOS:   open -R (Finder reveal)
        Linux:   DBus ShowItems (Nautilus/Dolphin) + xdg-open fallback

        Args:
            file_path: highlight လုပ်လိုသော file path

        Returns:
            True — အောင်မြင်ပြီ
            False — error
        """
        if not file_path or not os.path.exists(file_path):
            return False

        full_file_path = os.path.abspath(file_path)
        target_folder = os.path.dirname(full_file_path)
        current_os = platform.system()

        # -----------------------------------------------------------------
        # WINDOWS
        # -----------------------------------------------------------------
        if current_os == "Windows":
            return FileOpenerService._open_on_windows(
                full_file_path, target_folder
            )

        # -----------------------------------------------------------------
        # macOS
        # -----------------------------------------------------------------
        elif current_os == "Darwin":
            try:
                subprocess.run(
                    ["open", "-R", full_file_path],
                    check=False,
                )
                return True
            except Exception as e:
                print(f"macOS open error: {e}")
                return False

        # -----------------------------------------------------------------
        # LINUX
        # -----------------------------------------------------------------
        elif current_os == "Linux":
            try:
                subprocess.run(
                    [
                        "dbus-send",
                        "--session",
                        "--print-reply",
                        "--dest=org.freedesktop.FileManager1",
                        "/org/freedesktop/FileManager1",
                        "org.freedesktop.FileManager1.ShowItems",
                        f"array:string:file://{full_file_path}",
                        "string:",
                    ],
                    check=True,
                )
                return True
            except Exception:
                # Fallback: folder ဖွင့်
                try:
                    subprocess.run(
                        ["xdg-open", target_folder],
                        check=False,
                    )
                    return True
                except Exception as e:
                    print(f"Linux open error: {e}")
                    return False

        return False

    # ------------------------------------------------------------------
    # Windows helper
    # ------------------------------------------------------------------
    @staticmethod
    def _open_on_windows(full_file_path: str, target_folder: str) -> bool:
        """
        Windows Explorer ကို ရှိပြီးသား window ထဲမှာ file highlight
        လုပ်ရန် ကြိုးစားသည်။ မရရင် explorer /select ဖြင့် အသစ်ဖွင့်။

        main.py ရဲ့ open_downloaded_folder() logic ကို ကွက်တိ ကူးထားသည်။
        """
        try:
            import win32com.client
            import win32gui
        except ImportError:
            # win32com မရရင် explorer /select ဖြင့် fallback
            try:
                subprocess.run(
                    [r"explorer.exe", "/select,", full_file_path],
                    check=False,
                )
                return True
            except Exception as e:
                print(f"explorer fallback error: {e}")
                return False

        found_existing = False

        try:
            # Shell.Application COM
            shell = win32com.client.Dispatch("Shell.Application")
            target_folder_object = shell.Namespace(target_folder)

            if target_folder_object:
                # ပွင့်နေတဲ့ Explorer windows အားလုံးကို ရှာ
                for w in shell.Windows():
                    if w.Name not in ["File Explorer", "Windows Explorer"]:
                        continue

                    try:
                        window_folder = w.Document.Folder
                        window_path = os.path.abspath(window_folder.Self.Path)

                        # Folder တူမတူ စစ် (basename နှင့် full path နှစ်မျိုး)
                        if (
                            window_path.lower() == target_folder.lower()
                            or os.path.basename(window_path).lower()
                            == os.path.basename(target_folder).lower()
                        ):
                            hwnd = w.HWND

                            # Minimize ဖြစ်နေရင် restore
                            if win32gui.IsIconic(hwnd):
                                win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE

                            win32gui.ShowWindow(hwnd, 5)  # SW_SHOW
                            win32gui.SetForegroundWindow(hwnd)

                            # File select (29 = SVSI_SELECT)
                            folder_items = window_folder.Items()
                            for item in folder_items:
                                if (
                                    os.path.basename(full_file_path).lower()
                                    == item.Name.lower()
                                ):
                                    w.Document.SelectItem(item, 29)
                                    break

                            found_existing = True
                            break
                    except Exception:
                        continue

            # ရှိပြီးသား Explorer မတွေ့ရင် အသစ်ဖွင့်
            if not found_existing:
                subprocess.run(
                    [r"explorer.exe", "/select,", full_file_path],
                    check=False,
                )

            return True

        except Exception as e:
            print(f"Advanced COM Error: {e}")
            try:
                subprocess.run(
                    [r"explorer.exe", "/select,", full_file_path],
                    check=False,
                )
                return True
            except Exception as e2:
                print(f"explorer fallback error: {e2}")
                return False