from __future__ import annotations

import os
import PIL
import sys
import time
import uuid
import queue
import ctypes
import itertools
import threading

from PIL import Image
from ctypes import wintypes

from . import base
from . import utils


PRECISE_TIME = True
MINIUM_INTERVAL = 0.001
SET_DPI_AWARENESS = True


if SET_DPI_AWARENESS: base._SetProcessDpiAwareness(2)


def cooldown(interval):
    def inner(func):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            time.sleep(interval)
        return wrapper
    return inner


class ClassProperty:
    def __init__(self, func):
        self.func = func

    
    def __get__(self, instance, owner):
        return self.func(owner)


class VirtualKeyCodePair():
    def __init__(self, vk_code: int | list[int] | tuple[int] = None):
        if vk_code is None:
            self.vk_pair = ()

        elif isinstance(vk_code, (tuple, list)):
            self.vk_pair = tuple(set(vk_code))

        elif isinstance(vk_code, int):
            self.vk_pair = (vk_code,)
    

    def __add__(self, other):
        if isinstance(other, VirtualKeyCodePair):
            self.vk_pair += other.vk_pair

        elif isinstance(other, (list, tuple)):
            self.vk_pair += tuple(other)

        elif isinstance(other, int):
            self.vk_pair += other

        self.vk_pair = tuple(set(self.vk_pair))
        return self
    

    def __getitem__(self, key: int):
        return self.vk_pair[key]
    

    def __len__(self):
        return len(self.vk_pair)
    

    def __iter__(self):
        return iter(self.vk_pair)
    

    def __reversed__(self):
        return reversed(self.vk_pair)


class VirtualKeyCodes():
    def __init__(self, vk_codes: list[VirtualKeyCodePair] = None):
        if vk_codes is None: self.vk_codes = []
        else: self.vk_codes = vk_codes
    

    def __getitem__(self, key: int):
        return self.vk_codes[key]


    def __iter__(self):
        return iter(self.vk_codes)
    

    def __len__(self):
        return len(self.vk_codes)
    

    def append(self, object: VirtualKeyCodePair):
        self.vk_codes.append(object)


    @staticmethod
    def flatten(vk_codes):
        return list(set(itertools.chain.from_iterable(
            vk_code if isinstance(vk_code, list) else [vk_code]
            for vk_code in vk_codes
        )))
    

    @staticmethod
    def get(keys: str | list[str], flat: bool = False) -> list:
        def _convert(key):
            if key.lower() in utils.virtual_key_code_map.keys():
                result = utils.virtual_key_code_map[key.lower()]
            
            else: 
                result = base._VkKeyScanW(key)

            modifier_code = 0
            match result >> 8:
                case 0: return VirtualKeyCodePair(vk_code=result & 0xFF)

                case 1: modifier_code = 0x10
                case 2: modifier_code = 0x11
                case 4: modifier_code = 0x12

            return VirtualKeyCodePair(vk_code=(modifier_code, result & 0xFF))
        
        if keys is None:
            return VirtualKeyCodes()
        
        keys = keys if isinstance(keys, list) else [keys]
        vk_codes = VirtualKeyCodes()

        for key in keys:
            if "+" in key:
                pair = VirtualKeyCodePair()
                for k in key.split("+"): pair += _convert(key=k)
                vk_codes.append(pair)

            elif key.lower() in utils.virtual_key_code_map.keys():
                vk_codes.append(
                    VirtualKeyCodePair(
                        vk_code=utils.virtual_key_code_map[key.lower()]
                    )
                )

            elif len(key) > 1:
                for k in key: 
                    vk_codes.append(_convert(key=k))

            else: vk_codes.append(_convert(key=key))

        if flat:
            return list(set(itertools.chain.from_iterable(
                vk_code.vk_pair for vk_code in vk_codes
            )))

        return vk_codes


