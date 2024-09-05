from utime import localtime
import uasyncio as asyncio
from network import WLAN, STA_IF
from Common import syslog, micro_task
from Network import ifconfig
from Config import cfgget
from Types import resolve

from LM_system import top, memory_usage
try:
    import LM_intercon as InterCon
except:
    InterCon = None             # Optional function handling


DEBUG = False

#################################
#          Frame classes        #
#################################

class BaseFrame:

    def __init__(self, display, width, height, x=0, y=0):
        """Basic pixel frame properties"""
        self.display = display
        self.w = width
        self.h = height
        self.x = x
        self.y = y
        self.selected = False

    def clean(self):
        """Clean pixel frame area"""
        self.display.rect(x=self.x, y=self.y, w=self.w, h=self.h, state=0, fill=True)
        if self.selected or DEBUG:
            self.display.rect(x=self.x, y=self.y, w=self.w, h=self.h, state=1, fill=False)

    def select(self, x, y):
        """Select frame based on x,x aka cursor"""
        if self.x <= x <= self.x + self.w and self.y-1 <= y < self.y-1 + self.h:
            self.selected = True
            self.display.rect(x=self.x, y=self.y, w=self.w, h=self.h, state=1, fill=False)
        else:
            self.selected = False
        return self.selected


class Frame(BaseFrame):
    # Collect all Frame objects
    FRAMES = set()
    HIBERNATE = False

    def __init__(self, display, callback, width, height, x=0, y=0, tag=""):
        super().__init__(display, width, height, x, y)
        self.callback = callback
        self._taskid = None
        self.paused = False
        self.tag = tag
        Frame.FRAMES.add(self)

    def draw(self):
        """
        Redraw frame
        """
        self.clean()
        # Pass adjusted useful area
        self.callback(self.display, self.w-2, self.h-2, self.x+1, self.y+1)
        self.display.show()
        return f"Draw {self._taskid} frame"

    async def _task(self, period_ms):
        """
        Frame task - draw executor
        """
        with micro_task(tag=self._taskid) as my_task:
            s = None
            while True:
                if s != self.paused:
                    my_task.out = 'paused' if self.paused else f'refresh: {period_ms} ms'
                    s = self.paused
                if self.paused:
                    await asyncio.sleep_ms(period_ms)   # extra wait in paused mode
                else:
                    # Draw/Refresh frame
                    self.draw()
                # Async sleep - feed event loop
                await asyncio.sleep_ms(period_ms)

    def run(self, id, period_ms=500):
        # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
        self._taskid = f"oledui.{id}"
        state = micro_task(tag=self._taskid, task=self._task(period_ms=period_ms))
        return "Starting" if state else "Already running"

    @staticmethod
    def pause_all():
        Frame.HIBERNATE = True
        for frame in Frame.FRAMES:
            frame.paused = True

    @staticmethod
    def resume_all():
        Frame.HIBERNATE = False
        for frame in Frame.FRAMES:
            frame.paused = False
            frame.draw()


class Cursor(BaseFrame):
    TAG = ""                # Selected/Active frame tag

    def __init__(self, display, width, height, x=0, y=0):
        self.pos_xy = (0, 0)
        super().__init__(display, width, height, x, y)

    def draw(self):
        x, y = self.pos_xy
        self.display.rect(x-1, y+1, 2, 2, 1)  # draw new cursor
        self.display.show()

    def update(self, x, y):
        """
        Update cursor with
        - cursor position
        - frame selection
        """
        self.clean()
        self.pos_xy = (x, y)
        for frame in Frame.FRAMES:
            if frame.select(x, y):
                Cursor.TAG = frame.tag
        self.draw()

    def clean(self):
        """
        Clean previous cursor
        """
        x, y = self.pos_xy
        self.display.rect(x - 1, y + 1, 2, 2, 0)


