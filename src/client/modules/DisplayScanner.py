from threading import Thread

import numpy as np

from . import ESPMeshDevice


class DisplayScanner:
    def __init__(self):
        self.mesh_devices: list[ESPMeshDevice] = []

    def register_device(self, esp_mesh_device: ESPMeshDevice):
        self.mesh_devices.append(esp_mesh_device)

    def has_devices(self):
        return len(self.mesh_devices) > 0

    def close_device_sockets(self):
        for mesh_device in self.mesh_devices:
            mesh_device.close_socket()

    def fetch_and_dispatch_screen_to_devices(self, sct):
        screen = sct.grab(sct.monitors[1])
        screen_as_np_array = np.asarray(screen)
        threads = []
        for mesh_device in self.mesh_devices:
            t = Thread(target=mesh_device.send_screen_update, args=(screen_as_np_array,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