class Mouse():
    @ClassProperty
    def pos(cls) -> tuple[int]:
        return Mouse.get_pos()


    @ClassProperty
    def speed(cls) -> int:
        return Mouse.get_speed()
    

    @ClassProperty
    def accleration(cls) -> tuple[int]:
        return Mouse.get_accleration()


    @staticmethod
    def get_pos() -> tuple[int]:
        point = wintypes.POINT()
        result = base._GetCursorPos(ctypes.byref(point))

        if result:
            return (point.x, point.y)
        

    @staticmethod
    def get_speed() -> int:
        speed = wintypes.INT()
        result = base._SystemParametersInfoW(
            utils.SPI_GETMOUSESPEED,
            0,
            ctypes.byref(speed),
            0
        )

        if result:
            return speed.value
        
    
    @staticmethod
    def get_accleration() -> tuple[int]:
        threshold = (wintypes.INT * 3)()
        result = base._SystemParametersInfoW(
            utils.SPI_GETMOUSE,
            0,
            ctypes.byref(threshold),
            0
        )

        if result:
            return (threshold[0], threshold[1], threshold[2])
        
    
    @staticmethod
    def set_speed(speed: int):
        result = base._SystemParametersInfoW(
            utils.SPI_SETMOUSESPEED,
            0,
            ctypes.c_void_p(speed),
            utils.SPIF_UPDATEINIFILE | utils.SPIF_SENDCHANGE
        )

    
    @staticmethod
    def set_accleration(threshold: tuple[int]):
        threshold = (wintypes.INT * 3)(*threshold)

        result = base._SystemParametersInfoW(
            utils.SPI_SETMOUSE,
            0,
            threshold,
            utils.SPIF_UPDATEINIFILE | utils.SPIF_SENDCHANGE
        )


    @staticmethod
    def _mouse_event(**kwargs):
        input = utils.INPUT(type=ctypes.c_ulong(utils.INPUT_MOUSE))
        input.mi = utils.MOUSEINPUT(
            dx=kwargs["x"] if "x" in kwargs else 0,
            dy=kwargs["y"] if "y" in kwargs else 0,
            mouseData=kwargs["mouse_data"] if "mouse_data" in kwargs else 0,
            dwFlags=kwargs["event"],
            time=0
        )

        base._SendInput(1, ctypes.byref(input), ctypes.sizeof(utils.INPUT))


    def adjust_mouse(speed: int, threshold: tuple[int]):
        def inner(func):
            def wrapper(*args, **kwargs):
                original_speed = Mouse.get_speed()
                original_accleration = Mouse.get_accleration()

                Mouse.set_speed(speed=speed)
                Mouse.set_accleration(threshold=threshold)

                func(*args, **kwargs)

                Mouse.set_speed(speed=original_speed)
                Mouse.set_accleration(threshold=original_accleration)

            return wrapper
        return inner         


    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def move_to(
        point: tuple[int],
        duration: float = MINIUM_INTERVAL, 
        step: int = None
    ):
        (x, y) = point
        (now_x, now_y) = Mouse.get_pos()
        dx, dy = x - now_x, y - now_y
        (w, h) = System.get_screen_size()

        if dx == 0 and dy == 0:
            return

        if duration == 0 or step == 1:
            Mouse._mouse_event(
                event=utils.MOUSEEVENTF_MOVE | utils.MOUSEEVENTF_ABSOLUTE,
                x=round(x / (w - 1) * 65536),
                y=round(y / (h - 1) * 65536)
            )
            return
        
        if step is None:
            step = max(abs(dx), abs(dy))
            dt = duration / step
        
        start_time = time.perf_counter()
        for i in range(1, step + 1):
            norm_x = round((now_x + dx / step * i) / (w - 1) * 65535)
            norm_y = round((now_y + dy / step * i) / (h - 1) * 65535)

            Mouse._mouse_event(
                event=utils.MOUSEEVENTF_MOVE | utils.MOUSEEVENTF_ABSOLUTE,
                x=norm_x, 
                y=norm_y
            )
            
            if PRECISE_TIME:
                remain_time = start_time + dt * i - time.perf_counter()
                if remain_time > MINIUM_INTERVAL * 1.5:
                    time.sleep(MINIUM_INTERVAL)
                while time.perf_counter() < start_time + dt * i:
                    pass

            else: time.sleep(dt)


    @staticmethod
    @adjust_mouse(speed=10, threshold=(0, 0, 0))
    @cooldown(MINIUM_INTERVAL)
    def move(
        delta: tuple[int],
        duration: float = MINIUM_INTERVAL, 
        step: int = None
    ):
        (dx, dy) = delta
        (now_x, now_y) = Mouse.get_pos()
        x, y = now_x + dx, now_y + dy

        Mouse.move_to((x, y), duration=duration, step=step)


    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def click(button: str | int = "left", duration: float = MINIUM_INTERVAL):
        if str(button) in ["left", "l", 0]:
            Mouse._mouse_event(event=utils.MOUSEEVENTF_LEFTDOWN)
            time.sleep(duration)
            Mouse._mouse_event(event=utils.MOUSEEVENTF_LEFTUP)

        if str(button) in ["right", "r", 1]:
            Mouse._mouse_event(event=utils.MOUSEEVENTF_RIGHTDOWN)
            time.sleep(duration)
            Mouse._mouse_event(event=utils.MOUSEEVENTF_RIGHTUP)


    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def clickdown(button: str | int = "left"):
        if str(button) in ["left", "l", 0]:
            Mouse._mouse_event(event=utils.MOUSEEVENTF_LEFTDOWN)

        if str(button) in ["right", "r", 1]:
            Mouse._mouse_event(event=utils.MOUSEEVENTF_RIGHTDOWN)


    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def clickup(button: str | int = "left"):
        if str(button) in ["left", "l", 0]:
            Mouse._mouse_event(event=utils.MOUSEEVENTF_LEFTUP)

        if str(button) in ["right", "r", 1]:
            Mouse._mouse_event(event=utils.MOUSEEVENTF_RIGHTUP)


    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def drag_to(
        point: tuple[int],
        button: str | int = "left",
        duration:float = MINIUM_INTERVAL, 
        step: int = None
    ):
        if str(button) in ["left", "l", 0]:
            Mouse.clickdown(button="left")
            Mouse.move_to(point=point, duration=duration, step=step)
            Mouse.clickup(button="left")

        if str(button) in ["right", "r", 1]:
            Mouse.clickdown(button="right")
            Mouse.move_to(point=point, duration=duration, step=step)
            Mouse.clickup(button="right")
        

    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def drag(
        delta: tuple[int],
        button: str | int = "left",
        duration: float = MINIUM_INTERVAL, 
        step:int = None
    ):
        if str(button) in ["left", "l", 0]:
            Mouse.clickdown(button="left")
            Mouse.move(delta=delta, duration=duration, step=step)
            Mouse.clickup(button="left")

        if str(button) in ["right", "r", 1]:
            Mouse.clickdown(button="right")
            Mouse.move(delta=delta, duration=duration, step=step)
            Mouse.clickup(button="right")


    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def scroll(wheel: int, duration: float = MINIUM_INTERVAL, step: int = None):
        if duration == 0 or step == 1:
            Mouse._mouse_event(event=utils.MOUSEEVENTF_WHEEL, mouse_data=wheel)
            return
        
        if step is None:
            step = abs(wheel)
            dt = duration / step

            if dt < MINIUM_INTERVAL:
                Mouse._mouse_event(event=utils.MOUSEEVENTF_WHEEL, mouse_data=wheel)
                return
    
        moved_wheel, start_time = 0, time.perf_counter()
        for i in range(1, step + 1):
            count = 1 if i == step else step / i
            step_wheel = int(wheel / count) - moved_wheel
            moved_wheel += step_wheel

            Mouse._mouse_event(event=utils.MOUSEEVENTF_WHEEL, mouse_data=step_wheel)
            
            if PRECISE_TIME:
                remain_time = start_time + dt * i - time.perf_counter()
                if remain_time > MINIUM_INTERVAL * 1.5:
                    time.sleep(MINIUM_INTERVAL)
                while time.perf_counter() < start_time + dt * i:
                    pass

            else: time.sleep(dt)


