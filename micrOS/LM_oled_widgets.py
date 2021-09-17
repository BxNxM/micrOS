from ConfigHandler import cfgget
from gc import mem_free
from time import localtime
from network import WLAN, STA_IF
import LM_oled as oled


def simple_page():
    try:
        # Clean screen
        oled.clean(show=False)
        # Draw time
        oled.text("{}:{}:{}".format(localtime()[-5], localtime()[-4], localtime()[-3]), 30, 10)
    except Exception as e:
        return str(e)
    return True


def sys_page(clean=False):
    def __draw_rssi():
        value = WLAN(STA_IF).status('rssi')
        show_range = round(((value+91)/30)*8)    # pixel height 8
        oled.line(118, 8, 120, 8, show=False)
        oled.line(110, 1, 128, 1, show=False)
        for k in range(0, show_range):
            oled.line(118-k, 8-k, 120+k, 8-k, show=False)
    # Clean screen
    oled.clean(show=clean)
    # Print info
    try:
        __draw_rssi()
    except:
        pass
    ltime = localtime()
    h = "0{}".format(ltime[-5]) if len(str(ltime[-5])) < 2 else ltime[-5]
    m = "0{}".format(ltime[-4]) if len(str(ltime[-4])) < 2 else ltime[-4]
    s = "0{}".format(ltime[-3]) if len(str(ltime[-3])) < 2 else ltime[-3]
    oled.text("{}   {}:{}:{}".format(cfgget("nwmd")[0], h, m, s), 0, 0, show=False)
    oled.text("FUID: {}".format(cfgget("devfid")), 0, 15, show=False)
    oled.text("IP: {}".format(cfgget("devip")), 0, 25, show=False)
    fm = mem_free()
    kb, byte = int(fm/1000), int(fm % 1000)
    oled.text("Mem: {}kb {}b".format(kb, byte), 0, 35, show=False)
    oled.text("V: {}".format(cfgget("version")), 0, 45)             # It will show the whole buffer as well.
    return True

#######################
# LM helper functions #
#######################


def lmdep():
    return 'LM_oled'


def help():
    return 'simple_page', 'sys_page',\
           'INFO: OLED Module for SSD1306'
