import tkinter as tk

from modules import *

if __name__ == '__main__':
    tk_root = tk.Tk()
    tk_root.withdraw()
    esp_communication = ESPMulticastCommunication()
    mesh_entity_selection = Selection()
    mesh_entity_selector = MeshEntitySelector(esp_communication, mesh_entity_selection)
    mesh_entity_selector.run()
    display_scanner = DisplayScanner()
    for key in mesh_entity_selection.get_selection():
        esp_mesh_device = esp_communication.construct_esp_mesh_device(key)
        if esp_mesh_device.reserve_mesh_entity():
            esp_mesh_device.start_range_selection()
            screen_selection = Selection()
            screen_selector = ScreenSelector(screen_selection, key)
            screen_selector.run()
            esp_mesh_device.register_screen_selection(screen_selection)
            display_scanner.register_device(esp_mesh_device)
            esp_mesh_device.end_range_selection()
    if display_scanner.has_devices():
        screen_loop = ScreenLoop(display_scanner)
        screen_loop.loop()
