from utime import localtime, ticks_ms, ticks_diff
import uasyncio as asyncio
from network import WLAN, STA_IF
from Common import syslog, micro_task, manage_task
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
        self.display = display      # Display object
        self.w = width              # Frame width
        self.h = height             # Frame height
        self.x = x                  # Frame start X
        self.y = y                  # Frame start Y
        self.selected = False       # Store frame instance selection - updated by Cursor
        self.paused = False         # Async task pause feature (Frame class)

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

    def pause(self, state=None):
        """Used by child classes to control internal execution loop state"""
        if state is None:
            return self.paused
        self.paused = state
        return self.paused


class Frame(BaseFrame):
    # Collect all created Frame objects
    FRAMES = set()
    HIBERNATE = False

    def __init__(self, display, callback, width, height, x=0, y=0, tag="", hover_clb=None, press_clb=None):
        super().__init__(display, width, height, x, y)
        # Store callbacks
        self.callback = callback        # Main callback - draw or run
        self.hover_clb = hover_clb      # Hover callback - optional
        self.press_clb = press_clb      # Press callback - optional
        self.tag = tag                  # used for frame identification
        self._taskid = None             # used for task identification
        Frame.FRAMES.add(self)          # Store - managed frames

    def draw(self):
        """
        Redraw frame
        """
        self.clean()
        # Pass adjusted useful area
        try:
            self.callback(self.display, self.w - 2, self.h - 2, self.x + 1, self.y + 1)
        except Exception as e:
            syslog(f"[ERR] Frame clb: {e}")
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

    def run(self, tid, period_ms=500):
        """
        Start registered callback frame task
        """
        # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
        self._taskid = f"oledui.{tid}"
        state = micro_task(tag=self._taskid, task=self._task(period_ms=period_ms))
        return "Starting" if state else "Already running"

    def hover(self):
        """
        Called by Cursor
        """
        if PopUpFrame.INSTANCE is None:
            return False
        if callable(self.hover_clb):
            PopUpFrame.INSTANCE.run(self.hover_clb)
            return True
        return False

    def press(self):
        """
        Called by Cursor / PageUI control
        """
        if PopUpFrame.INSTANCE is None:
            return False
        if callable(self.press_clb):
            PopUpFrame.INSTANCE.run(self.press_clb)
            return True
        return False

    @staticmethod
    def pause_all():
        """
        Pause all managed frames
        """
        Frame.HIBERNATE = True
        for frame in Frame.FRAMES:
            frame.pause(True)

    @staticmethod
    def resume_all():
        """
        Resume all managed frames
        """
        Frame.HIBERNATE = False
        for frame in Frame.FRAMES:
            frame.pause(False)
            frame.draw()

    @staticmethod
    def get_frame(tag):
        """
        Get frame by tag
        """
        for frame in Frame.FRAMES:
            if frame.tag == tag:
                return frame


class Cursor(BaseFrame):
    TAG = ""                # Selected/Active frame tag

    def __init__(self, display, width, height, x=0, y=0):
        super().__init__(display, width, height, x, y)
        self.pos_xy = (0, 0)

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
                # Frame was found
                if frame.tag != Cursor.TAG:
                    # Change event
                    Cursor.TAG = frame.tag
                    has_hover = frame.hover()
                    if not has_hover:
                        PopUpFrame.INSTANCE.cancel()
        self.draw()

    def clean(self):
        """
        Clean previous cursor
        """
        x, y = self.pos_xy
        self.display.rect(x - 1, y + 1, 2, 2, 0)


