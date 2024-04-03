import json
import socket
import uuid

from . import ESPMeshDevice


class ESPMulticastCommunication:
    def __init__(self):
        self.name = uuid.uuid4()
        self.open_port = 6000
        self.multicast_ttl = 2
        self.esp_mesh_multicast = ('239.100.101.102', 6000)
        self.timeout = 1
        self.available_mesh_entities = self.__fetch_mesh_entities()

    def __fetch_mesh_entities(self) -> dict:
        mesh_entities = {}
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.multicast_ttl)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('', self.open_port))
            s.settimeout(self.timeout)
            s.sendto(b"reconnaissance", self.esp_mesh_multicast)
            waiting_for_reply = True
            while waiting_for_reply:
                try:
                    data, addr = s.recvfrom(1024)
                    entity_reply = json.loads(data.decode('utf-8'))
                    entity_reply['ip_address'] = (addr[0], 6001)
                    entity_uuid = entity_reply.pop('uuid')
                    mesh_entities[entity_uuid] = entity_reply
                except socket.timeout:
                    waiting_for_reply = False
        return mesh_entities

    def get_available_mesh_entities(self) -> dict:
        return self.available_mesh_entities

    def update_available_mesh_entities(self):
        self.available_mesh_entities = self.__fetch_mesh_entities()

    def construct_esp_mesh_device(self, key):
        requested_mesh_entity = self.available_mesh_entities[key]
        device_uuid = key
        ip_address = requested_mesh_entity['ip_address']
        amount_of_leds = requested_mesh_entity['amount_of_leds']
        return ESPMeshDevice(device_uuid, ip_address, amount_of_leds)