class Keyboard():
    @staticmethod
    def _keyboard_event(**kwargs):
        if kwargs["virtual_key_code"] is not None:
            input = utils.INPUT(type=ctypes.c_ulong(utils.INPUT_KEYBOARD))
            input.ki = utils.KEYBDINPUT(
                wVk=kwargs["virtual_key_code"],
                wScan=0,
                dwFlags=kwargs["event"],
                time=0
            )

            base._SendInput(1, ctypes.byref(input), ctypes.sizeof(utils.INPUT))


    @staticmethod
    def is_down(keys: str | list[str]) -> bool:
        vk_codes = VirtualKeyCodes.get(keys=keys, flat=True)
        
        result = any([base._GetAsyncKeyState(vk_code) < 0 for vk_code in vk_codes])
        return result
    

    @staticmethod
    def is_up(keys: str | list[str]) -> bool:
        vk_codes = VirtualKeyCodes.get(keys=keys, flat=True)
        
        result = any([base._GetAsyncKeyState(vk_code) > 0 for vk_code in vk_codes])
        return result

    
    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def keydown(keys: str | list[str]):
        vk_codes = VirtualKeyCodes.get(keys=keys, flat=True)

        for vk_code in vk_codes:
            Keyboard._keyboard_event(
                event=utils.KEYEVENTF_KEYDOWN,
                virtual_key_code=vk_code
            )


    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def keyup(keys: str | list[str]):
        vk_codes = VirtualKeyCodes.get(keys=keys, flat=True)

        for vk_code in vk_codes:
            Keyboard._keyboard_event(
                event=utils.KEYEVENTF_KEYUP, 
                virtual_key_code=vk_code
            )


    @staticmethod
    @cooldown(MINIUM_INTERVAL)
    def press(keys: str | list[str], duration: float = MINIUM_INTERVAL):
        vk_codes = VirtualKeyCodes.get(keys=keys)
        dt = duration / len(vk_codes)

        for vk_code in vk_codes:
            if isinstance(vk_code, VirtualKeyCodePair):
                for vkc in vk_code:
                    Keyboard._keyboard_event(
                        event=utils.KEYEVENTF_KEYDOWN,
                        virtual_key_code=vkc
                    )

                time.sleep(dt)

                for vkc in reversed(vk_code):
                    Keyboard._keyboard_event(
                        event=utils.KEYEVENTF_KEYUP, 
                        virtual_key_code=vkc
                    )

            else: 
                Keyboard._keyboard_event(
                    event=utils.KEYEVENTF_KEYDOWN,
                    virtual_key_code=vkc
                )
                time.sleep(dt)
                Keyboard._keyboard_event(
                    event=utils.KEYEVENTF_KEYUP, 
                    virtual_key_code=vkc
                )
    