class HeaderBarFrames:

    def __init__(self, display, cursor_draw, timer=30, tag="header"):
        self.display = display
        self.cursor_draw = cursor_draw
        self.timer = [timer, timer]     #[0] default value, [1] timer cnt
        # Create header: time frame
        time_frame = Frame(self.display, self._time, width=65, height=10, x=32, y=0, tag=tag)
        time_frame.run("time", period_ms=1000)
        # Create header: cpu,mem metrics
        cpu_mem_frame = Frame(self.display, self._cpu_mem, width=10, height=10, x=116, y=0, tag=tag)
        cpu_mem_frame.run('cpu_mem', period_ms=2100)
        # Create header: wifi rssi
        rssi_frame = Frame(self.display, self._rssi, width=10, height=10, x=0, y=0, tag=tag)
        rssi_frame.run('rssi', period_ms=4200)
        # Create header: timer frame (auto sleep)
        if isinstance(timer, int):
            timer_frame = Frame(self.display, self._timer, width=8, height=10, x=14, y=0, tag=tag)
            timer_frame.run("timer", period_ms=int((timer*1000)/24))

    def _time(self, display, w, h, x, y):
        # Built-in: time widget frame
        ltime = localtime()
        try:
            h = f"0{ltime[-5]}" if len(str(ltime[-5])) < 2 else ltime[-5]
            m = f"0{ltime[-4]}" if len(str(ltime[-4])) < 2 else ltime[-4]
            s = f"0{ltime[-3]}" if len(str(ltime[-3])) < 2 else ltime[-3]
        except:
            h, m, s = 0, 0, 0
        display.text(f"{h}:{m}:{s}", x, y)
        self.cursor_draw()

    def _timer(self, display, w=5, h=5, x=0, y=0):
        # Built-in: timer widget frame
        _view = int(w * h * (self.timer[1] / self.timer[0]))
        _complete_lines_cnt = int(_view / w)             # complete lines number
        _sub_line_x = _view - (_complete_lines_cnt * w)  # incomplete line width
        for _l in range(0, h):
            if _l < _complete_lines_cnt:
                display.line(x, y+_l, x+w, y+_l)
            else:
                display.line(x, y+_l, x+_sub_line_x, y+_l)
                break
        self.timer[1] -= 1
        if self.timer[1] <= 0:
            # Pause All Frame tasks
            Frame.pause_all()
            self.display.poweroff()
            self.reset_timer()

    def reset_timer(self):
        self.timer[1] = self.timer[0]

    def _cpu_mem(self, display, w, h, x, y):
        # Built-in: cpu_mem widget frame
        sys_usage = top()
        cpu = sys_usage.get('CPU load [%]', 100)
        cpu = 100 if cpu > 100 else cpu  # limit cpu overload in visualization
        mem = sys_usage.get('Mem usage [%]', 100)
        _cpu_limit, _mem_limit = cpu > 90, mem > 70  # fill indicator (limit)
        _cpu, _mem = int(h * (cpu / 100)), int(h * (mem / 100))
        width = int((w-2)/2)
        display.rect(x, y+h-1-_cpu, w=width, h=_cpu, fill=_cpu_limit)  # cpu usage indicator
        display.rect(x+(width+2), y+h-_mem, w=width, h=_mem, fill=_mem_limit)  # memory usage indicator
        self.cursor_draw()

    def _rssi(self, display, w, h, x, y):
        # Built-in: _rssi widget frame
        w, h = w-1, h-1     # index correction from 0
        try:
            value = WLAN(STA_IF).status('rssi')
        except:
            value = -1
        show_range = round(((value + 91) / 30) * h+1)  # pixel height 8
        display.line(x, y, x+2, y)
        for _h in range(0, show_range):
            start_x = x
            start_y = y + h - _h
            end_x = x + w - (h-_h)
            end_y = y + h - _h
            display.line(start_x, start_y, end_x, end_y)
        self.cursor_draw()

