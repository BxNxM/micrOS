from ConfigHandler import cfgget
from gc import mem_free
from utime import localtime
from network import WLAN, STA_IF
import LM_oled as oled
from Common import SmartADC
from LogicalPins import physical_pin


#################################
# PAGE MANAGER CLASS DEFINITION #
#################################

class PageUI:
    PAGE_UI_OBJ = None

    def __init__(self, page_callbacks, w, h):
        self.active_page = 0
        self.page_callback_list = page_callbacks
        self.width = w
        self.height = h
        PageUI.PAGE_UI_OBJ = self

    def __page_header(self):
        """Generates header bar with NW mode + Clock + wifi rssi"""

        def __draw_rssi():
            value = WLAN(STA_IF).status('rssi')
            show_range = round(((value + 91) / 30) * 8)  # pixel height 8
            oled.line(self.width - 10, 8, self.width - 8, 8)
            oled.line(self.width - 18, 1, self.width, 1)
            for k in range(0, show_range):
                oled.line(118 - k, 8 - k, 120 + k, 8 - k)

        try:
            __draw_rssi()
        except:
            pass
        ltime = localtime()
        h = "0{}".format(ltime[-5]) if len(str(ltime[-5])) < 2 else ltime[-5]
        m = "0{}".format(ltime[-4]) if len(str(ltime[-4])) < 2 else ltime[-4]
        s = "0{}".format(ltime[-3]) if len(str(ltime[-3])) < 2 else ltime[-3]
        oled.text("{}   {}:{}:{}".format(cfgget("nwmd")[0], h, m, s), 0, 0)

    def __page_bar(self):
        """Generates page indicator bar"""
        plen = int(self.width / len(self.page_callback_list))
        # Draw page indicators
        for p in range(0, self.width, plen):
            oled.rect(p, self.height - 4, plen - 1, 4)
        # Draw active page indicator
        #oled.line(self.active_page * plen + 1, self.height - 2, self.active_page * plen + plen - 1, self.height - 2)
        oled.rect(self.active_page * plen + 1, self.height - 3, plen - 2, 2)

    def show_page(self):
        """Re/draw active page"""
        oled.clean()
        self.__page_header()
        self.__page_bar()
        self.page_callback_list[self.active_page]()
        oled.show()

    def next_page(self):
        """Change page - next & Draw"""
        self.active_page += 1
        if self.active_page > len(self.page_callback_list) - 1:
            self.active_page = 0
        self.show_page()
        return self.active_page

    def previous_page(self):
        """Change page - previous & Draw"""
        self.active_page -= 1
        if self.active_page < 0:
            self.active_page = len(self.page_callback_list) - 1
        self.show_page()
        return self.active_page


#################################
#        PAGE DEFINITIONS       #
#################################

""" Create "user" pages here """


def simple_page():
    try:
        oled.text('Hello World', 20, 30)
    except Exception as e:
        return str(e)
    return True


def adc_page():
    def __visualize(p):
        max_w = 50
        percent = p * 0.01
        size = round(percent * max_w)
        size = 1 if size < 1 else size
        # Visualize percentage
        oled.rect(0, 9, size, size, fill=True)
        # Visualize percentages scale
        steps = int(max_w/10)
        for scale in range(steps, max_w+1, steps):
            if scale < size:
                oled.rect(0, 9, scale, scale, state=0)
            else:
                oled.rect(0, 9, scale, scale, state=1)

    data = SmartADC.get_singleton(physical_pin('genadc')).get()
    __visualize(p=data['percent'])
    oled.text("{} %".format(data['percent']), 65, 20)
    oled.text("{} V".format(data['volt']), 65, 40)
    return True


def sys_page():
    oled.text("FUID: {}".format(cfgget("devfid")), 0, 15)
    oled.text("IP: {}".format(cfgget("devip")), 0, 25)
    fm = mem_free()
    kb, byte = int(fm / 1000), int(fm % 1000)
    oled.text("Mem: {}kb {}b".format(kb, byte), 0, 35)
    oled.text("V: {}".format(cfgget("version")), 0, 45)
    return True


#################################
# PAGE GUI CONTROLLER FUNCTIONS #
#################################


def pageui():
    """ INIT PageUI - add page definitions here """
    pages = [sys_page, simple_page, adc_page]
    if PageUI.PAGE_UI_OBJ is None:
        PageUI(pages, 128, 64)
    PageUI.PAGE_UI_OBJ.show_page()


def next_page():
    return PageUI.PAGE_UI_OBJ.next_page()


def prev_page():
    return PageUI.PAGE_UI_OBJ.previous_page()


#######################
# LM helper functions #
#######################


def lmdep():
    return 'LM_oled'


def help():
    return 'pageui', 'next_page', 'prev_page',\
           'INFO: OLED Module for SSD1306'