class HeaderBarFrames:

    def __init__(self, display, cursor_draw, timer=30):
        self.display = display
        self.cursor_draw = cursor_draw
        self.timer = [timer, timer]     #[0] default value, [1] timer cnt
        # Create header: time frame
        time_frame = Frame(self.display, self._time, width=66, height=10, x=32, y=0, tag="time")
        time_frame.run("time", period_ms=1000)
        # Create header: cpu,mem metrics
        cpu_mem_frame = Frame(self.display, self._cpu_mem, width=10, height=10, x=118, y=0, tag="cpu_mem",
                              hover_clb=self._cpu_mem_hover)
        cpu_mem_frame.run('cpu_mem', period_ms=2100)
        # Create header: wifi rssi
        rssi_frame = Frame(self.display, self._rssi, width=10, height=10, x=0, y=0, tag="rssi",
                           hover_clb=self._rssi_hover)
        rssi_frame.run('rssi', period_ms=4200)
        # Create header: timer frame (auto sleep)
        if isinstance(timer, int):
            timer_frame = Frame(self.display, self._timer, width=8, height=10, x=14, y=0, tag="timer",
                                hover_clb=self._timer_hover)
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

    def _timer_hover(self, display, w, h, x, y):
        display.text("Power off in", x, y)
        display.text(f"{self.timer[1]} sec", x+10, y+10)
        self.cursor_draw()

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
        y_base = y+h+1
        spacer = 3
        display.rect(x, y_base-_cpu, w=width, h=_cpu, fill=_cpu_limit)  # cpu usage indicator
        display.rect(x+width+spacer, y_base-_mem, w=width, h=_mem, fill=_mem_limit)  # memory usage indicator
        self.cursor_draw()

    def _cpu_mem_hover(self, display, w, h, x, y):
        sys_usage = top()                                   # Get CPU and MEM usage percentage
        mem_kb = int(memory_usage().get("mem_used", 0) / 1000)     # Get MEM usage in kb
        cpu = sys_usage.get('CPU load [%]', 100)
        mem = sys_usage.get('Mem usage [%]', 100)
        display.text(f"CPU {cpu}%", x, y)
        display.text(f"MEM {mem}%", x, y+10)
        display.text(f"{mem_kb}kb", x+10, y+20)
        self.cursor_draw()

    @staticmethod
    def __rssi_into():
        try:
            value = WLAN(STA_IF).status('rssi')
        except:
            value = -90         # Weak signal in case of error
        min_rssi, max_rssi = -90, -40
        rssi = max(min_rssi, min(max_rssi, value))
        rssi_ratio = ((rssi - min_rssi) / (max_rssi - min_rssi))
        return round(rssi_ratio, 1), value

    def _rssi(self, display, w, h, x, y):
        # Built-in: _rssi widget frame
        x = min(x-1, 0)
        rssi_ratio, _ = self.__rssi_into()
        # Top level line indicator
        display.line(x, y, x+w, y)
        # Calculate lines
        start_line_y = y+h
        end_line_y = y + int(h*(1-rssi_ratio))
        for y_index in range(start_line_y, end_line_y, -1):
            end_x = x + min(w, w-int(w*(y_index/start_line_y))+1)
            display.line(x, y_index, end_x, y_index)
        self.cursor_draw()

    def _rssi_hover(self, display, w, h, x, y):
        rssi_ratio, strength = self.__rssi_into()
        display.text("RSSI info", x, y)
        display.text(f"{rssi_ratio*100}%", x+10, y+10)
        display.text(f"{strength}dBm", x + 10, y + 20)
        self.cursor_draw()


class AppFrame(Frame):
    PAGES = []

    def __init__(self,  display, cursor_draw, width, height, x=0, y=0, tag="app", page=0):
        self.active_page_index = page
        self.cursor_draw = cursor_draw
        super().__init__(display, self._application, width, height, x=x, y=y, tag=tag)

    def _application(self, display, width, height, x=0, y=0):
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


