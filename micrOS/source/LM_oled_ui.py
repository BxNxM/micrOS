from ConfigHandler import cfgget
from utime import localtime
from network import WLAN, STA_IF
import LM_oled as oled
from LogicalPins import physical_pin, pinmap_dump
from Network import ifconfig
from Debug import errlog_add
from machine import Pin
try:
    from gc import mem_free
except:
    from simgc import mem_free  # simulator mode
try:
    import LM_intercon as InterCon
except:
    InterCon = None             # Optional function handling
try:
    from LM_genIO import get_adc
except:
    get_adc = None              # Optional function handling


#################################
# PAGE MANAGER CLASS DEFINITION #
#################################

class PageUI:
    PAGE_UI_OBJ = None

    def __init__(self, page_callbacks, w, h, pwr_sec=None):
        self.active_page = 0
        self.page_callback_list = page_callbacks
        self.width = w
        self.height = h
        self.show_msg = None
        self.blink_effect = False
        self.oled_state = True
        # OK/CENTER button state values
        self.bttn_press_callback = None
        # Intercon connection state values
        self.open_intercons = []
        self.conn_data = "n/a"
        # Create built-in event/button IRQ
        self.irq_ok = False
        self.__create_button_irq()
        # Power saver state machine - turn off sec, deltaT (timirq executor seq loop), counter
        self.pwr_saver_state = [pwr_sec, round(cfgget('timirqseq') / 1000, 2), pwr_sec]
        # Store instance - use as singleton
        PageUI.PAGE_UI_OBJ = self

    #############################
    #        INTERNAL MAGIC     #
    #############################
    def __page_header(self):
        """Generates header bar with NW mode + Clock + wifi rssi"""

        def __draw_rssi():
            value = WLAN(STA_IF).status('rssi')
            show_range = round(((value + 91) / 30) * 8)  # pixel height 8
            oled.line(self.width - 10, 8, self.width - 8, 8)
            oled.line(self.width - 18, 1, self.width, 1)
            for _h in range(0, show_range):
                oled.line(118 - _h, 8 - _h, 120 + _h, 8 - _h)

        def __pwr_off():
            x_offset = 29
            sec, _, cnt = self.pwr_saver_state
            if sec is None:
                return
            indicator = round(cnt / sec, 1) * 8       # pixel height 8
            for i in range(indicator):
                oled.line(self.width-x_offset, 6-i, self.width-x_offset-2, 6-i)

        try:
            __draw_rssi()
            __pwr_off()
        except:
            pass

        ltime = localtime()
        h = "0{}".format(ltime[-5]) if len(str(ltime[-5])) < 2 else ltime[-5]
        m = "0{}".format(ltime[-4]) if len(str(ltime[-4])) < 2 else ltime[-4]
        s = "0{}".format(ltime[-3]) if len(str(ltime[-3])) < 2 else ltime[-3]
        nwmd = ifconfig()[0]
        nwmd = nwmd[0] if len(nwmd) > 0 else "0"
        irq_ok = ' ' if self.bttn_press_callback is None else '*' if self.irq_ok else '!'
        oled.text("{} {} {}:{}:{}".format(nwmd, irq_ok, h, m, s), 0, 0)

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
            self.blink_effect = not self.blink_effect
            oled.rect(106, 17, 9, 5, state=1, fill=self.blink_effect)
            oled.rect(106, 24, 9, 9, state=1, fill=self.blink_effect)

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

    def __create_button_irq(self, pinkey='oleduibttn'):
        """Create button press IRQ for OK/Center button"""
        try:
            pin = physical_pin(pinkey)
        except Exception as e:
            msg = '[ERR] Button IRQ:{} {}'.format(pinkey, e)
            pin = None
            errlog_add(msg)
        if pin:
            pin_obj = Pin(pin, Pin.IN, Pin.PULL_DOWN)
            # [IRQ] - event type setup
            pin_obj.irq(trigger=Pin.IRQ_RISING, handler=lambda pin: self.control('press'))
            self.irq_ok = True

    def __power_save(self):
        sec, dt, cnt = self.pwr_saver_state
        if sec is None:
            # Power saver off - no auto turn off
            return
        if cnt > 0:
            self.pwr_saver_state[2] = cnt - dt
        else:
            self.control('off')
            self.pwr_saver_state[2] = sec

    #############################
    #       PUBLIC FUNCTIONS    #
    #############################
    def add_page(self, page_callback):
        if page_callback in self.page_callback_list:
            return True
        self.page_callback_list.append(page_callback)
        return True

    def show_page(self):
        """Re/draw active page"""
        oled.clean()
        msg_event = self.__msgbox()
        if self.oled_state:
            self.__page_header()
            self.__page_bar()
            if not msg_event:
                self.page_callback_list[self.active_page]()         # <== Execute page functions
            oled.show()
            self.__power_save()

    def control(self, cmd):
        # Reset power saver counter
        self.pwr_saver_state[2] = self.pwr_saver_state[0]
        # Reset sys msg data
        self.show_msg = None
        # Handle control parameters
        if cmd.strip() == 'press':
            """Simulate button press"""
            self._page_button_press()  # Execute button callback
        elif cmd.strip() == 'next':
            """Change page - next & Draw"""
            self.active_page += 1
            if self.active_page > len(self.page_callback_list) - 1:
                self.active_page = 0
            self.show_page()
            self.bttn_press_callback = None
            self.conn_data = 'n/a'
        elif cmd.strip() == 'prev':
            """Change page - previous & Draw"""
            self.active_page -= 1
            if self.active_page < 0:
                self.active_page = len(self.page_callback_list) - 1
            self.show_page()
            self.bttn_press_callback = None
            self.conn_data = 'n/a'
        elif cmd.strip() == 'on':
            oled.poweron()
            self.oled_state = True
        elif cmd.strip() == 'off':
            oled.poweroff()
            self.oled_state = False
            self.bttn_press_callback = None
        return "page: {} pwr: {}".format(self.active_page, self.oled_state)

    def _page_button_press(self):
        """
        Create OK/Center button
        - any page can register callback function
        what will be called by this function (button pressed)
        """
        if self.bttn_press_callback is None:
            return
        # Execute callback
        self.bttn_press_callback()
        # Clean bttn press event - delete callback
        self.bttn_press_callback = None

    def set_press_callback(self, callback):
        """Button callback setter method + draw button"""
        self.bttn_press_callback = callback

        # Draw button
        posx, posy = 44, 45
        oled.rect(posx-4, posy-4, 48, 15)
        oled.text("press", posx, posy)

        # Draw press effect - based on button state: S
        if "S:1" in self.conn_data:
            self.blink_effect = True
        elif "S:0" in self.conn_data:
            self.blink_effect = False
        else:
            # # Draw press effect - blink
            self.blink_effect = not self.blink_effect
        oled.rect(posx-3, posy-3, 48-2, 15-2, self.blink_effect)

    def intercon_page(self, host, cmd):
        """Generic interconnect page core - create multiple page with it"""
        posx = 5
        posy = 12

        def button():
            # BUTTON CALLBACK - INTERCONNECT execution
            self.open_intercons.append(host)
            try:
                # Send CMD to other device & show result
                data = InterCon.send_cmd(host, cmd)
                self.conn_data = ''.join(data).replace(' ', '')     # squish data to print
            except Exception as e:
                self.conn_data = str(e)
            self.open_intercons.remove(host)

        # Check open host connection
        if host in self.open_intercons:
            return
        # Draw host + cmd details
        oled.text(host, 0, posy)
        oled.text(cmd, posx, posy+10)
        oled.text(self.conn_data, posx, posy + 20)
        # Set button press callback (+draw button)
        self.set_press_callback(button)


