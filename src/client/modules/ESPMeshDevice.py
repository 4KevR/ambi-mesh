import socket
from enum import Enum

import numpy as np
import scipy.interpolate as interpolate

from . import Selection


def rgb_to_hex(rgb):
    return '%02x%02x%02x' % tuple(map(int, rgb))


class ConnectionState(Enum):
    NOT_CONNECTED = 1
    RESERVED = 2
    SELECTING = 3
    READY = 4
    STREAMING = 5
    DISCONNECTED = 6


class ESPMeshDevice:
    def __init__(self, device_uuid, ip_address, amount_of_leds):
        self.led_coords = None
        self.device_uuid = device_uuid
        self.amount_of_leds = amount_of_leds
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(ip_address)
        self.connection_state = ConnectionState.NOT_CONNECTED

    def register_screen_selection(self, screen_selection: Selection):
        list_pixel_selection = screen_selection.get_selection()
        points = np.array(list_pixel_selection)
        distances = np.sqrt((np.diff(points, axis=0) ** 2).sum(axis=1))
        cumulative_distance = np.insert(distances, 0, 0).cumsum()
        x_inter = interpolate.interp1d(cumulative_distance, points[:, 0], kind='linear', fill_value='extrapolate')
        y_inter = interpolate.interp1d(cumulative_distance, points[:, 1], kind='linear', fill_value='extrapolate')
        led_distances = np.linspace(0, cumulative_distance.max(), self.amount_of_leds)
        led_xs = list(map(int, x_inter(led_distances)))
        led_ys = list(map(int, y_inter(led_distances)))
        self.led_coords = list(zip(led_xs, led_ys))

    def send_screen_update(self, screen):
        hex_array = []
        for led_x, led_y in self.led_coords:
            hex_array.append(rgb_to_hex(screen[led_y][led_x][:3][::-1]))
        data = "".join(hex_array) + "\n"
        self.sock.send(data.encode())
        data = self.sock.recv(1024)
        if data.decode('utf-8') != 'ack':
            self.sock.close()

    def reserve_mesh_entity(self) -> bool:
        reserved = self.__send_acknowledged(b"reserve")
        if reserved:
            self.connection_state = ConnectionState.RESERVED
            return True
        return False

    def start_range_selection(self) -> bool:
        selected = self.__send_acknowledged(b"selecting")
        if selected:
            self.connection_state = ConnectionState.SELECTING
            return True
        return False

    def end_range_selection(self) -> bool:
        is_ready = self.__send_acknowledged(b"ready")
        if is_ready:
            self.connection_state = ConnectionState.READY
            return True
        return False

    def disconnect_from_mesh_entity(self) -> bool:
        disconnected = self.__send_acknowledged(b"disconnect")
        if disconnected:
            self.connection_state = ConnectionState.DISCONNECTED
            return True
        return False

    def __send_acknowledged(self, command: bytes) -> bool:
        self.sock.send(command + b'\n')
        try:
            data = self.sock.recv(1024)
            if data.decode('utf-8') != 'ack':
                return False
        except socket.timeout:
            return False
        return True

    def close_socket(self):
        self.disconnect_from_mesh_entity()
        self.sock.close()
