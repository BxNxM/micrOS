from BleHandler import BleHandler
from time import sleep

BLE = None


def __init_ble():
    global BLE
    if BLE is None:
        BLE = BleHandler()
    return BLE


def advert():
    __init_ble().advertise()
    return "Advertise micrOS node"


def scan():
    __init_ble().scan()
    return "Start scanning..."


def list():
    return __init_ble().dns()


def make():
    bleobj = __init_ble()
    bleobj.advertise()
    sleep(1)
    bleobj.scan()
    return "Advertise and scan ble nw."


def help():
    return 'advert', 'scan', 'list', 'make'
