try:
    import camera
except Exception as e:
    camera = None
import time
from Debug import console_write
from Common import rest_endpoint, syslog

try:
    from LM_dashboard_be import widget_add
except:
    widget_add = None

FLASH_LIGHT = None      # Flashlight object
IN_CAPTURE = False      # Make sure single capture in progress in the same time
CAM_INIT = False

def load_n_init(quality='medium', freq='default', effect="NONE"):
    """
    Load Camera module OV2640
    :param quality: high (HD), medium (SVGA), low (240x240)
    :param freq: default (not set: 10kHz) or high: 20kHz
    :param effect: NONE (default), OR: NEG, BW, RED, GREEN, BLUE, RETRO
    """
    if camera is None:
        syslog("Non supported feature - use esp32cam image!")
        return "Non supported feature - use esp32cam image!"

    global CAM_INIT
    if CAM_INIT:
        return CAM_INIT

    for cnt in range(0, 3):
        console_write(f"Init OV2640 cam {cnt+1}/3")
        try:
            # ESP32-CAM (default configuration) - https://bit.ly/2Ndn8tN
            if freq.strip().lower() == 'high':
                # You can try using a faster xclk (20MHz), this also worked with the esp32-cam and m5camera
                # but the image was pixelated and somehow green.
                cam = camera.init(0, format=camera.JPEG, xclk_freq=camera.XCLK_20MHz, fb_location=camera.PSRAM)
            else:
                cam = camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
            if cam:
                CAM_INIT = cam              # set to True (store cam object)
                break
        except Exception as e:
            syslog(f"[ERR] OV2640: {e}")
        camera.deinit()
        time.sleep(1)
    if not CAM_INIT:
        return "Cannot init OV2640 cam"

    # Apply (default) camera settings
    settings(quality=quality, effect=effect, saturation=50, brightness=50, contrast=50, whitebalace="NONE", q=15)
    # Register rest endpoint
    rest_endpoint('cam/snapshot', _snapshot_clb)
    rest_endpoint('cam/stream', _image_stream_clb)
    if widget_add is not None:
        widget_add({'OV2640': {'settings/saturation=': 'slider',
                               'settings/brightness=': 'slider',
                               'settings/contrast=': 'slider'}})
    return "Endpoint created: /cam/snapshot and /cam/stream"


def settings(quality=None, flip=None, mirror=None, effect=None, saturation=None, brightness=None, contrast=None, whitebalace=None, q=None):
    """
    Camera settings
    :param flip: flip image True/False
    :param mirror: mirror image True/False
    :param effect: None (default), OR: NEG, BW, RED, GREEN, BLUE, RETRO
    :param saturation:  0-100 %
    :param brightness:  0-100 %
    :param contrast:    0-100 %
    :param whitebalace: NONE (default) SUNNY, CLOUDY, OFFICE, HOME
    :param q:           10-63 lower number means higher quality
    """

    def percent_to_value(percent):
        # Ensure the input is within the valid range (0-100)
        percent = max(0, min(100, percent))
        # Convert the percentage to a value between -2 and 2
        value = ((percent / 100) * 4) - 2
        return int(value)

    # framesize settings
    # The options are the following:
    # FRAME_96X96 FRAME_QQVGA FRAME_QCIF FRAME_HQVGA FRAME_240X240
    # FRAME_QVGA FRAME_CIF FRAME_HVGA FRAME_VGA FRAME_SVGA
    # FRAME_XGA FRAME_HD FRAME_SXGA FRAME_UXGA FRAME_FHD
    # FRAME_P_HD FRAME_P_3MP FRAME_QXGA FRAME_QHD FRAME_WQXGA
    # FRAME_P_FHD FRAME_QSXGA
    if quality == 'medium':
        camera.framesize(camera.FRAME_SVGA)     # SVGA: 800x600
    elif quality == 'high':
        camera.framesize(camera.FRAME_HD)       # HD: 1280×720
    elif quality is not None:
        camera.framesize(camera.FRAME_HVGA)     # low (default) HVGA: 480x320
    # Check this link for more information: https://bit.ly/2YOzizz

    ## Other settings:
    # flip up side down
    if isinstance(flip, bool):
        camera.flip(1 if flip else 0)
    # left / right
    if isinstance(mirror, bool):
        camera.mirror(1 if mirror else 0)

    # SPECIAL EFFECTS: EFFECT_NONE (default) EFFECT_NEG EFFECT_BW EFFECT_RED EFFECT_GREEN EFFECT_BLUE EFFECT_RETRO
    effects = {'NEG': camera.EFFECT_NEG, 'BW': camera.EFFECT_BW, 'RED': camera.EFFECT_RED,
               'GREEN': camera.EFFECT_GREEN, 'BLUE': camera.EFFECT_BLUE,
               'RETRO': camera.EFFECT_RETRO}
    if effect is not None:
        camera.speffect(camera.EFFECT_NONE if effects.get(effect, None) is None else effects.get(effect))

    # white balance: WB_NONE (default) WB_SUNNY WB_CLOUDY WB_OFFICE WB_HOME
    wb = {"SUNNY": camera.WB_SUNNY, "CLOUDY": camera.WB_CLOUDY,
          "OFFICE": camera.WB_OFFICE, "HOME": camera.WB_HOME}
    if whitebalace is not None:
        camera.whitebalance(camera.WB_NONE if wb.get(whitebalace, None) is None else wb.get(whitebalace))

    # saturation: -2,2 (default 0). -2 grayscale
    if saturation is not None and isinstance(saturation, int):
        camera.saturation(percent_to_value(saturation))

    # brightness: -2,2 (default 0). 2 brightness
    if brightness is not None and isinstance(brightness, int):
        camera.brightness(percent_to_value(brightness))

    # contrast: -2,2 (default 0). 2 highcontrast
    if contrast is not None and isinstance(contrast, int):
        camera.contrast(percent_to_value(contrast))

    # quality: 10-63 lower number means higher quality
    if q is not None and isinstance(q, int) and 10 <= q <=63:
        camera.quality(q)

    return 'Settings applied.'