class Hotkey():
    def __init__(self):
        self.running = True
        self.hotkeys = []
        self.event_queue = queue.Queue()


    def add(self, keys: str | list[str], callback: function = None):
        keys = keys if isinstance(keys, list) else [keys]
        vk_codes = VirtualKeyCodes.get(keys=keys)

        for key, vk_code in zip(keys, vk_codes):
            self.hotkeys.append({
                "key": key,
                "vk_code": vk_code,
                "callback": callback,
                "id": uuid.uuid4().int & 0xFFFFFFFF
            })


    def detect(self):
        for hotkey in self.hotkeys:
            modifier = utils.MOD_NOREPEAT

            if len(hotkey["vk_code"]) > 1:
                for mvkc in hotkey["vk_code"][0:-1]:
                    match mvkc:
                        case 0X10: modifier |= utils.MOD_SHIFT
                        case 0X11: modifier |= utils.MOD_CONTROL
                        case 0X12: modifier |= utils.MOD_ALT
            
            result = base._RegisterHotKey(None, hotkey["id"], modifier, hotkey["vk_code"][-1])

        while self.running:
            try:
                msg = wintypes.MSG()
                result = base._PeekMessageW(ctypes.byref(msg), None, 0, 0, 1)

                if result and msg.message == utils.WM_HOTKEY:
                    recieve_id = msg.wParam & 0xFFFFFFFF
                    self.event_queue.put(recieve_id)

                    for hotkey in self.hotkeys:
                        if hotkey["id"] == recieve_id and callable(hotkey["callback"]):
                            hotkey["callback"](key=hotkey["key"])
            
                time.sleep(MINIUM_INTERVAL * 100)

            except Exception: break

        for hotkey in self.hotkeys:
            result = base._UnregisterHotKey(None, hotkey["id"])


    def get_event_queue(self):
        try:
            return self.event_queue.get_nowait()
        
        except queue.Empty:
            return None


    def start(self):
        self.running = True
        thread = threading.Thread(target=self.detect)
        thread.start()


    def stop(self):
        self.running = False


