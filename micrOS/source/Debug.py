from machine import Pin
try:
    from Logger import syslog
except:
    syslog = None
try:
    from microIO import resolve_pin, pinmap_search, detect_platform
except:
    detect_platform = None


#############################################
#       DEBUG PRINT + PROGRESS LED          #
#############################################


class DebugCfg:
    DEBUG = True        # DEBUG PRINT ON/OFF - SET FROM ConfigHandler
    PLED_STEP = None    # PROGRESS LED OBJECT - init in init_pled
    NEO_WHEEL = None    # NEOPIXEL (ws2812/esp32s3) color wheel object
    COLOR_INDEX = 0     # APA102 TinyPico color wheel counter

    @staticmethod
    def init_pled():
        # CALL FROM ConfigHandler
        if detect_platform is None:
            # Check LogicalPins module loadable (robustness...)
            return
        micro_platform = detect_platform()
        if micro_platform == "tinypico":
            # Progress led for TinyPico
            DebugCfg._init_apa102()
            return
        pled = pinmap_search('builtin')['builtin']
        if pled is not None:
            if isinstance(pled, int):
                # SET PROGRESS LED WITH BUILT-IN step FUNCTION
                if micro_platform == "esp32s3":
                    # Progress led for esp32s3
                    DebugCfg._init_ws2812()
                else:
                    # Progress led for esp32/etc
                    DebugCfg._init_simple()
            else:
                # OVERRIDE PROGRESS LED WITH CUSTOM step FUNCTION
                DebugCfg.PLED_STEP = pled

    @staticmethod
    def step():
        """
        DEBUG LED FEEDBACK
        - handle 3 types of builtin LEDs: analog, neopixel(ws2812), apa102
        - automatic selection based on board type + builtin logical pin number
        """
        try:
            if callable(DebugCfg.PLED_STEP):
                return DebugCfg.PLED_STEP()         # Run step function (return None: double-blink OR True: no d-b)
        except Exception as e:
            errlog_add(f"[PLED] step error: {e}")
        return True

    @staticmethod
    def _init_simple():
        try:
            # Progress led for esp32/etc
            led_obj = Pin(abs(resolve_pin('builtin')), Pin.OUT)
            if resolve_pin('builtin') < 0:     # Pin number start with (-), like -8 (means inverted output)
                led_obj.value(1)                # Turn OFF built-in LED state invert (1:OFF)
            # Set function callback for step function (simple led - blink)
            DebugCfg.PLED_STEP = lambda: led_obj.value(not led_obj.value())     # # double-blink: return None
        except Exception as e:
            errlog_add(f"[PLED] led error: {e}")

    @staticmethod
    def _init_apa102():
        try:
            from machine import SoftSPI
            from dotstar import DotStar
            from tinypico import DOTSTAR_CLK, DOTSTAR_DATA, SPI_MISO, set_dotstar_power, dotstar_color_wheel
            spi = SoftSPI(sck=Pin(DOTSTAR_CLK), mosi=Pin(DOTSTAR_DATA), miso=Pin(SPI_MISO))
            # Create a DotStar instance
            dotstar = DotStar(spi, 1, brightness=0.4)  # Just one DotStar, half brightness
            # Turn on the power to the DotStar
            set_dotstar_power(True)
            DebugCfg.PLED_STEP = lambda: DebugCfg._step_apa102(led_obj=dotstar, color_wheel=dotstar_color_wheel)
        except Exception as e:
            errlog_add(f"[PLED] apa102 error: {e}")

    @staticmethod
    def _step_apa102(led_obj, color_wheel):
        # Get the R,G,B values of the next colour
        r, g, b = color_wheel(DebugCfg.COLOR_INDEX*2)
        # Set the colour on the DOTSTAR
        led_obj[0] = (int(r * 0.6), g, b, 0.4)
        # Increase the wheel index
        DebugCfg.COLOR_INDEX = 0 if DebugCfg.COLOR_INDEX > 1000 else DebugCfg.COLOR_INDEX + 2
        return True                  # No double-blink

    @staticmethod
    def _init_ws2812():
        try:
            from neopixel import NeoPixel
            neo_pin = Pin(resolve_pin('builtin'))
            led_obj = NeoPixel(neo_pin, 1)
            DebugCfg.PLED_STEP = lambda: DebugCfg._step_ws2812(led_obj)
        except Exception as e:
            errlog_add(f"[PLED] ws2812 error: {e}")

    @staticmethod
    def _step_ws2812(led_obj):
        def _color_wheel():
            while True:
                yield 10, 0, 0
                yield 5, 5, 0
                yield 0, 10, 0
                yield 0, 5, 5
                yield 0, 0, 10
                yield 5, 0, 5
        if DebugCfg.NEO_WHEEL is None:
            DebugCfg.NEO_WHEEL = _color_wheel()
        led_obj[0] = next(DebugCfg.NEO_WHEEL)
        led_obj.write()
        return True                     # No double-blink


def console_write(msg):
    if DebugCfg.DEBUG:
        try:
            analog = DebugCfg.step()
            print(msg)
            if analog is None:
                DebugCfg.step()             # Double-blink
        except Exception as e:
            errlog_add(f"[ERR] console_write: {e}", console=False)


def errlog_add(data, console=True):
    """
    :param data: msg string / data
    :param console: activate console_write (default: True)
    :return: is ok
    """
    if console:
        console_write(data)
    return False if syslog is None else syslog(data)
