import string
from typing import Dict

import snap7


class S7Addr:
    type: snap7.types.WordLen
    db: int
    byte: int
    bit: int


class S7Comm:

    _ip_address: string
    _read_db_list: dict[int, dict[str, any]] = {}

    rain_today: string
    rain_yday: string
    cpu_state: string

    def __init__(self, ip_address) -> None:
        self._client = snap7.client.Client()
        self._ip_address = ip_address
        self.comms_status = False

    def register_db(self, db_number: int, start: int, size: int):
        db_details = {"start": start, "size": size, "data": None}
        self._read_db_list[db_number] = db_details

    def write_db(self, s7addr: S7Addr):

        if not self._connect():
            return None

        try:
            pass
            self._client.write_area(snap7.types.Areas.DB, 10, 0, 10, 1, data)
        except:
            return None

    def update_dbs(self) -> bool:

        if not self._connect():
            return None

        try:
            for db_number in self._read_db_list.keys():
                start = self._read_db_list[db_number]["start"]
                size = self._read_db_list[db_number]["size"]
                data = self._client.db_read(db_number, start, size)
                self._read_db_list[db_number]["data"] = data
        except:
            return None

    def get_db_data(self):
        return self._read_db_list

    def get_cpu_state(self) -> str:
        if not self._connect():
            return None

        state = self._client.get_cpu_state()
        self.cpu_state = "Run" if state == "S7CpuStatusRun" else "Stop"
        return self.cpu_state

    def _connect(self) -> bool:

        if self._client is None:
            self._client = snap7.client.Client()

        # Try and connect if not already
        if not self._client.get_connected():
            try:
                self._client.connect(self._ip_address, 0, 1, 102)
            except:
                del self._client
                self._client = snap7.client.Client()

        # Didnt successfully connect, return false status
        if not self._client.get_connected():
            self.comms_status = False
            return False

        # All good - connected
        self.comms_status = True
        return True


class S7Bool(S7Addr):
    def __init__(self, db: int, byte: int, bit: int) -> None:
        self.type = snap7.types.WordLen.Bit
        self.db = db
        self.byte = byte
        self.bit = bit

    def __str__(self) -> str:
        return f"DB{self.db}.DBX{self.byte}.{self.bit}"

    def get_bool(self, db_data) -> bool:
        try:
            return bool(snap7.util.get_bool(db_data, self.byte, self.bit))
        except:
            return None


class S7DWord(S7Addr):
    def __init__(self, db: int, offset: int) -> None:
        self.type = snap7.types.WordLen.DWord
        self.db = db
        self.offset = offset

    def __str__(self) -> str:
        return f"DB{self.db}.DBD{self.offset}"

    def get_real(self, real_format, db_data) -> float:
        try:
            return float(real_format.format(snap7.util.get_real(db_data, self.offset)))
        except:
            return None

    def get_dint(self, db_data) -> int:
        try:
            return snap7.util.get_dint(db_data, self.offset)
        except:
            return None

    def get_dword(self, db_data) -> int:
        try:
            return snap7.util.get_dword(db_data, self.offset)
        except:
            return None


class S7Word(S7Addr):
    def __init__(self, db: int, offset: int) -> None:
        self.type = snap7.types.WordLen.Word
        self.db = db
        self.offset = offset

    def __str__(self) -> str:
        return f"DB{self.db}.DBW{self.offset}"

    def get_int(self, real_format, db_data) -> int:
        try:
            return snap7.util.get_int(db_data, self.offset)
        except:
            return None

    def get_word(self, real_format, db_data) -> int:
        try:
            return snap7.util.get_word(db_data, self.offset)
        except:
            return None


def s7_real(real_format, data, offset):
    return float(real_format.format(snap7.util.get_real(data, offset)))


def s7_bool(data, byte, bit):
    return bool(snap7.util.get_bool(data, byte, bit))
