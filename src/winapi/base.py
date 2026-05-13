import ctypes

from ctypes import wintypes

from . import utils


gdi32 = ctypes.windll.gdi32
user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
kernel32 = ctypes.windll.kernel32


_SendInput = user32.SendInput
_SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(utils.INPUT), wintypes.INT]
_SendInput.restype = wintypes.UINT


_GetMessageW = user32.GetMessageW
_GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
_GetMessageW.restype = wintypes.INT

_PeekMessageW = user32.PeekMessageW
_PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
_PeekMessageW.restype = wintypes.INT


# Mouse

_GetCursorPos = user32.GetCursorPos
_GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
_GetCursorPos.restype = wintypes.INT

_SystemParametersInfoW = user32.SystemParametersInfoW
_SystemParametersInfoW.argtypes = [wintypes.INT, wintypes.INT, ctypes.c_void_p, wintypes.INT]
_SystemParametersInfoW.restype = wintypes.INT

_GetProcessDpiAwareness = ctypes.windll.Shcore.GetProcessDpiAwareness
_GetProcessDpiAwareness.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.INT)]
_GetProcessDpiAwareness.restype = wintypes.INT

_SetProcessDpiAwareness = ctypes.windll.Shcore.SetProcessDpiAwareness
_SetProcessDpiAwareness.argtypes = [wintypes.INT]
_SetProcessDpiAwareness.restype = wintypes.INT


# Keyboard

_VkKeyScanW = user32.VkKeyScanW
_VkKeyScanW.argtypes = [wintypes.WCHAR]
_VkKeyScanW.restype = wintypes.SHORT

_GetAsyncKeyState = user32.GetAsyncKeyState
_GetAsyncKeyState.argtypes = [wintypes.INT]
_GetAsyncKeyState.restype = wintypes.SHORT


# Hotkey

_RegisterHotKey = user32.RegisterHotKey
_RegisterHotKey.argtypes = [wintypes.HWND, wintypes.INT, wintypes.UINT, wintypes.UINT]
_RegisterHotKey.restype = wintypes.INT

_UnregisterHotKey = user32.UnregisterHotKey
_UnregisterHotKey.argtypes = [wintypes.HWND, wintypes.INT]
_UnregisterHotKey.restype = wintypes.INT


# window

_FindWindowW = user32.FindWindowW
_FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
_FindWindowW.restype = wintypes.HWND

_GetForegroundWindow = user32.GetForegroundWindow
_GetForegroundWindow.restype = wintypes.HWND

_GetWindowTextW = user32.GetWindowTextW
_GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, wintypes.INT]
_GetWindowTextW.restype = wintypes.INT

_GetClassNameW = user32.GetClassNameW
_GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, wintypes.INT]
_GetClassNameW.restype = wintypes.INT

_IsWindowVisible = user32.IsWindowVisible
_IsWindowVisible.argtypes = [wintypes.HWND]
_IsWindowVisible.restype = wintypes.INT

_WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

_EnumWindows = user32.EnumWindows
_EnumWindows.argtypes = [_WNDENUMPROC, wintypes.LPARAM]
_EnumWindows.restype = wintypes.INT

_DwmGetWindowAttribute = dwmapi.DwmGetWindowAttribute
_DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
_DwmGetWindowAttribute.restype = wintypes.INT

_GetWindowDC = user32.GetWindowDC
_GetWindowDC.argtypes = [wintypes.HWND]
_GetWindowDC.restype = wintypes.HWND

_SetForegroundWindow = user32.SetForegroundWindow
_SetForegroundWindow.argtypes = [wintypes.HWND]
_SetForegroundWindow.restype = wintypes.INT

_MoveWindow = user32.MoveWindow
_MoveWindow.argtypes = [wintypes.HWND, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.BOOL]
_MoveWindow.restype = wintypes.INT


# graphic

_EnumDisplaySettingsW = user32.EnumDisplaySettingsW
_EnumDisplaySettingsW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(utils.DEVMODEW)]
_EnumDisplaySettingsW.restype = wintypes.INT

_CreateCompatibleDC = gdi32.CreateCompatibleDC
_CreateCompatibleDC.argtypes = [wintypes.HDC]
_CreateCompatibleDC.restype = wintypes.HDC

_CreateCompatibleBitmap = gdi32.CreateCompatibleBitmap
_CreateCompatibleBitmap.argtypes = [wintypes.HDC, wintypes.INT, wintypes.INT]
_CreateCompatibleBitmap.restype = wintypes.HANDLE

_BitBlt = gdi32.BitBlt
_BitBlt.argtypes = [wintypes.HDC, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.HDC, wintypes.INT, wintypes.INT, wintypes.DWORD]
_BitBlt.restype = wintypes.INT

_GetDIBits = gdi32.GetDIBits
_GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, wintypes.LPVOID, ctypes.POINTER(utils.BITMAPINFO), wintypes.UINT]
_GetDIBits.restype = wintypes.INT

_SelectObject = gdi32.SelectObject
_SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
_SelectObject.restype = wintypes.HANDLE