class PageBarFrame(Frame):

    def __init__(self,  display, cursor_draw, app_frame, width, height=5, x=0, y=0, tag="footer"):
        super().__init__(display, self._page_indicator, width, height, x=x, y=y, tag=tag)
        self.cursor_draw = cursor_draw
        self.app_frame = app_frame
        self._trigger_limit_ms = 100

    def _page_indicator(self, display, w, h, x, y):
        if callable(PageUI.HAPTIC):
            PageUI.HAPTIC()
        page_cnt = len(AppFrame.PAGES)
        plen = int(round(w / page_cnt))
        # Draw active page indicator
        display.rect(x+self.app_frame.active_page_index*plen+1, y+1, plen-2, h-2, fill=True)
        self.cursor_draw()


class PopUpFrame(BaseFrame):
    INSTANCE = None

    def __init__(self,  display, cursor_draw, app_frame, width, height=5, x=0, y=0):
        super().__init__(display, width, height, x=x, y=y)
        self.cursor_draw = cursor_draw
        self.app_frame = app_frame
        self.callback = None
        self._taskid = None
        offset = 6
        self._inner_x = self.x + offset
        self._inner_y = self.y + offset
        self._inner_w = self.w - (offset * 2)
        self._inner_h = self.h - (offset * 2)
        PopUpFrame.INSTANCE = self

    def _draw_icon(self):
        # Frame
        #self.display.rect(self._inner_x, self._inner_y, self._inner_w, self._inner_h)
        # Info sign
        x = self._inner_x+self._inner_w-8
        y_dot = self._inner_y+4
        y_base = y_dot+8
        width = 6
        self.display.rect(x, y_dot, width, 6, fill=1)         # .
        self.display.rect(x, y_base, width, 12, fill=1)       # i

    def draw(self):
        """Draw callback"""
        self.clean()
        self._draw_icon()
        if callable(self.callback):
            self.callback(self.display, self._inner_w, self._inner_h, self._inner_x, self._inner_y)
        self.display.show()
        self.cursor_draw()
        return f"Draw {self._taskid} frame"

    def run(self, callback):
        """Start draw task with callback"""
        # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
        self.app_frame.pause(True)
        self.selected = True
        self.callback = callback
        self.draw()

    def textbox(self, msg):
        """
        Draw PopUp Textbox
        """
        # Prepare
        self.app_frame.pause(True)
        self.selected = True
        self.clean()
        self._draw_icon()
        # Draw message
        chunk_size = 13
        char_height= 10
        # Format message: fitting and \n parsing
        msg = msg.split('\n')
        chunks = [line[i:i + chunk_size] for line in msg for i in range(0, len(line), chunk_size)]
        for i, line in enumerate(chunks):
            if i > 2:   # max 3 lines of 13 char
                break
            line_start_y = 4+ char_height * i
            self.display.text(line, self._inner_x, self._inner_y + line_start_y)
        self.display.show()
        return f"Draw textbox frame"

    def cancel(self):
        if self.selected:
            self.selected = False
            self.app_frame.pause(False)
            if self._taskid is not None:
                self._taskid = None
                return manage_task(self._taskid, "kill")
        return True

#################################################################################
#                                    PageUI manager                             #
#                                    (Frame manager)                            #
#################################################################################

