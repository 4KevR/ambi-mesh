import time
from tkinter import Toplevel, Button

from mss import mss

from . import DisplayScanner


class ScreenLoop:
    def __init__(self, display_scanner: DisplayScanner):
        self.display_scanner = display_scanner
        self.to_terminate = False
        self.tk_exit_root = Toplevel()
        submit_button = Button(self.tk_exit_root, text="Close connections", command=self.terminate_loop)
        submit_button.pack()

    def terminate_loop(self):
        self.to_terminate = True

    def loop(self):
        last_update = time.time()
        counter = 0
        with mss() as sct:
            while not self.to_terminate:
                self.tk_exit_root.update()
                self.display_scanner.fetch_and_dispatch_screen_to_devices(sct)
                counter += 1
                if time.time() - last_update > 1:
                    last_update = time.time()
                    print(f"Frames: {counter} fps")
                    counter = 0
            self.display_scanner.close_device_sockets()
            self.tk_exit_root.destroy()
            self.tk_exit_root.update()
            self.tk_exit_root.quit()
