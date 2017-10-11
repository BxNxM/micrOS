import ssd1306
import machine
import time
# framebuf quickguide: http://docs.micropython.org/en/latest/wipy/library/framebuf.html

class oled(ssd1306.SSD1306_I2C):

    def __init__(self, width=128, height=64, i2c=None, addr=0x3c, external_vcc=False):
        if i2c is None:
            i2c = self.internal_i2c()
        super().__init__(width, height, i2c, addr, external_vcc)

    def internal_i2c(self, scl_pin=5, sda_pin=4):
        # I2C BUS INICIALIZATION:
        # init the i2c bus - SCL - gpio5 on pinout: D1, SDA - gpio4 on board: D2
        try:
            i2c = machine.I2C(scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin))
            device_ids = i2c.scan()
        except Exception as e:
            raise Exception("EXCEPTION i2c: " + str(e))

        if len(device_ids) != 0:
            print("I2C INSTANCE: " + str(i2c))
            print("AVAIBLE DEVICES: " + str(device_ids))
            return i2c
        else:
            raise Exception("DEVICE IS NOT CONNECTED!")

    def display(self, option):
        if option == "poweron":
            self.poweron()
        elif option == "poweroff":
            self.poweroff()

    def pixel(self, x, y, col):
        super().pixel(x, y, col)

    def text(self, string, x, y, col=1):
        super().text(string, x, y, col)

    def line(self, xy_start, xy_end, col=1):
        self.framebuf.line(xy_start[0], xy_start[1], xy_end[0], xy_end[1], col)

    def rect(self, x, y, width, height, col=1):
        self.framebuf.rect(x, y, width, height, col)

    def fill_rect(self, x, y, width, height, col=1):
        self.framebuf.fill_rect(x, y, width, height, col)

    def text(self, string, x, y, col=1):
        text_size = 8
        self.fill_rect(x, y, text_size*len(string), text_size, col=0)
        super().text(string, x, y, col)

