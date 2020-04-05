from ConfigHandler import cfgget
from gc import mem_free
from time import localtime, sleep

__OLED = None

def __init():
    global __OLED
    if __OLED is None:
        from machine import Pin, I2C
        from ssd1306 import SSD1306_I2C
        from LogicalPins import getPlatformValByKey
        i2c = I2C(-1, Pin(getPlatformValByKey('i2c_scl')), Pin(getPlatformValByKey('i2c_sda')))
        __OLED = SSD1306_I2C(128, 64, i2c)
    return __OLED


def pixel_art():
    base_point = (55, 40)
    base_size = 15
    delta_size = 5

    # INIT OLED IF WAS NOT CREATED
    __init()

    # MAIN RECT
    __OLED.rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size+delta_size, base_size+delta_size, 1)
    __OLED.show()
    sleep(0.15)

    # TOP-LEFT CORNER
    __OLED.rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size, base_size, 1)
    __OLED.show()
    sleep(0.15)
    # BUTTON-RIGHT CORNER
    __OLED.rect(base_point[0], base_point[1], base_size, base_size, 1)
    __OLED.show()
    sleep(0.15)

    # TOP-LEFT CORNER2
    __OLED.rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size-delta_size, base_size-delta_size, 1)
    __OLED.show()
    sleep(0.15)
    # BUTTON-RIGHT CORNER2
    __OLED.rect(base_point[0]+delta_size, base_point[1]+delta_size, base_size-delta_size, base_size-delta_size, 1)
    __OLED.show()
    sleep(0.15)

    # TOP-LEFT CORNER3
    __OLED.rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size-delta_size*2, base_size-delta_size*2, 1)
    __OLED.show()
    sleep(0.15)
    # BUTTON-RIGHT CORNER3
    __OLED.rect(base_point[0]+delta_size*2, base_point[1]+delta_size*2, base_size-delta_size*2, base_size-delta_size*2, 1)
    __OLED.show()
    sleep(0.15)

    # Jumping cube - top-left - and back
    __OLED.rect(base_point[0]-delta_size*2, base_point[1]-delta_size*2, base_size-delta_size*2, base_size-delta_size*2, 1)
    __OLED.show()
    __OLED.rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size-delta_size*2, base_size-delta_size*2, 0)      #
    __OLED.show()
    sleep(0.1)
    __OLED.rect(base_point[0]-delta_size*3, base_point[1]-delta_size*3, base_size-delta_size*2, base_size-delta_size*2, 1)
    __OLED.show()
    __OLED.rect(base_point[0]-delta_size*2, base_point[1]-delta_size*2, base_size-delta_size*2, base_size-delta_size*2, 0)    #
    __OLED.show()
    sleep(0.1)
    __OLED.rect(base_point[0]-delta_size*4, base_point[1]-delta_size*4, base_size-delta_size*2, base_size-delta_size*2, 1)
    __OLED.show()
    __OLED.rect(base_point[0]-delta_size*3, base_point[1]-delta_size*3, base_size-delta_size*2, base_size-delta_size*2, 0)    #
    __OLED.show()
    sleep(0.1)
    __OLED.rect(base_point[0]-delta_size*4, base_point[1]-delta_size*4, base_size-delta_size*2, base_size-delta_size*2, 1)
    __OLED.show()
    __OLED.rect(base_point[0]-delta_size*4, base_point[1]-delta_size*4, base_size-delta_size*2, base_size-delta_size*2, 0)    #
    __OLED.show()
    sleep(0.1)
    __OLED.rect(base_point[0]-delta_size*3, base_point[1]-delta_size*3, base_size-delta_size*2, base_size-delta_size*2, 1)
    __OLED.show()
    __OLED.rect(base_point[0]-delta_size*4, base_point[1]-delta_size*4, base_size-delta_size*2, base_size-delta_size*2, 0)
    __OLED.show()
    sleep(0.1)
    __OLED.rect(base_point[0]-delta_size*2, base_point[1]-delta_size*2, base_size-delta_size*2, base_size-delta_size*2, 1)
    __OLED.show()
    __OLED.rect(base_point[0]-delta_size*3, base_point[1]-delta_size*3, base_size-delta_size*2, base_size-delta_size*2, 0)
    __OLED.show()
    sleep(0.1)
    __OLED.rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size-delta_size*2, base_size-delta_size*2, 1)
    __OLED.show()


def simple_page():
    try:
        # Clean screen
        __init().fill(0)
        # Draw time
        __OLED.text("{}:{}:{}".format(localtime()[-5], localtime()[-4], localtime()[-3]), 30, 10)
        __OLED.show()
        pixel_art()
    except Exception as e:
        return str(e)
    return True


def show_debug_page():
    try:
        # Clean screen
        __init().fill(0)
        __OLED.show()
        # Print info
        __OLED.text("{}:{}:{}".format(localtime()[-5], localtime()[-4], localtime()[-3]), 30, 0)
        __OLED.text("NW_MODE: {}".format(cfgget("nwmd")), 0, 10)
        __OLED.text("IP: {}".format(cfgget("devip")), 0, 20)
        __OLED.text("FreeMem: {}".format(mem_free()), 0, 30)
        __OLED.text("PORT: {}".format(cfgget("socport")), 0, 40)
        __OLED.text("NAME: {}".format(cfgget("devfid")), 0, 50)
        # Show page buffer - send to display
        __OLED.show()
    except Exception as e:
        return str(e)
    return True


def help():
    return ('simple_page', 'show_debug_page')

