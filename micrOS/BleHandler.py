from micropython import const
import struct
import bluetooth
from binascii import hexlify
from ConfigHandler import cfgget

# BLUETOOTH IRQ LUT
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

# BLUETOOTH FLAGS
_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

# BLUETOOTH KEYS
_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"), _FLAG_READ | _FLAG_NOTIFY,)
_UART_RX = (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"), _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,)
_UART_SERVICE = (_UART_UUID, (_UART_TX, _UART_RX),)

# BLUETOOTH ADVERTISING DATA
_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_UUID16_MORE = const(0x2)
_ADV_TYPE_UUID32_MORE = const(0x4)
_ADV_TYPE_UUID128_MORE = const(0x6)
_ADV_TYPE_APPEARANCE = const(0x19)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)


class BleHandler:

    def __init__(self):
        print("[AdvH] Create BLE object, and advertise node...")
        self._ble = bluetooth.BLE()
        # Activate bluetooth
        self._ble.active(True)
        # Bluetooth irq callback handling
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        # Create connection set
        self._connections = set()
        self._payload = None
        self.local_devs_data = {}

    @staticmethod
    def adv_payload_data(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
        payload = bytearray()
        print("[AdvH] name: {} services: {}".format(name, services))

        def _append(adv_type, value):
            nonlocal payload
            #print("[!!!!] |{}|{}|".format(value, adv_type))
            payload += struct.pack("BB", len(value) + 1, adv_type) + value

        _append(_ADV_TYPE_FLAGS, struct.pack("B", (0x01 if limited_disc else 0x02) + (0x18 if br_edr else 0x04)))
        if name:
            _append(_ADV_TYPE_NAME, name)

        if services:
            for uuid in services:
                b = bytes(uuid)
                if len(b) == 2:
                    _append(_ADV_TYPE_UUID16_COMPLETE, b)
                elif len(b) == 4:
                    _append(_ADV_TYPE_UUID32_COMPLETE, b)
                elif len(b) == 16:
                    _append(_ADV_TYPE_UUID128_COMPLETE, b)

        # See org.bluetooth.characteristic.gap.appearance.xml
        if appearance:
            _append(_ADV_TYPE_APPEARANCE, struct.pack("<h", appearance))
        print("[AdvH] Advertise payload: {}".format(payload))
        return payload

    @staticmethod
    def _decode_field(payload, adv_type):
        i = 0
        result = []
        while i + 1 < len(payload):
            if payload[i + 1] == adv_type:
                result.append(payload[i + 2: i + payload[i] + 1])
            i += 1 + payload[i]
        return result

    @staticmethod
    def decode_name(payload):
        n = BleHandler._decode_field(payload, _ADV_TYPE_NAME)
        return str(n[0], "utf-8") if n else ""

    @staticmethod
    def decode_services(payload):
        services = []
        for u in BleHandler._decode_field(payload, _ADV_TYPE_UUID16_COMPLETE):
            services.append(bluetooth.UUID(struct.unpack("<h", u)[0]))
        for u in BleHandler._decode_field(payload, _ADV_TYPE_UUID32_COMPLETE):
            services.append(bluetooth.UUID(struct.unpack("<d", u)[0]))
        for u in BleHandler._decode_field(payload, _ADV_TYPE_UUID128_COMPLETE):
            services.append(bluetooth.UUID(u))
        return services

    @staticmethod
    def _gen_adv_info():
        if cfgget('nwmd') == 'STA' and cfgget('devip') != 'n/a':
            stasubip = '.'.join(cfgget('devip').split('.')[-2:])
            subfid = cfgget('devfid')[0:2]
            return '{}|{}'.format(subfid, stasubip)
        return 'micrOS'

    def advertise(self, name=None, appearance=0, interval_us=1500000):
        print("[AdvH] Starting advertising")
        if name is None:
            name = BleHandler._gen_adv_info()
        # Advertise node
        self._payload = BleHandler.adv_payload_data(name=name, services=[_UART_UUID], appearance=appearance)
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def _irq(self, event, data):
        """
        Handle Advertise server lifecycle
        """
        # Advertise IRQ callbacks - Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("[AdvH] New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("[AdvH] Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self.advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            print("[AdvH] GATTS input data: ", value)
            if value_handle == self._handle_rx:
                print("|- [AdvH] GATTS input data: ", value)
        # Scan IRQ callbacks
        elif event == _IRQ_SCAN_DONE:
            print("[AdvH] Scan finished:\n {}".format(self.local_devs_data))
        if event == _IRQ_SCAN_RESULT:
            print("Scan Raw result: {}".format(data))           # TODO: remove
            addr_type, addr, adv_type, rssi, adv_data = data
            if adv_type in (_ADV_IND, _ADV_DIRECT_IND) and _UART_UUID in BleHandler.decode_services(adv_data):
                # Found a potential device, remember it and stop scanning.
                addr = bytes(addr)  # Note: addr buffer is owned by caller so need to copy it.
                name = BleHandler.decode_name(adv_data) or "?"
                if addr_type is not None:
                    print("[AdvH] Scan result: {}:{}:{}".format(name, addr, addr_type))
                    decoded_addr = hexlify(addr).decode('utf-8')
                    self.local_devs_data[decoded_addr] = (name, addr_type)

    def scan(self, duration_ms=6000, interval_us=30000, window_us=30000):
        # Find a device advertising the environmental sensor service.
        # Set duration_ms to None for stop scanning
        # Set duration_ms = 0 -> scan indefinitely
        self._ble.gap_scan(duration_ms, interval_us, window_us)

    def dns(self):
        return self.local_devs_data