# demo
'''
instance = oled()
instance.pixel(10, 10, 1)
instance.show()
instance.line((0,0), (10,10))
instance.line((0,0), (10,0))
instance.show()
instance.text("test1", 20, 20)
instance.show()
instance.rect(60, 30, 20, 20)
instance.show()
instance.fill_rect(90, 40, 20, 20)
instance.show()
'''
class GUI(oled):

    def __init__(self, width=128, height=64, i2c=None, addr=0x3c, external_vcc=False):
        super().__init__(width, height, i2c, addr, external_vcc)
        # page state - page_manager
        self.page_index = 0
        self.previous_page_index = 0
        self.isfirst_call = True
        self.page_manager_except = False

    # TOP RSSI VIEWER
    def rssi_bar(self, value, bar_height=3):
        width = int(self.width / 4) - 2
        bar_steps = 3
        bar_steps_width = int(width / bar_steps)
        # clean rssi bar
        self.fill_rect(0, 0, width, bar_height, col=0)
        # draw_frame
        self.line(xy_start=(0, 0), xy_end=(width, 0))
        self.line(xy_start=(0, bar_height), xy_end=(width, bar_height))
        self.line(xy_start=(0, 0), xy_end=(0, bar_height))
        self.line(xy_start=(width, 0), xy_end=(width, bar_height))
        # braw rssi bar
        for i in range(0, value):
            x_coord_ = int(i * bar_steps_width)
            self.fill_rect(x_coord_, 0, bar_steps_width, bar_height, col=1)
        # draw rest of the grid - vertical lines
        for value in range(1, 3):
            self.line(xy_start=(value*bar_steps_width, 0), xy_end=(value*bar_steps_width, bar_height), col=0)

    # BOTTOM PAGE VIEWER
    def page_bar(self, all_page, actual_page, bar_height=4):
        x_step = (self.width)/all_page
        # CLEAN PREVIOUS BAR AREA
        self.fill_rect(0, self.height-bar_height, self.width, bar_height, col=0)
        self.fill_rect(0, self.height-bar_height, self.width, bar_height, col=1)
        # DRAW BAR GRID
        for i in range(0, all_page):
            x_coord_ = int(i * x_step)
            x_coord = int(actual_page * x_step)
            if x_coord_ != x_coord:
                self.fill_rect(x_coord_+1, self.height-bar_height+1, int(x_step)-1, bar_height-2, col=0)
        # DRAW STATUS
        self.line(xy_start=(127, self.height-bar_height), xy_end=(127, self.height), col=1)

    # use this function in loop
    def page_manager(self, page_def_list, button_obj_read, wifi_rssi=0):
        # clean if exception happened
        if self.page_manager_except:
            self.text("           ")
        # handle pages functions
        index_buff = self.page_index
        if not self.isfirst_call:
            # read button - if true increase page index
            print(">>> read button")
            self.page_index+=button_obj_read()[1]
            #print(">>> read button - button index: " + str(self.page_index))
            if self.page_index > len(page_def_list)-1:
                self.page_index = 0
        else:
            self.isfirst_call = False
        # if button was pressed - page goues up to down
        self.button_indicator(index_buff)
        # clean full page if page is changed
        if self.page_index != self.previous_page_index:
            print(">>> clean screen")
            self.fill_rect(0, 0, self.width-1, self.height, col=0)
            self.previous_page_index = self.page_index
        # draw page_bar
        print(">>> draw page_bar")
        self.page_bar(len(page_def_list), self.page_index)
        #print(">>> draw rssi bar")
        self.rssi_bar(wifi_rssi)
        # run page
        print(">>> draw page" + str(page_def_list[self.page_index]))
        try:
            page_def_list[self.page_index](self)
            # call given function page
            self.page_manager_except = False
        except Exception as e:
            if "memory allocation failed" in str(e):
                pass
            self.page_manager_except = True
            print("PAGE EXCEPTION {}".format(str(e)))
            text = "EXCEPTION {}".format(self.page_index)
            self.text(text)
        finally:
            self.show()

    def  button_indicator(self, index_buff):
        # if button was pressed - page goues up to down
        x = 46
        y = 24
        width = 31
        height = 15
        if index_buff < self.page_index:
            self.fill_rect(x,y, width, height, col=0)
            self.text("-->", x=50, y=28)
            self.rect(x,y, width, height)
            self.show()
        elif index_buff > self.page_index:
            self.fill_rect(x,y, width, height, col=0)
            self.text("<--", x=50, y=28)
            self.rect(x,y, width, height)
            self.show()

    def draw_page_function(self, page, wifi_rssi=0):
        #print(">>> draw rssi bar")
        self.rssi_bar(wifi_rssi)
        try:
            page(self)
            self.show()
        except Exception as e:
            print("draw_page_function EXCEPTION: " + str(e))

#simulate
def button():
    time.sleep(0.5)
    return True, 1
    #return False, 0

# DEMO
def page0_demo(oled_panel):
    text="Page 0 width"
    oled_panel.text(text, x=10, y=10)
    text="page_bar"
    oled_panel.text(text, x=10, y=20)
def page1_demo(oled_panel):
    text="Page 1 width"
    oled_panel.text(text, x=10, y=10)
    text="Page 1.1 width"
    oled_panel.text(text, x=10, y=10)
    text="page_bar"
    oled_panel.text(text, x=10, y=20)
def page2_demo(oled_panel):
    text="Page 2 width"
    oled_panel.text(text, x=10, y=10)
    text="page_bar"
    oled_panel.text(text, x=10, y=20)

def rssi_bar_demo(oled_frame):
    for k in range (0, 3):
        for i in range(0, 4):
            oled_frame.rssi_bar(value=i, bar_height=3)
            oled_frame.show()
            time.sleep(0.5)

def page_bar_demo(oled_frame):
    for k in range(2, 10):
        for i in range(0, k):
            oled_frame.page_bar(k, i)
            oled_frame.show()
            time.sleep(1)

def page_manager_demo(oled_frame):
    page_list = []
    page_list.append(page0_demo)
    page_list.append(page1_demo)
    page_list.append(page2_demo)
    while True:
        oled_frame.page_manager(page_list, button)
        time.sleep(1)


#oled_frame = GUI()
#rssi_bar_demo(oled_frame)
#page_bar_demo(oled_frame)
#page_manager_demo(oled_frame)
#oled_frame.draw_page_function(page0_demo)



