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

    def update(self) -> boolean:
        if not self._client.get_connected():
            self._client.connect(self._ip_address, 0, 1, 102)
        if not self._client.get_connected():
            self.comms_status = False
            return None
        self.comms_status = True

        state = self._client.get_cpu_state()
        self.cpu_state = "Run" if state == "S7CpuStatusRun" else "Stop"

        # Hardcoded DB40, 54 bytes of data for RAIN
        data = self._client.db_read(40, 0, 54)
        self.rain_today = float("{0:.1f}".format(snap7.util.get_real(data, 30)))
        self.rain_yday = float("{0:.1f}".format(snap7.util.get_real(data, 42)))

hass7:Hass7 = Hass7("192.168.1.61")
hass7.update()
print(f"{hass7.rain_today} {hass7.rain_yday} {hass7.cpu_state}")