import string
from xmlrpc.client import boolean

import snap7


class Hass7:

    _ip_address: string

    rain_today: string
    rain_yday: string
    cpu_state: string

    def __init__(self, ip_address) -> None:
        self._client = snap7.client.Client()
        self._ip_address = ip_address
        self.comms_status = False

    def update(self) -> bool:
        self.comms_status = False
        self._client.connect(self._ip_address, 0, 1, 102)
        if not self._client.get_connected():
            return False
        self.comms_status = True

        state = self._client.get_cpu_state()
        self.cpu_state = "Run" if state == "S7CpuStatusRun" else "Stop"

        # Hardcoded DB40, 54 bytes of data for RAIN
        self._data = self._client.db_read(40, 0, 54)
        self.rain_today = float("{0:.1f}".format(snap7.util.get_real(self._data, 30)))
        self.rain_yday = float("{0:.1f}".format(snap7.util.get_real(self._data, 42)))

        return True

    def get_real(self, offset):
        if self.comms_status == True:
            return float("{0:.1f}".format(snap7.util.get_real(self._data, offset)))
        return 0


hass7 = Hass7("192.168.1.61")
status = hass7.update()
print(hass7.comms_status)
print(hass7.get_real(30))
print(hass7.get_real(42))