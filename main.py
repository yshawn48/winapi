import time

from src.winapi import *

if __name__ == "__main__":
    def func(**kwargs):
        print(f"pressed {kwargs["key"]}")

    hk = Hotkey()
    hk.add(["w", "a", "s", "d"], callback=func)
    
    hk.start()
    time.sleep(3)
    hk.stop()