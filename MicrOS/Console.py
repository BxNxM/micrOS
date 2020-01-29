try:
    import ProgressLED as pLED
except Exception as e:
    pLED = False

try:
    PLED_STAT = ConfigHandler.cfg.get("progressled")
except Exception as e:
    PLED_STAT = True

DEBUG_PRINT= False


def progress_led_toggle_adaptor(func):
    def wrapper(*args, **kwargs):
        if pLED and PLED_STAT: pLED.pled.toggle()
        output = func(*args, **kwargs)
        if pLED and PLED_STAT: pLED.pled.toggle()
        return output
    return wrapper

@progress_led_toggle_adaptor
def write(msg):
    if DEBUG_PRINT:
        print(msg)

if __name__ == "__main__":
    write("Hello World!")
