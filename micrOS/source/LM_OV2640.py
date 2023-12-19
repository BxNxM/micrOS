try:
    import camera
except Exception as e:
    camera = None
import time
from Debug import errlog_add, console_write
from Common import rest_endpoint

FLASH_LIGHT = None      # Flashlight object
IN_CAPTURE = False      # Make sure single capture in progress in the same time
CAM_INIT = False

def load_n_init(quality='medium'):
    """
    Load Camera module OV2640
    :param quality: high (HD), medium (SVGA), low (240x240)
    """

    if camera is None:
        errlog_add("Non supported feature - use esp32cam image!")
        return "Non supported feature - use esp32cam image!"

    global CAM_INIT
    if CAM_INIT:
        return CAM_INIT

    for cnt in range(0, 3):
        console_write(f"Init OV2640 cam {cnt+1}/3")
        try:
            # ESP32-CAM (default configuration) - https://bit.ly/2Ndn8tN
            cam = camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
            if cam:
                CAM_INIT = cam          # set to True
                break
        except Exception as e:
            errlog_add(f"[ERR] OV2640: {e}")
        camera.deinit()
        time.sleep(1)
    if not CAM_INIT:
        return "Cannot init OV2640 cam"

    # The parameters: format=camera.JPEG, xclk_freq=camera.XCLK_10MHz are standard for all cameras.
    # You can try using a faster xclk (20MHz), this also worked with the esp32-cam and m5camera
    # but the image was pixelated and somehow green.

    settings(quality=quality)

    # Register rest endpoint
    rest_endpoint('cam', _image_stream_clb)
    return f"Endpoint created: /cam and /cam/stream"


def settings(quality=None, flip=None, mirror=None):
    """
    Camera settings
    :param flip: flip image True/False
    :param mirror: mirror image True/False
    """
    # framesize
    if quality == 'medium':
        camera.framesize(camera.FRAME_SVGA)     # SVGA: 800x600
    elif quality == 'high':
        camera.framesize(camera.FRAME_HD)       # HD: 1280×720
    elif quality is not None:
        camera.framesize(camera.FRAME_HVGA)     # low (default) HVGA: 480x320
    # The options are the following:
    # FRAME_96X96 FRAME_QQVGA FRAME_QCIF FRAME_HQVGA FRAME_240X240
    # FRAME_QVGA FRAME_CIF FRAME_HVGA FRAME_VGA FRAME_SVGA
    # FRAME_XGA FRAME_HD FRAME_SXGA FRAME_UXGA FRAME_FHD
    # FRAME_P_HD FRAME_P_3MP FRAME_QXGA FRAME_QHD FRAME_WQXGA
    # FRAME_P_FHD FRAME_QSXGA
    # Check this link for more information: https://bit.ly/2YOzizz

    ## Other settings:
    # flip up side down
    if isinstance(flip, bool):
        camera.flip(1 if flip else 0)
    # left / right
    if isinstance(mirror, bool):
        camera.mirror(1 if mirror else 0)

    # special effects: EFFECT_NONE (default) EFFECT_NEG EFFECT_BW EFFECT_RED EFFECT_GREEN EFFECT_BLUE EFFECT_RETRO
    camera.speffect(camera.EFFECT_NONE)

    # white balance: WB_NONE (default) WB_SUNNY WB_CLOUDY WB_OFFICE WB_HOME
    camera.whitebalance(camera.WB_NONE)

    # saturation: -2,2 (default 0). -2 grayscale
    camera.saturation(0)

    # brightness: -2,2 (default 0). 2 brightness
    camera.brightness(0)

    # contrast: -2,2 (default 0). 2 highcontrast
    camera.contrast(0)

    # quality: 10-63 lower number means higher quality
    camera.quality(15)

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
        errlog_add(f"[OV2640] Failed to capture: {e}")
    IN_CAPTURE = False
    return buf


def photo():
    buf = capture()
    with open('photo.jpg', 'w') as f:
        if buf:
            f.write(buf)
            return "Image saved as photo.jpg"
    return "Cannot save... photo.jpg"


def _image_stream_clb():
    image = capture()
    if image:
        return 'image/jpeg', image
    return 'text/plain', f'capture error: {image}'


def _img_clb():
    with open("photo.jpg", 'rb') as f:
        image = f.read()
    return 'image/jpeg', image


def set_photo_endpoint():
    """
    Set photo endpoint (rest endpoint)
    """
    rest_endpoint('photo', _img_clb)
    return "Endpoint created: /photo"


def set_test_endpoint(endpoint='test'):
    """
    Set test endpoint (rest endpoint)
    :param endpoint: /<endpoint> to have as custom endpoint
    """
    rest_endpoint(endpoint, _test_reply_clb)
    return f"Endpoint created: /{endpoint}"


def _test_reply_clb():
    text = "hello world!"
    return 'text/plain', text

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

def help():
    return 'load_n_init quality="medium/low/high"', 'settings quality=None flip=None/True mirror=None/True',\
        'capture', 'photo', 'set_test_endpoint endpoint="test"', 'set_photo_endpoint', 'flashlight value=None<0-1000>, default=100',\
        'Thanks to :) https://github.com/lemariva/micropython-camera-driver',\
        '[HINT] after load_n_init you can access the /cam and /cam/stream endpoints'
