from tkinter import ttk, Button, Toplevel, messagebox

from . import Selection, ESPMulticastCommunication


class MeshEntitySelector:
    def __init__(self, esp_communication: ESPMulticastCommunication, mesh_entity_selection: Selection):
        self.esp_communication = esp_communication
        self.mesh_entity_selection = mesh_entity_selection
        self.root = Toplevel()
        self.entities_tree = ttk.Treeview(self.root, columns=('deviceKey', 'ipAddress', 'reservedStatus'))
        self.__populate_tree()
        self.entities_tree.pack()
        self.__add_buttons()

    def __populate_tree(self):
        esp_mesh_entities = self.esp_communication.get_available_mesh_entities()
        self.entities_tree['show'] = 'headings'
        self.entities_tree.heading('deviceKey', text='Device Key')
        self.entities_tree.heading('ipAddress', text='IP Address')
        self.entities_tree.heading('reservedStatus', text='Reserved Status')
        for index, (key, value) in enumerate(esp_mesh_entities.items()):
            self.entities_tree.insert('', 'end', iid=key, values=(key, value['ip_address'][0], value['reserved']))
        if len(esp_mesh_entities) == 0:
            messagebox.showwarning("No mesh entities available", "There are no available mesh entities at this moment.")

    def __add_buttons(self):
        submit_button = Button(self.root, text="Submit", command=self.submit_selection)
        submit_button.pack(side='left')
        refresh_button = Button(self.root, text="Refresh", command=self.refresh_tree)
        refresh_button.pack(side='right')

    def submit_selection(self):
        selected = self.entities_tree.selection()
        if not selected:
            messagebox.showwarning("No valid selection", "Please select one or more entities.")
            return
        for item_id in selected:
            item = self.entities_tree.item(item_id)
            reserved_status = item["values"][2] == "True"
            if reserved_status:
                messagebox.showwarning("Reserved entity", "One or more selected entities are reserved.")
                return
        self.mesh_entity_selection.set_selection(selected)
        self.root.destroy()
        self.root.update()
        self.root.quit()

    def refresh_tree(self):
        for i in self.entities_tree.get_children():
            self.entities_tree.delete(i)
        self.esp_communication.update_available_mesh_entities()
        self.__populate_tree()

    def run(self):
        self.root.wait_window()