class AppFrame(Frame):
    PAGES = []

    def __init__(self,  display, cursor_draw, width, height, x=0, y=0, tag="app", page=0):
        super().__init__(display, None, width, height, x=x, y=y, tag=tag)
        self.active_page_index = page
        self.cursor_draw = cursor_draw
        self.callback = self.application

    def application(self, display, width, height, x=0, y=0):
        if len(AppFrame.PAGES) > 0:
            page = AppFrame.PAGES[self.active_page_index]
            # Pass adjusted useful area
            # TODO: check if page is async... (advanced task embedding)
            try:
                page(display, width, height, x, y)
            except Exception as e:
                display.text(e, x, y)
        self.cursor_draw()

    @staticmethod
    def add_page(page):
        if callable(page):
            AppFrame.PAGES.append(page)     # add single page
            return True
        if isinstance(page, list):
            AppFrame.PAGES += page          # add list of pages
            return True
        return False

    def next(self):
        pages_cnt = len(AppFrame.PAGES) - 1
        self.active_page_index += 1
        if self.active_page_index > pages_cnt:
            self.active_page_index = 0

    def previous(self):
        pages_cnt = len(AppFrame.PAGES) - 1
        self.active_page_index -= 1
        if self.active_page_index < 0:
            self.active_page_index = pages_cnt


#################################################################################
#                                    PageUI manager                             #
#                                    (Frame manager)                            #
#################################################################################

class PageUI:
    DISPLAY = None
    PAGE_UI_OBJ = None

    def __init__(self, w=128, h=64, page=0, poweroff=None, oled_type='ssd1306', control=None, haptic=False):
        """
        :param w: screen width
        :param h: screen height
        :param page: start page index
        :param poweroff: power off after given seconds
        :param oled_type: ssd1306 or sh1106
        :param control: trackball / None
        """
        if oled_type.strip() in ('ssd1306', 'sh1106'):
            if oled_type.strip() == 'ssd1306':
                import LM_oled as oled
            else:
                import LM_oled_sh1106 as oled
            PageUI.DISPLAY = oled
            oled.load(width=w, height=h, brightness=50)
        else:
            syslog(f"Oled UI unknown oled_type: {oled_type}")
            Exception(f"Oled UI unknown oled_type: {oled_type}")
        if control is not None and control.strip() == "trackball":
            from LM_trackball import subscribe_event
            subscribe_event(self._control_clb)
        self.haptic = None
        if haptic:
            try:
                from LM_haptic import tap
                self.haptic = tap
            except Exception as e:
                syslog(f"[ERR] oledui haptic: {e}")
        self.width = w
        self.height = h
        self.timer = poweroff
        # Store persistent frame objects
        self.cursor = None
        self.header_bar = None
        self.app_frame = None
        self.page_bar = None
        # Save
        PageUI.PAGE_UI_OBJ = self
        self.DISPLAY.clean()

    def create(self):
        self.DISPLAY.text("Boot UI", 36, 28)
        self.DISPLAY.show()
        self.cursor = Cursor(PageUI.DISPLAY, width=2, height=2, x=0, y=0)
        self.header_bar = HeaderBarFrames(PageUI.DISPLAY, timer=self.timer, cursor_draw=self.cursor.draw)
        self.app_frame = AppFrame(PageUI.DISPLAY, self.cursor.draw, width=self.width, height=self.height-15, x=0, y=self.height-54)
        self.app_frame.run("page", period_ms=900)
        self.page_bar = self.pageBar()

    def _control_clb(self, params):
        """
        {"X": trackball.posx, "Y": trackball.posy,
            "S": trackball.toggle, "action": trackball.action}
        """
        action = params.get('action', None)
        if action is not None:
            x, y = params['X'], self.height-params['Y']                         # invert Y axes
            self.cursor.update(x, y)
            lut = {"right": "next", "left": "prev"}
            self.control(lut.get(action, action))
            self.DISPLAY.show()

    def control(self, action, force=False):
        # Wake on action
        if Frame.HIBERNATE:
            Frame.resume_all()
            self.DISPLAY.poweron()
        self.header_bar.reset_timer()
        self.cursor.draw()
        # Enable page lift-right scroll when footer is selected
        if Cursor.TAG == 'footer' or force:
            if callable(self.haptic):
                self.haptic()
            if action == "next":
                self.app_frame.next()
            if action == "prev":
                self.app_frame.previous()
        if action == "off":
            Frame.pause_all()
            self.DISPLAY.poweroff()
        if action == "on":
            Frame.resume_all()
            self.DISPLAY.poweron()
        self.page_bar.draw()

    def pageBar(self):
        def page_indicator(display, w, h, x, y):
            page_cnt = len(AppFrame.PAGES)
            plen = int(round(w / page_cnt))
            """
            # Draw page indicators
            for p in range(0, w, plen):
                display.rect(x+p, y, plen, h)
            """
            # Draw active page indicator
            display.rect(x+self.app_frame.active_page_index*plen+1, y+1, plen-2, h-2, fill=True)
            self.cursor.draw()

        page_bar = Frame(self.DISPLAY, page_indicator, width=self.width, height=5, x=0, y=self.height-5, tag="footer")
        page_bar.draw()
        #page_bar.run("pagebar", 1000)
        return page_bar

    @staticmethod
    def add_page(page):
        return AppFrame.add_page(page)


