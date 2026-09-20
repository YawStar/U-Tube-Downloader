import ctypes
from ctypes import wintypes
from enum import IntEnum
from pathlib import Path
from PySide6.QtGui import QIcon

# =========================================================
# Windows DLL
# =========================================================

ole32 = ctypes.OleDLL("ole32")
user32 = ctypes.WinDLL("user32")


# =========================================================
# HRESULT
# =========================================================

S_OK = 0
S_FALSE = 1

COINIT_APARTMENTTHREADED = 0x2
CLSCTX_INPROC_SERVER = 0x1


# =========================================================
# Taskbar Progress State
# =========================================================

class TBPF(IntEnum):
    """
    ITaskbarList3 Taskbar Progress State
    """

    NO_PROGRESS = 0x00000000
    INDETERMINATE = 0x00000001
    NORMAL = 0x00000002
    ERROR = 0x00000004
    PAUSED = 0x00000008


# =========================================================
# GUID Structure
# =========================================================

class GUID(ctypes.Structure):

    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


# =========================================================
# CLSID_TaskbarList
#
# 56FDF344-FD6D-11D0-958A-006097C9A090
# =========================================================

CLSID_TaskbarList = GUID(
    0x56FDF344,
    0xFD6D,
    0x11D0,
    (ctypes.c_ubyte * 8)(
        0x95,
        0x8A,
        0x00,
        0x60,
        0x97,
        0xC9,
        0xA0,
        0x90,
    ),
)


# =========================================================
# IID_ITaskbarList3
#
# EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF
# =========================================================

IID_ITaskbarList3 = GUID(
    0xEA1AFB91,
    0x9E28,
    0x4B86,
    (ctypes.c_ubyte * 8)(
        0x90,
        0xE9,
        0x9E,
        0x9F,
        0x8A,
        0x5E,
        0xEF,
        0xAF,
    ),
)


# =========================================================
# ITaskbarList3
# =========================================================

