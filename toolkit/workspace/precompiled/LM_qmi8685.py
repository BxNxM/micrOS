"""
A simple driver for the QMI8658 IMU.
https://github.com/echo-lalia/qmi8658-micropython/blob/main/qmi8685.py
"""

import struct
import time
from machine import Pin, I2C
from micropython import const
from microIO import bind_pin, pinmap_search


# Sensor constants
_QMI8685_PARTID = const(0x05)
_REG_PARTID = const(0x00)
_REG_REVISION = const(0x01)

_REG_CTRL1 = const(0x02)  # Serial interface and sensor enable
_REG_CTRL2 = const(0x03)  # Accelerometer settings
_REG_CTRL3 = const(0x04)  # Gyroscope settings
_REG_CTRL4 = const(0x05)  # Magnetomer settings (support not implemented in this driver yet)
_REG_CTRL5 = const(0x06)  # Sensor data processing settings
_REG_CTRL6 = const(0x07)  # Attitude Engine ODR and Motion on Demand
_REG_CTRL7 = const(0x08)  # Enable Sensors and Configure Data Reads

_REG_TEMP = const(0x33)  # Temperature sensor.

_REG_AX_L = const(0x35)  # Read accelerometer
_REG_AX_H = const(0x36)
_REG_AY_L = const(0x37)
_REG_AY_H = const(0x38)
_REG_AZ_L = const(0x39)
_REG_AZ_H = const(0x3A)

_REG_GX_L = const(0x3B)  # read gyro
_REG_GX_H = const(0x3C)
_REG_GY_L = const(0x3D)
_REG_GY_H = const(0x3E)
_REG_GZ_L = const(0x3F)
_REG_GZ_H = const(0x40)

_QMI8658_I2CADDR_DEFAULT = const(0X6B)


_ACCELSCALE_RANGE_2G = const(0b00)
_ACCELSCALE_RANGE_4G = const(0b01)
_ACCELSCALE_RANGE_8G = const(0b10)
_ACCELSCALE_RANGE_16G = const(0b11)

_GYROSCALE_RANGE_16DPS = const(0b000)
_GYROSCALE_RANGE_32DPS = const(0b001)
_GYROSCALE_RANGE_64DPS = const(0b010)
_GYROSCALE_RANGE_128DPS = const(0b011)
_GYROSCALE_RANGE_256DPS = const(0b100)
_GYROSCALE_RANGE_512DPS = const(0b101)
_GYROSCALE_RANGE_1024DPS = const(0b110)
_GYROSCALE_RANGE_2048DPS = const(0b111)

_ODR_8000HZ = const(0b0000)
_ODR_4000HZ = const(0b0001)
_ODR_2000HZ = const(0b0010)
_ODR_1000HZ = const(0b0011)
_ODR_500HZ = const(0b0100)
_ODR_250HZ = const(0b0101)
_ODR_125HZ = const(0b0110)
_ODR_62_5HZ = const(0b0111)


class QMI8658:
    """QMI8658 inertial measurement unit."""
    INSTANCE = None

    def __init__(
            self,
            i2c_bus: I2C,
            address: int = _QMI8658_I2CADDR_DEFAULT,
            accel_scale: int = _ACCELSCALE_RANGE_8G,
            gyro_scale: int = _GYROSCALE_RANGE_256DPS):
        """Read from a sensor on the given I2C bus, at the given address."""
        self.i2c = i2c_bus
        self.address = address
        # Cache the sensor instance globally for easy access
        QMI8658.INSTANCE = self

        # Verify sensor part ID
        if self._read_u8(_REG_PARTID) != _QMI8685_PARTID:
            raise AttributeError("Cannot find a QMI8658")

        # Setup initial configuration
        self._configure_sensor(accel_scale, gyro_scale)

        # Configure scales/divisors for the driver
        self.acc_scale_divisor = {
            _ACCELSCALE_RANGE_2G: 1 << 14,
            _ACCELSCALE_RANGE_4G: 1 << 13,
            _ACCELSCALE_RANGE_8G: 1 << 12,
            _ACCELSCALE_RANGE_16G: 1 << 11,
        }[accel_scale]

        self.gyro_scale_divisor = {
            _GYROSCALE_RANGE_16DPS: 2048,
            _GYROSCALE_RANGE_32DPS: 1024,
            _GYROSCALE_RANGE_64DPS: 512,
            _GYROSCALE_RANGE_128DPS: 256,
            _GYROSCALE_RANGE_256DPS: 128,
            _GYROSCALE_RANGE_512DPS: 64,
            _GYROSCALE_RANGE_1024DPS: 32,
            _GYROSCALE_RANGE_2048DPS: 16,
        }[gyro_scale]


    def _configure_sensor(self, accel_scale: int, gyro_scale: int):
        # Initialize accelerometer and gyroscope settings
        self._write_u8(_REG_CTRL1, 0x60)  # Set SPI auto increment and big endian (Ctrl 1)
        self._write_u8(_REG_CTRL2, (accel_scale << 4) | _ODR_1000HZ)  # Accel Config
        self._write_u8(_REG_CTRL3, (gyro_scale << 4) | _ODR_1000HZ)  # Gyro Config
        self._write_u8(_REG_CTRL5, 0x01)  # Low-pass filter enable
        self._write_u8(_REG_CTRL7, 0x03)  # Enable accel and gyro
        time.sleep_ms(100)


    # Helper functions for register operations
    def _read_u8(self, reg:int) -> int:
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def _read_xyz(self, reg:int) -> tuple[int, int, int]:
        data = self.i2c.readfrom_mem(self.address, reg, 6)
        return struct.unpack('<hhh', data)

    def _write_u8(self, reg: int, value: int):
        self.i2c.writeto_mem(self.address, reg, bytes([value]))


    @property
    def temperature(self) -> float:
        """Get the device temperature."""
        temp_raw = self._read_u8(_REG_TEMP)
        return temp_raw / 256

    @property
    def acceleration(self) -> tuple[float, float, float]:
        """Get current acceleration reading."""
        raw_accel = self._read_xyz(_REG_AX_L)
        return tuple(val / self.acc_scale_divisor for val in raw_accel)

    @property
    def gyro(self) -> tuple[float, float, float]:
        """Get current gyroscope reading."""
        raw_gyro = self._read_xyz(_REG_GX_L)
        return tuple(val / self.gyro_scale_divisor for val in raw_gyro)

#######################
#   Public functions  #
#######################

def load():
    """
    Load the QMI8658 sensor instance.
    The QMI8658 is a motion sensor that measures acceleration, angular velocity (gyroscope), and temperature
    """
    if QMI8658.INSTANCE is None:
        QMI8658(I2C(0, sda=Pin(bind_pin('i2c_sda')), scl=Pin(bind_pin('i2c_scl'))))
    return QMI8658.INSTANCE


def temperature():
    return load().temperature


def acceleration():
    return load().acceleration


def gyro():
    return load().gyro


def measure():
    inst = load()
    return {"temp": inst.temperature, "accel": inst.acceleration, "gyro": inst.gyro}


#######################
# LM helper functions #
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
    return 'load', 'temperature', 'acceleration', 'gyro', 'measure', 'pinmap'