class Window():
    def __init__(self, handle: int):
        self.handle = handle
        self.name = Window.get_name(self.handle)
        self.class_name = Window.get_class_name(self.handle)
        self.size = Window.get_size(self.handle)


    @staticmethod
    def is_visible(window: Window | int) -> bool:
        handle = window.handle if isinstance(window, Window) else window

        if not bool(base._IsWindowVisible(handle)):
            return False
        
        if not Window.get_name(handle):
            return False
        
        is_cloaked = wintypes.ULONG(0)
        base._DwmGetWindowAttribute(
            handle,
            utils.DWMWA_CLOAKED,
            ctypes.byref(is_cloaked),
            ctypes.sizeof(is_cloaked)
        )

        if is_cloaked.value != 0:
            return False
        
        return True


    @staticmethod
    def find(
        window_name: str = None,
        class_name: str = None
    ) -> int:
        result = base._FindWindowW(class_name, window_name)

        if result: return Window(result)


    @staticmethod
    def find_all(
        window_name: str = None,
        class_name: str = None
    ) -> list[int]:
        windows = []

        def _callback(handle, lparam):
            if window_name and Window.get_name(window=handle) != window_name:
                return True
            
            elif class_name and Window.get_class_name(window=handle) != class_name:
                return True

            if Window.is_visible(window=handle):
                windows.append(Window(handle))

            return True
        
        _EnumWindowsProc = base._WNDENUMPROC(_callback)
        base._EnumWindows(_EnumWindowsProc, 0)

        return windows
    

    @staticmethod
    def get_foreground():
        result = base._GetForegroundWindow()

        if result: return Window(result)
    

    @staticmethod
    def get_name(window: Window | int) -> str:
        handle = window.handle if isinstance(window, Window) else window

        buffer = ctypes.create_unicode_buffer(256)
        result = base._GetWindowTextW(handle, buffer, ctypes.sizeof(buffer))

        if result:
            return buffer.value
        

    @staticmethod
    def get_class_name(window: Window | int) -> str:
        handle = window.handle if isinstance(window, Window) else window

        buffer = ctypes.create_unicode_buffer(256)
        result = base._GetClassNameW(handle, buffer, ctypes.sizeof(buffer))

        if result:
            return buffer.value

    
    @staticmethod
    def get_size(window: Window | int) -> tuple[int]:
        handle = window.handle if isinstance(window, Window) else window

        rect = wintypes.RECT()
        result = base._DwmGetWindowAttribute(
            handle,
            utils.DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect),
            ctypes.sizeof(rect)
        )

        if result == 0:
            return (
                rect.left,
                rect.top,
                rect.right - rect.left,
                rect.bottom - rect.top
            )
        
    
    @staticmethod
    def set_foreground(window: Window | int):
        handle = window.handle if isinstance(window, Window) else window

        result = base._SetForegroundWindow(handle)


    @staticmethod
    def resize(
        window: Window | int,
        size: tuple[int]
    ):
        handle = window.handle if isinstance(window, Window) else window

        (x, y, w, h) = size
        result = base._MoveWindow(handle, x, y, w, h, True)


class Graphic():
    @staticmethod
    def screenshot(
        window: Window | int,
        size: tuple[int] = None,
        save: bool = False,
        filepath: str = None
    ) -> PIL.Image.Image:
        if window:
            handle = window.handle if isinstance(window, Window) else window
            (x, y, w, h) = Window.get_size(window=handle)

        elif size:
            (x, y, w, h) = size

        else:
            x, y = 0, 0
            (w, h) = System.get_screen_size()

        if filepath is None:
            filepath = f"screenshot/{time.time_ns()}.png"

        device_context = base._GetWindowDC(0)
        memory_device_context = base._CreateCompatibleDC(device_context)

        bitmap_info = utils.BITMAPINFO()
        bitmap_info.bmiHeader.biSize = ctypes.sizeof(utils.BITMAPINFOHEADER)
        bitmap_info.bmiHeader.biWidth = w
        bitmap_info.bmiHeader.biHeight = -h
        bitmap_info.bmiHeader.biPlanes = 1
        bitmap_info.bmiHeader.biBitCount = 32
        bitmap_info.bmiHeader.biCompression = 0
        bitmap_info.bmiHeader.biClrUsed = 0
        bitmap_info.bmiHeader.biClrImportant = 0

        data = ctypes.create_string_buffer(w * h * 4)

        bitmap = base._CreateCompatibleBitmap(device_context, w, h)
        base._SelectObject(memory_device_context, bitmap)
        
        base._BitBlt(
            memory_device_context, 
            0, 0, w, h, 
            device_context, 
            x, y, 
            utils.SRCCOPY | utils.CAPTUREBLT
        )
        base._GetDIBits(
            memory_device_context, 
            bitmap, 
            0,
            h, 
            data, 
            bitmap_info, 
            utils.DIB_RGB_COLORS
        )

        raw = bytearray(data)
        raw[3::4] = b"\xff" * (w * h)

        image = Image.frombytes("RGBA", (w, h), bytes(raw), "raw", "BGRA")
        
        if save:
            dirpath = os.path.dirname(filepath)
            if not os.path.isdir(dirpath): os.mkdir(dirpath)

            image.save(filepath)

        return image
    

class System():
    @ClassProperty
    def screen_size(cls) -> tuple[int]:
        return System.get_screen_size()

    @staticmethod
    def get_screen_size() -> tuple[int]:
        devmode = utils.DEVMODEW()
        devmode.dmSize = ctypes.sizeof(utils.DEVMODEW)
        
        result = base._EnumDisplaySettingsW(None, -1, ctypes.byref(devmode))

        return (devmode.dmPelsWidth, devmode.dmPelsHeight)


class UAC():
    @staticmethod
    def runas_admin():
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable, 
                " ".join(sys.argv),
                None, 
                1
            )