class PageUI:
    INSTANCE = None
    DISPLAY = None
    HAPTIC = None

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
        if haptic:
            try:
                from LM_haptic import tap
                PageUI.HAPTIC = tap
            except Exception as e:
                syslog(f"[ERR] oledui haptic: {e}")
        self.width = w
        self.height = h
        self.page = page
        self.timer = poweroff
        self._last_page_switch = ticks_ms()
        # Store persistent frame objects
        self.cursor = None
        self.header_bar = None
        self.app_frame = None
        self.page_bar = None
        self.popup = None
        # Save
        PageUI.INSTANCE = self
        self.DISPLAY.clean()

    def create(self):
        self.DISPLAY.text("Boot UI", 36, 28)
        self.DISPLAY.show()
        # Create managed frames
        self.cursor = Cursor(PageUI.DISPLAY, width=2, height=2, x=0, y=0)
        self.header_bar = HeaderBarFrames(PageUI.DISPLAY, timer=self.timer, cursor_draw=self.cursor.draw)
        self.app_frame = AppFrame(PageUI.DISPLAY, self.cursor.draw, width=self.width,
                                  height=self.height-15, x=0, y=self.height-54, page=self.page)
        self.app_frame.run("page", period_ms=900)
        self.page_bar = PageBarFrame(PageUI.DISPLAY, self.cursor.draw, self.app_frame,
                                     width=self.width, height=5, x=0, y=self.height-5)
        self.page_bar.draw()
        self.popup = PopUpFrame(PageUI.DISPLAY, self.cursor.draw, self.app_frame, width=self.width,
                                  height=self.height-15, x=0, y=self.height-54)

    def _control_clb(self, params):
        """
        {"X": trackball.posx, "Y": trackball.posy,
            "S": trackball.toggle, "action": trackball.action}
        """
        action = params.get('action', None)
        if action is not None:
            x, y = params['X'], self.height-params['Y']     # invert Y axes
            self.cursor.update(x, y)
            lut = {"right": "next", "left": "prev"}         # Convert trackball output to control command
            self.control(lut.get(action, action))
            self.DISPLAY.show()

    def control(self, action, force=False):
        # Wake on action
        self.wake()
        # Initial actions:
        self.header_bar.reset_timer()
        self.cursor.draw()

        # Enable page lift-right scroll when footer is selected
        if Cursor.TAG == 'footer' or force:
            delta_t = ticks_diff(ticks_ms(), self._last_page_switch)
            if delta_t > 200:       # Check page switch frequency - max 200ms
                self._last_page_switch = ticks_ms()
                if action == "next":
                    self.app_frame.next()
                if action == "prev":
                    self.app_frame.previous()
                self.page_bar.draw()
        if action == "off":
            Frame.pause_all()
            self.DISPLAY.poweroff()
        if action == "on":
            Frame.resume_all()
            self.DISPLAY.poweron()
        if action == "press":
            if self.popup.selected:
                self.popup.cancel()

    def wake(self):
        """Wake up UI from hibernation"""
        if Frame.HIBERNATE:
            Frame.resume_all()
            if callable(PageUI.HAPTIC):
                PageUI.HAPTIC()
            self.DISPLAY.poweron()

    @staticmethod
    def add_page(page):
        return AppFrame.add_page(page)

#################################################################################
#                                     Page function                             #
#################################################################################

def _system_page(display, w, h, x, y):
    """
    System basic information page
    """
    display.text(cfgget("devfid"), x, y+5)
    display.text(f"  {ifconfig()[1][0]}", x, y+15)
    display.text(f"  V: {cfgget('version')}", x, y+25)
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
    offset = 4
    display.rect(x+offset, y+offset, w-(offset*2), h-(offset*2))


def _empty_page(display, w, h, x, y):
    pass

#################################################################################
#                                  Public functions                             #
#################################################################################

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
    if PageUI.INSTANCE is None:
        ui = PageUI(width, height, poweroff=poweroff, oled_type=oled_type, control=control, haptic=haptic)
        # Add default pages...
        ui.add_page([_system_page, _intercon_page, _test_page, _empty_page])
        ui.create()         # Header(4), AppPage(1), PagerIndicator
        return "PageUI was created"
    return "PageUI was already created"


def control(cmd="next"):
    if cmd in ("next", "prev", "on", "off"):
        PageUI.INSTANCE.control(cmd, force=True)
        return cmd
    return f"Unknown action: {cmd}"


def popup(msg='micrOS msg'):
    """
    POP-UP message function
    :param msg: message string
    """
    PageUI.INSTANCE.wake()
    return PageUI.INSTANCE.popup.textbox(msg)


def cancel_popup():
    return PageUI.INSTANCE.popup.cancel()


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
                  "BUTTON debug", "popup msg='text'", "cancel_popup"),
        widgets=widgets)
