"""
micrOS Console and Log write interface implementations.
- with progress led feature, simple and custom
    Designed by Marcell Ban aka BxNxM
"""

from machine import Pin
try:
    from Logger import syslog as logger_syslog
except:
    logger_syslog = None
try:
    from microIO import resolve_pin, pinmap_search, register_pin
except:
    pinmap_search = None


#############################################
#       DEBUG PRINT + PROGRESS LED          #
#############################################


class DebugCfg:
    DEBUG = True        # DEBUG PRINT ON/OFF - SET FROM ConfigHandler
    PLED_STEP = None    # PROGRESS LED OBJECT - init in init_pled

    @staticmethod
    def init_pled():
        # CALL FROM ConfigHandler
        if pinmap_search is None:
            # Check LogicalPins module loadable (robustness...)
            return
        pled = pinmap_search('builtin')['builtin']
        if pled is None:
            # No available builtin pin, skip pled init...
            return
        # CONFIGURE PROGRESS LED
        if isinstance(pled, int):
            # [MODE] Simple flashing progress LED
            try:
                # Progress led for esp32/etc
                led_obj = Pin(abs(resolve_pin('builtin')), Pin.OUT)
                if resolve_pin('builtin') < 0:
                    # Pin number start with (-), like -8 (means inverted output)
                    led_obj.value(1)            # Turn OFF built-in LED state invert (1:OFF)
                # Set function callback for step function (simple led - blink)
                DebugCfg.PLED_STEP = lambda: led_obj.value(not led_obj.value())  # # double-blink: return None
            except Exception as e:
                syslog(f"[PLED] led error: {e}")
        elif callable(pled):
            # [MODE] OVERRIDE PROGRESS LED WITH CUSTOM step FUNCTION
            DebugCfg.PLED_STEP = pled
            DebugCfg._auto_register_pin()
        else:
            syslog(f"[WARN] pled type not supported: {pled}")


    @staticmethod
    def _auto_register_pin():
        try:
            pin = DebugCfg.PLED_STEP(pin=True)
            if isinstance(pin, int):
                register_pin('builtin', pin)
        except Exception as e:
            syslog(f"[ERR] pled pin registration: {e}", console=False)


    @staticmethod
    def step():
        """
        DEBUG LED FLASHING FEEDBACK
        - handle step callback function execution
        """
        try:
            if callable(DebugCfg.PLED_STEP):
                return DebugCfg.PLED_STEP()         # Run step function (return None: double-blink OR True: no d-b)
        except Exception as e:
            syslog(f"[PLED] step error: {e}")
        return True


def console_write(msg):
    if DebugCfg.DEBUG:
        try:
            analog = DebugCfg.step()
            print(msg)
            if analog is None:
                DebugCfg.step()             # Double-blink
        except Exception as e:
            syslog(f"[ERR] console_write: {e}", console=False)


def syslog(data, console=True):
    """
    :param data: msg string / data
    :param console: activate console_write (default: True)
    :return: is ok
    """
    if console:
        console_write(data)
    return False if logger_syslog is None else logger_syslog(data)
