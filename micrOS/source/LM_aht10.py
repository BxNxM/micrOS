from machine import I2C, Pin
from microIO import bind_pin, pinmap_search
from Common import syslog
from time import sleep
from binascii import hexlify
from Types import resolve

##################################################################################
# AHT10 temperature & humidity sensor                                            #
# Specification: https://server4.eca.ir/eshop/AHT10/Aosong_AHT10_en_draft_0c.pdf #
##################################################################################
__AHT10_OBJ = None


def _handle_connection_error(f):
    def _decorated(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            syslog(f"[ERR] {f.__name__}: {e}")
    return _decorated


class AHT10:
    def __init__(self, address = 0x38):
        self.i2c = I2C(-1, Pin(bind_pin('i2c_scl')), Pin(bind_pin('i2c_sda')), freq = 9600)
        self.address = address
        if not self.init_sensor():
            raise Exception("Could not initialize the sensor!")

    def _send_sensor(self, buf):
        i2c_ack_count = self.i2c.writeto(self.address, buf)
        if len(buf) != i2c_ack_count:
            raise Exception(f"Number of ACKs does not match buffer size: {len(buf)} != {i2c_ack_count}. Buffer content: {hexlify(buf).decode()}")
        return True

    def _read_sensor(self, nbytes):
        sensor_data = self.i2c.readfrom(self.address, nbytes)
        return sensor_data

    @_handle_connection_error
    def measure(self):
        """
        Send measurement trigger command and apply conversion to the result
        :return tuple: temperature, humidity
        """
        device_busy = True
        retry_count = 0

        self._send_sensor(b'\xAC\x33\x00')
        while device_busy and retry_count < 10:
            sleep(0.1) # The delay can be at least 75ms
            device_busy = self._read_sensor(1)[0] >> 8 == 1
            retry_count += 1

        if device_busy:
            return None

        sensor_data = self._read_sensor(6)

        # Humidity data is stored on the 2nd, 3rd and the first half of the 4th byte,
        # the rest contains temperature data
        hum = ((sensor_data[1] << 16) | (sensor_data[2] << 8) | sensor_data[3]) >> 4
        hum = hum * 100 / 2**20

        temp = ((sensor_data[3] & 0x0F) << 16) | (sensor_data[4] << 8) | sensor_data[5]
        temp = ((temp * 200) / 2**20) - 50

        return temp, hum

    @_handle_connection_error
    def init_sensor(self):
        """
        Send initialization command
        """
        return self._send_sensor(b'\xE1\x08\x00')

    @_handle_connection_error
    def reset(self):
        """
        Send soft reset command
        """
        return self._send_sensor(b'\xBA')


def load():
    """
    Initialize AHT10 module
    """
    __init_AHT10()
    return "AHT10 temp/hum sensor - loaded"


def __init_AHT10():
    global __AHT10_OBJ
    if __AHT10_OBJ is None:
        __AHT10_OBJ = AHT10()
    return __AHT10_OBJ


def measure():
    """
    Measure with aht10
    :return dict: temp, hum
    """
    _temp, _hum = __init_AHT10().measure()
    return {"temp [ºC]": _temp,
            "hum [%]": _hum}


def reset():
    """
    Reset the sensor
    """
    __init_AHT10().reset()

#######################
# Helper LM functions #
#######################

def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search(['i2c_scl', 'i2c_sda'])


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('TEXTBOX measure', 'reset', 'load', 'pinmap'), widgets=widgets)