def capture():
    if camera is None:
        return "Non supported feature - use esp32cam image!"
    load_n_init()
    global IN_CAPTURE
    # Capture image
    buf = False
    if IN_CAPTURE:
        return buf
    IN_CAPTURE = True
    try:
        n_try = 0
        while n_try < 10:
            # wait for sensor to start and focus before capturing image
            buf = camera.capture()
            if buf:
                break
            n_try += 1
            time.sleep(0.1)
    except Exception as e:
        syslog(f"[OV2640] Failed to capture: {e}")
    IN_CAPTURE = False
    return buf


def photo(name='photo.jpg'):
    buf = capture()
    with open(name, 'w') as f:
        if buf:
            f.write(buf)
            return "Image saved as photo.jpg"
    return "Cannot save... photo.jpg"


def _snapshot_clb():
    image = capture()
    if image is not None:
        return 'image/jpeg', image
    return 'text/plain', f'capture error: {image}'


def _image_stream_clb():
    return 'multipart/x-mixed-replace', {'callback': capture, 'content-type': 'image/jpeg'}


def _img_clb(name="photo.jpg"):
    with open(name, 'rb') as f:
        image = f.read()
    return 'image/jpeg', image


def set_photo_endpoint():
    """
    Set photo endpoint (rest endpoint)
    """
    rest_endpoint('photo', _img_clb)
    return "Endpoint created: /photo"


def __dimmer_init():
    global FLASH_LIGHT
    if FLASH_LIGHT is None:
        from machine import Pin, PWM
        dimmer_pin = Pin(4)
        FLASH_LIGHT = PWM(dimmer_pin, freq=20480)
    return FLASH_LIGHT

def flashlight(value=None, default=100):
    """
    Camera flashlight
    :param value: None OR 0-1000
    :param default: default value when value is None (ON/OFF function)
    """
    fl = __dimmer_init()
    if value is None:
        val = fl.duty()
        value = 0 if val > 0 else default
    fl.duty(value)
    return {'value': value}

def lmdep():
    """
    Show Load Module dependency
    - List of load modules used by this application
    :return: tuple
    """
    return 'dashboard_be'

def help():
    return 'load_n_init quality="medium/low/high" freq="default/high"',\
        'settings quality=None flip=None/True mirror=None/True effect="NONE" saturation brightness contrast',\
        'capture', 'photo', 'set_photo_endpoint', 'flashlight value=None<0-1000> default=100',\
        'Thanks to :) https://github.com/lemariva/micropython-camera-driver',\
        '[HINT] after load_n_init you can access the /cam/snapshot and /cam/stream endpoints'