class ITaskbarList3:

    def __init__(self, hwnd):

        self.hwnd = wintypes.HWND(hwnd)

        self._ptr = ctypes.c_void_p()
        self._vtable = None
        self._com_initialized = False

        # -------------------------------------------------
        # Initialize COM
        # -------------------------------------------------

        hr = ole32.CoInitializeEx(
            None,
            COINIT_APARTMENTTHREADED,
        )

        if hr not in (S_OK, S_FALSE):

            raise OSError(
                f"CoInitializeEx failed: "
                f"HRESULT=0x{hr & 0xFFFFFFFF:08X}"
            )

        self._com_initialized = True

        # -------------------------------------------------
        # Create TaskbarList COM object
        # -------------------------------------------------

        hr = ole32.CoCreateInstance(
            ctypes.byref(CLSID_TaskbarList),
            None,
            CLSCTX_INPROC_SERVER,
            ctypes.byref(IID_ITaskbarList3),
            ctypes.byref(self._ptr),
        )

        if hr != S_OK:

            self.close()

            raise OSError(
                f"CoCreateInstance failed: "
                f"HRESULT=0x{hr & 0xFFFFFFFF:08X}"
            )

        if not self._ptr:

            self.close()

            raise RuntimeError(
                "ITaskbarList3 returned NULL pointer"
            )

        # -------------------------------------------------
        # VTable
        # -------------------------------------------------

        self._vtable = ctypes.cast(
            self._ptr,
            ctypes.POINTER(
                ctypes.POINTER(ctypes.c_void_p)
            ),
        )[0]

        # -------------------------------------------------
        # ITaskbarList.HrInit
        #
        # VTable:
        # 0 QueryInterface
        # 1 AddRef
        # 2 Release
        # 3 HrInit
        # -------------------------------------------------

        self._HrInit = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
        )(self._vtable[3])

        hr = self._HrInit(self._ptr)

        if hr != S_OK:

            self.close()

            raise OSError(
                f"ITaskbarList3.HrInit failed: "
                f"HRESULT=0x{hr & 0xFFFFFFFF:08X}"
            )

        # -------------------------------------------------
        # SetProgressValue
        #
        # ITaskbarList3 VTable index = 9
        # -------------------------------------------------

        self._SetProgressValue = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
            wintypes.HWND,
            ctypes.c_ulonglong,
            ctypes.c_ulonglong,
        )(self._vtable[9])

        # -------------------------------------------------
        # SetProgressState
        #
        # ITaskbarList3 VTable index = 10
        # -------------------------------------------------

        self._SetProgressState = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
            wintypes.HWND,
            ctypes.c_uint,
        )(self._vtable[10])

        # -------------------------------------------------
        # SetOverlayIcon
        #
        # ITaskbarList3 VTable index = 18
        #
        # HRESULT SetOverlayIcon(
        #     HWND hwnd,
        #     HICON hIcon,
        #     LPCWSTR pszDescription
        # );
        # -------------------------------------------------

        self._SetOverlayIcon = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
            wintypes.HWND,
            wintypes.HICON,
            wintypes.LPCWSTR,
        )(self._vtable[18])


    # =====================================================
    # Progress
    # =====================================================

    def set_progress(self, value, maximum=100):

        if not self._ptr:
            return False

        value = max(0, int(value))
        maximum = max(1, int(maximum))

        hr = self._SetProgressValue(
            self._ptr,
            self.hwnd,
            value,
            maximum,
        )

        return hr == S_OK


    # =====================================================
    # Progress State
    # =====================================================

    def set_state(self, state: TBPF):

        if not self._ptr:
            return False

        hr = self._SetProgressState(
            self._ptr,
            self.hwnd,
            int(state),
        )

        return hr == S_OK


    # =====================================================
    # Clear Progress
    # =====================================================

    def clear_progress(self):

        return self.set_state(
            TBPF.NO_PROGRESS
        )


    # =====================================================
    # Overlay Icon
    # =====================================================

    def set_overlay_icon(
        self,
        icon_input,
        description="",
    ):
        if not self._ptr:
            return False

        hicon = None
        should_destroy = False

        # -------------------------------------------------
        # 1. QIcon ဖြင့် ဝင်လာပါက HICON အဖြစ် ပြောင်းလဲခြင်း
        # -------------------------------------------------
        if isinstance(icon_input, QIcon):
            # Taskbar Overlay Icon standard size ဖြစ်သော 16x16 pixels QPixmap ထုတ်ယူမည်
            pixmap = icon_input.pixmap(16, 16)
            
            # Pixmap မှတစ်ဆင့် HICON (Win32 Icon Handle) သို့ ပြောင်းမည်
            # PySide6 တွင် pixmap.toImage().toHICON() ဖြင့် တိုက်ရိုက် ပြောင်းနိုင်သည်
            hicon = pixmap.toImage().toHICON()
            
            # PySide6 မှ ဖန်တီးပေးသော HICON Memory ကို ပြန်ရှင်းပေးရန်အတွက်
            should_destroy = True

        # -------------------------------------------------
        # 2. String သို့မဟုတ် Path ဖြင့် ဝင်လာပါက Disk မှ ဖတ်မည်
        # -------------------------------------------------
        elif isinstance(icon_input, (str, Path)):
            icon_path = Path(icon_input)
            if not icon_path.exists():
                raise FileNotFoundError(f"Overlay icon not found: {icon_path}")

            LR_LOADFROMFILE = 0x00000010
            LR_DEFAULTSIZE = 0x00000040
            IMAGE_ICON = 1

            user32.LoadImageW.restype = wintypes.HANDLE
            hicon = user32.LoadImageW(
                None,
                str(icon_path),
                IMAGE_ICON,
                0,
                0,
                LR_LOADFROMFILE | LR_DEFAULTSIZE,
            )
            should_destroy = True

        if not hicon:
            return False

        # -------------------------------------------------
        # 3. Taskbar Overlay သို့ HICON ပေးပို့ခြင်း
        # -------------------------------------------------
        hr = self._SetOverlayIcon(
            self._ptr,
            self.hwnd,
            wintypes.HICON(hicon),
            description,
        )

        # -------------------------------------------------
        # 4. ဖန်တီးထားသော HICON ကို Release လုပ်ပေးခြင်း
        # -------------------------------------------------
        if should_destroy:
            user32.DestroyIcon(wintypes.HICON(hicon))

        return hr == S_OK

    def set_overlay_icon1(
        self,
        icon_path,
        description="",
    ):

        if not self._ptr:
            return False

        icon_path = Path(icon_path)

        if not icon_path.exists():
            raise FileNotFoundError(
                f"Overlay icon not found: {icon_path}"
            )

        # -------------------------------------------------
        # Load .ico
        # -------------------------------------------------

        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE = 0x00000040

        IMAGE_ICON = 1

        user32.LoadImageW.restype = wintypes.HANDLE

        hicon = user32.LoadImageW(
            None,
            str(icon_path),
            IMAGE_ICON,
            0,
            0,
            LR_LOADFROMFILE | LR_DEFAULTSIZE,
        )

        if not hicon:

            raise ctypes.WinError(
                ctypes.get_last_error()
            )

        # -------------------------------------------------
        # Set Overlay
        # -------------------------------------------------

        hr = self._SetOverlayIcon(
            self._ptr,
            self.hwnd,
            wintypes.HICON(hicon),
            description,
        )

        # -------------------------------------------------
        # Release our HICON
        # -------------------------------------------------

        user32.DestroyIcon(
            wintypes.HICON(hicon)
        )

        return hr == S_OK


    # =====================================================
    # Remove Overlay Icon
    # =====================================================

    def clear_overlay_icon(self):

        if not self._ptr:
            return False

        hr = self._SetOverlayIcon(
            self._ptr,
            self.hwnd,
            None,
            None,
        )

        return hr == S_OK


    # =====================================================
    # Downloading
    # =====================================================

    def downloading(
        self,
        value,
        maximum=100,
        icon_path=None,
    ):

        self.set_state(
            TBPF.NORMAL
        )

        self.set_progress(
            value,
            maximum,
        )

        if icon_path:
            self.set_overlay_icon(
                icon_path,
                "Downloading",
            )


    # =====================================================
    # Paused
    # =====================================================

    def paused(
        self,
        value=None,
        maximum=100,
        icon_path=None,
    ):

        self.set_state(
            TBPF.PAUSED
        )

        if value is not None:

            self.set_progress(
                value,
                maximum,
            )

        if icon_path:
            self.set_overlay_icon(
                icon_path,
                "Paused",
            )


    # =====================================================
    # Error
    # =====================================================

    def error(
        self,
        value=None,
        maximum=100,
        icon_path=None,
    ):

        self.set_state(
            TBPF.ERROR
        )

        if value is not None:

            self.set_progress(
                value,
                maximum,
            )

        if icon_path:

            self.set_overlay_icon(
                icon_path,
                "Error",
            )


    # =====================================================
    # Indeterminate / Loading
    # =====================================================

    def indeterminate(
        self,
        icon_path=None,
    ):

        self.set_state(
            TBPF.INDETERMINATE
        )

        if icon_path:

            self.set_overlay_icon(
                icon_path,
                "Loading",
            )


    # =====================================================
    # Completed
    # =====================================================

    def completed(
        self,
        icon_path=None,
    ):

        self.set_state(
            TBPF.NO_PROGRESS
        )

        if icon_path:

            self.set_overlay_icon(
                icon_path,
                "Completed",
            )


    # =====================================================
    # Reset Everything
    # =====================================================

    def reset(self):

        self.clear_progress()
        self.clear_overlay_icon()


    # =====================================================
    # Release COM
    # =====================================================

    def close(self):

        if self._ptr:

            try:

                release = ctypes.WINFUNCTYPE(
                    ctypes.c_ulong,
                    ctypes.c_void_p,
                )(self._vtable[2])

                release(self._ptr)

            except Exception:
                pass

            self._ptr = None
            self._vtable = None

        if self._com_initialized:

            ole32.CoUninitialize()

            self._com_initialized = False


    # =====================================================
    # Destructor
    # =====================================================

    def __del__(self):

        try:
            self.close()
        except Exception:
            pass