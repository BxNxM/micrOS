# HLK-LD2410 (Microwave-based human/object presence sensor) Tool
# rev 1 - shabaz - May 2023
# Example data report in Basic mode:
# hex: f4 f3 f2 f1 0d 00 02 aa 03 4f 00 64 4c 00 64 32 00 55 00 f8 f7 f6 f5
# bytes 0-3 are the header, always 0xf4, 0xf3, 0xf2, 0xf1
# bytes 4-5 are the frame length, always 0x0d, 0x00 for Basic mode
# byte 6 is the report type, always 0x02 for Basic mode, or 0x01 for Engineering mode
# byte 7 is the report head, always 0xaa
# byte 8 is the state, 0x00 = no target, 0x01 = moving target, 0x02 = stationary target, 0x03 = combined target
# bytes 9-10 are the moving target distance in cm, little endian
# byte 11 is the moving target energy
# bytes 12-13 are the stationary target distance in cm, little endian
# byte 14 is the stationary target energy
# bytes 15-16 are the detection distance in cm, little endian
# https://community.element14.com/technologies/embedded/b/blog/posts/experimenting-with-microwave-based-sensors-for-presence-detection
# Based on https://github.com/shabaz123/LD2410/blob/main/ld2410.py

from machine import Pin, UART
import utime
from microIO import bind_pin, pinmap_search

ser = UART(1, baudrate = 256000, tx=Pin(bind_pin('tx')), rx=Pin(bind_pin('rx')), timeout = 1)
HEADER = bytes([0xfd, 0xfc, 0xfb, 0xfa])
TERMINATOR = bytes([0x04, 0x03, 0x02, 0x01])
NULLDATA = bytes([])
REPORT_HEADER = bytes([0xf4, 0xf3, 0xf2, 0xf1])
REPORT_TERMINATOR = bytes([0xf8, 0xf7, 0xf6, 0xf5])

STATE_NO_TARGET = 0
STATE_MOVING_TARGET = 1
STATE_STATIONARY_TARGET = 2
STATE_COMBINED_TARGET = 3
TARGET_NAME = ["no_target", "moving_target", "stationary_target", "combined_target"]

meas = {
    "state": STATE_NO_TARGET,
    "moving_distance": 0,
    "moving_energy": 0,
    "stationary_distance": 0,
    "stationary_energy": 0,
    "detection_distance": 0 }

def print_bytes(data):
    if len(data) == 0:
        print("<no data>")
        return
    text = f"hex: {data[0]:02x}"
    for i in range(1, len(data)):
        text = text + f" {data[i]:02x}"
    print(text)

def bytes_to_str(data):
    if len(data) == 0:
        return "<no data>"
    text = f"hex: {data[0]:02x}"
    for i in range(1, len(data)):
        text = text + f" {data[i]:02x}"
    return text

def send_command(cmd, data=NULLDATA, response_expected=True):
    cmd_data_len = bytes([len(cmd) + len(data), 0x00])
    frame = HEADER + cmd_data_len + cmd + data + TERMINATOR
    ser.write(frame)
    if response_expected:
        response = ser.read()
    else:
        response = NULLDATA
    return response

def enable_config():
    response = send_command(bytes([0xff, 0x00]), bytes([0x01, 0x00]))
    print_bytes(response)

def end_config():
    response = send_command(bytes([0xfe, 0x00]), response_expected=False)

def _read_firmware_version():
    response = send_command(bytes([0xa0, 0x00]))
    print_bytes(response)
    return response

def enable_engineering():
    response = send_command(bytes([0x62, 0x00]))
    print_bytes(response)

def end_engineering():
    response = send_command(bytes([0x63, 0x00]))
    print_bytes(response)

def read_serial_buffer():
    response = ser.read()
    print_bytes(response)
    return response

def _print_meas():
    print(f"state: {TARGET_NAME[meas['state']]}")
    print(f"moving distance: {meas['moving_distance']}")
    print(f"moving energy: {meas['moving_energy']}")
    print(f"stationary distance: {meas['stationary_distance']}")
    print(f"stationary energy: {meas['stationary_energy']}")
    print(f"detection distance: {meas['detection_distance']}")

def _parse_report(data):
    global meas
    # sanity checks
    if len(data) < 23:
        print(f"error, frame length {data} is too short")
        return
    if data[0:4] != REPORT_HEADER:
        print(f"error, frame header is incorrect")
        return
    # Check if data[4] (frame length) is valid. It must be 0x0d or 0x23
    # depending on if we are in basic mode or engineering mode
    if data[4] != 0x0d and data[4] != 0x23:
        print(f"error, frame length is incorrect")
        return
    # data[7] must be report 'head' value 0xaa
    if data[7] != 0xaa:
        print(f"error, frame report head value is incorrect")
        return
    # sanity checks passed. Store the sensor data in meas
    meas["state"] = data[8]
    meas["moving_distance"] = data[9] + (data[10] << 8)
    meas["moving_energy"] = data[11]
    meas["stationary_distance"] = data[12] + (data[13] << 8)
    meas["stationary_energy"] = data[14]
    meas["detection_distance"] = data[15] + (data[16] << 8)
    # print the data
    _print_meas()

def _read_serial_until(identifier):
    content = bytes([])
    while len(identifier) > 0:
        v = ser.read(1)
        if v is None:
            # timeout
            return None
            break
        if v[0] == identifier[0]:
            content = content + v[0:1]
            identifier = identifier[1:len(identifier)]
        else:
            content = bytes([])
    return content

def serial_flush():
    dummy = ser.read()
    return dummy

def _read_serial_frame():
    # dummy read to flush out the read buffer:
    serial_flush()
    utime.sleep_ms(100)
    # keep reading to see a header arrive:
    header = _read_serial_until(REPORT_HEADER)
    if header == None:
        return None
    # read the rest of the frame:
    response = ser.read(23-4)
    if response == None:
        return None
    response = header + response
    if response[-4:] != REPORT_TERMINATOR:
        # error, packet seems incorrect
        return None
    print_bytes(response)
    _parse_report(response)
    return response


def read():
    _read_serial_frame()
    if meas['state'] == STATE_MOVING_TARGET:
        state = 'moving'
    elif meas['state'] == STATE_COMBINED_TARGET:
        state = 'combined'
    else:
        state = 'n/a'
    return {'state': state, 'measure': meas}


def firmware_version():
    return bytes_to_str(_read_firmware_version())


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search(['tx', 'rx'])


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'read', 'firmware_version', 'serial_flush', 'pinmap'