#################################
#           Default pages       #
#################################

def _system_page(display, w, h, x, y):
    """
    System basic information page
    """
    display.text(cfgget("devfid"), x, y+2)
    display.text(f"  {ifconfig()[1][0]}", x, y+12)
    if memory_usage is not None:
        mem = memory_usage()
        display.text(f"  {mem['percent']}% ({int(mem['mem_used']/1000)}kb)", x, y+22)
    display.text(f"  V: {cfgget('version')}", x, y+32)
    return True

def _intercon_page(display, w, h, x, y):
    if InterCon is None:
        return False
    line_limit = 3
    line_start = y+5
    line_cnt = 1
    display.text("InterCon cache", x, line_start)
    if sum([1 for _ in InterCon.host_cache()]) > 0:
        for key, val in InterCon.host_cache().items():
            key = key.split('.')[0]
            val = '.'.join(val.split('.')[-2:])
            display.text(f" {val} {key}", x, line_start + (line_cnt * 10))
            line_cnt += 1
            if line_cnt > line_limit:
                break
        return True
    display.text("Empty", x+40, line_start + 20)
    return True


def _test_page(display, w, h, x, y):
    display.rect(x, y, w, h)
    display.rect(x+2, y+2, w-4, h-4)


def _empty_page(display, w, h, x, y):
    pass

#################################
#         Public features       #
#################################

def load(width=128, height=64, oled_type="sh1106", control='trackball', poweroff=None, haptic=False):
    """
    Create async oled UI
    :param width: screen width in pixels
    :param height: screen height in pixels
    :param oled_type: sh1106 / ssd1306
    :param control: trackball / None
    :param poweroff: power off after given seconds
    :param haptic: enable (True) / disable (False) haptic feedbacks (vibration)
    """
    if PageUI.PAGE_UI_OBJ is None:
        ui = PageUI(width, height, poweroff=poweroff, oled_type=oled_type, control=control, haptic=haptic)
        # Add default pages...
        ui.add_page([_system_page, _intercon_page, _test_page, _empty_page])
        ui.create()         # Header(4), AppPage(1), PagerIndicator
        return "PageUI was created"
    return "PageUI was already created"


def control(cmd="next"):
    if cmd in ("next", "prev", "on", "off"):
        PageUI.PAGE_UI_OBJ.control(cmd, force=True)
        return cmd
    return f"Unknown action: {cmd}"


def msgbox(msg='micrOS msg'):
    """
    POP-UP message function
    :param msg: message string
    """
    pass


def debug():
    global DEBUG
    DEBUG = not DEBUG
    return DEBUG


def help(widgets=False):
    """
    New generation of oled_ui
    - with async frames
    """
    return resolve(
        ("load width=128 height=64 oled_type='sh1106/ssd1306' control='trackball' poweroff=None/sec haptic=False",
                  "BUTTON control cmd=<prev,next,on,off>",
                  "BUTTON debug"),
        widgets=widgets)
