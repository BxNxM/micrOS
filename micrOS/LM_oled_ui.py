from ConfigHandler import cfgget
from gc import mem_free
from utime import localtime
from network import WLAN, STA_IF
import LM_oled as oled
from Common import SmartADC
from LogicalPins import physical_pin
from Network import ifconfig


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
        self.show_msg = None
        self.msg_effect = False
        self.oled_state = True
        PageUI.PAGE_UI_OBJ = self

    def __page_header(self):
        """Generates header bar with NW mode + Clock + wifi rssi"""

        def __draw_rssi():
            value = WLAN(STA_IF).status('rssi')
            show_range = round(((value + 91) / 30) * 8)  # pixel height 8
            oled.line(self.width - 10, 8, self.width - 8, 8)
            oled.line(self.width - 18, 1, self.width, 1)
            for _h in range(0, show_range):
                oled.line(118 - _h, 8 - _h, 120 + _h, 8 - _h)

        try:
            __draw_rssi()
        except:
            pass
        ltime = localtime()
        h = "0{}".format(ltime[-5]) if len(str(ltime[-5])) < 2 else ltime[-5]
        m = "0{}".format(ltime[-4]) if len(str(ltime[-4])) < 2 else ltime[-4]
        s = "0{}".format(ltime[-3]) if len(str(ltime[-3])) < 2 else ltime[-3]
        nwmd = ifconfig()[0]
        nwmd = nwmd[0] if len(nwmd) > 0 else "0"
        oled.text("{}   {}:{}:{}".format(nwmd, h, m, s), 0, 0)

    def __page_bar(self):
        """Generates page indicator bar"""
        plen = int(self.width / len(self.page_callback_list))
        # Draw page indicators
        for p in range(0, self.width, plen):
            oled.rect(p, self.height - 4, plen - 1, 4)
        # Draw active page indicator
        oled.rect(self.active_page * plen + 1, self.height - 3, plen - 2, 2)

    def __msgbox(self):
        def __effect():
            self.msg_effect = not self.msg_effect
            oled.rect(106, 17, 9, 5, state=1, fill=self.msg_effect)
            oled.rect(106, 24, 9, 9, state=1, fill=self.msg_effect)

        msg = self.show_msg
        if msg is None:
            # Check input msg
            return False
        if not self.oled_state:
            # Turn ON oled if msg arrives
            oled.poweron()
            self.oled_state = True

        oled.rect(10, 15, 108, 40, state=1)
        # oled.rect(98, 15, 20, 20, state=1)
        __effect()
        if len(msg) > 10:
            # First line
            oled.text(msg[0:10], 15, 25)
            buff = msg[10:]
            msg = buff[:11] if len(buff) > 12 else buff
        # Second line
        oled.text(msg, 15, 40)
        return True

    def show_page(self):
        """Re/draw active page"""
        oled.clean()
        msg_event = self.__msgbox()
        if self.oled_state:
            self.__page_header()
            self.__page_bar()
            if not msg_event:
                self.page_callback_list[self.active_page]()
            oled.show()

    def control(self, cmd):
        self.show_msg = None
        if cmd.strip() == 'next':
            """Change page - next & Draw"""
            self.active_page += 1
            if self.active_page > len(self.page_callback_list) - 1:
                self.active_page = 0
            self.show_page()
            return self.active_page
        elif cmd.strip() == 'prev':
            """Change page - previous & Draw"""
            self.active_page -= 1
            if self.active_page < 0:
                self.active_page = len(self.page_callback_list) - 1
            self.show_page()
            return self.active_page
        if cmd.strip() == 'on':
            oled.poweron()
            self.oled_state = True
        elif cmd.strip() == 'off':
            oled.poweroff()
            self.oled_state = False


#################################
#        PAGE DEFINITIONS       #
#################################

""" Create "user" pages here """


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
    oled.text(cfgget("devfid"), 0, 15)
    oled.text("  {}".format(ifconfig()[1][0]), 0, 25)
    fm = mem_free()
    kb, byte = int(fm / 1000), int(fm % 1000)
    oled.text("  {}kb {}b".format(kb, byte), 0, 35)
    oled.text("  V: {}".format(cfgget("version")), 0, 45)
    return True


def simple_page():
    try:
        oled.text('micrOS GUI', 20, 30)
    except Exception as e:
        return str(e)
    return True


def template():
    return True

#################################
# PAGE GUI CONTROLLER FUNCTIONS #
#################################


def pageui():
    """ INIT PageUI - add page definitions here """
    pages = [sys_page, simple_page, template, adc_page]
    if PageUI.PAGE_UI_OBJ is None:
        PageUI(pages, 128, 64)
    PageUI.PAGE_UI_OBJ.show_page()


def control(cmd='next'):
    valid_cmd = ('next', 'prev', 'on', 'off')
    if cmd in valid_cmd:
        return PageUI.PAGE_UI_OBJ.control(cmd)
    return 'Invalid command {}! Hint: {}'.format(cmd, valid_cmd)


def msgbox(msg='micrOS msg'):
    PageUI.PAGE_UI_OBJ.show_msg = msg
    PageUI.PAGE_UI_OBJ.show_page()
    return 'Show msg'

#######################
# LM helper functions #
#######################


def lmdep():
    return 'oled'


def help():
    return 'pageui', 'control next/prev/on/off',\
           'msgbox "msg"', 'INFO: OLED Module for SSD1306'