#################################
#        PAGE DEFINITIONS       #
#################################

def _sys_page():
    """
    System basic information page
    """
    oled.text(cfgget("devfid"), 0, 15)
    oled.text("  {}".format(ifconfig()[1][0]), 0, 25)
    fm = mem_free()
    kb, byte = int(fm / 1000), int(fm % 1000)
    oled.text("  {}kb {}b".format(kb, byte), 0, 35)
    oled.text("  V: {}".format(cfgget("version")), 0, 45)
    return True


def _intercon_cache():
    if InterCon is None:
        return False
    line_start = 15
    line_cnt = 1
    line_limit = 3
    oled.text("InterCon cache", 0, line_start)
    if sum([1 for _ in InterCon.dump()]) > 0:
        for key, val in InterCon.dump().items():
            key = key.split('.')[0]
            val = '.'.join(val.split('.')[-2:])
            oled.text(" {} {}".format(val, key), 0, line_start+(line_cnt*10))
            line_cnt = 1 if line_cnt > line_limit else line_cnt+1
        return True
    oled.text("Empty", 40, line_start+20)
    return True


def _micros_welcome():
    """Template function"""
    def button():
        """Button callback example"""
        oled.text('HELLO :D', 35, 29)
        oled.show()

    try:
        oled.text('micrOS GUI', 30, 15)
        PageUI.PAGE_UI_OBJ.set_press_callback(button)
    except Exception as e:
        return str(e)
    return True


def _adc_page():
    """
    ADC value visualizer
    """
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

    def __rgb_brightness(percent):
        from sys import modules
        if 'LM_rgb' in modules.keys():
            from LM_rgb import brightness
            if percent is None:
                return
            brightness(percent, smooth=True)

    data = {'percent': 'null', 'volt': 'null'}
    if get_adc is not None:
        data = get_adc(physical_pin('genadc'))
    __visualize(p=data['percent'])
    oled.text("{} %".format(data['percent']), 65, 20)
    oled.text("{} V".format(data['volt']), 65, 40)
    __rgb_brightness(data['percent'])
    return True

#################################
# PAGE GUI CONTROLLER FUNCTIONS #
#   USED IN MICROS SHELL/IRQs   #
#################################


def pageui(pwr_sec=None):
    """ INIT PageUI - add page definitions here - interface"""
    pages = [_sys_page, _intercon_cache, _adc_page, _micros_welcome]      # <== Add page function HERE
    if PageUI.PAGE_UI_OBJ is None:
        PageUI(pages, 128, 64, pwr_sec)
    PageUI.PAGE_UI_OBJ.show_page()


def control(cmd='next'):
    """OLED UI control functions interface"""
    valid_cmd = ('next', 'prev', 'press', 'on', 'off')
    if cmd in valid_cmd:
        return PageUI.PAGE_UI_OBJ.control(cmd)
    return 'Invalid command {}! Hint: {}'.format(cmd, valid_cmd)


def msgbox(msg='micrOS msg'):
    """POP-UP message function - interface"""
    PageUI.PAGE_UI_OBJ.show_msg = msg
    PageUI.PAGE_UI_OBJ.show_page()
    return 'Show msg'


def intercon_genpage(cmd=None):
    """
    Create intercon pages dynamically :)
    based on cmd value.
    cmd: host hello / host system clock
    """
    cmd = cmd.replace(",", '')      # TODO: Command parsing/joining workaround (exec LM core)
    raw = cmd.split()
    host = raw[0]
    cmd = ' '.join(raw[1:])
    if PageUI.PAGE_UI_OBJ is None:
        # Auto init UI
        pageui()
    try:
        # Create page for intercon command
        PageUI.PAGE_UI_OBJ.add_page(lambda: PageUI.PAGE_UI_OBJ.intercon_page(host, cmd))
    except Exception as e:
        return str(e)
    return True


#######################
# LM helper functions #
#######################

def lmdep():
    """
    Show Load Module dependency
    - List of load modules used by this application
    :return: tuple
    """
    return 'oled', 'intercon', 'genIO'


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    pin_map = oled.pinmap()
    pin_map.update(pinmap_dump('oleduibttn'))
    return pin_map


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'pageui pwr_sec=None/int(sec)', 'control next/prev/press/on/off',\
           'msgbox "msg"', 'intercon_genpage "host cmd"',\
           'pinmap', 'INFO: OLED Module for SSD1306'
