try:
    import camera
except Exception as e:
    camera = None
import time
from Debug import errlog_add, console_write
from Common import rest_endpoint


def load_n_init():

    if camera is None:
        errlog_add("Non supported feature - use esp32cam image!")
        return "Non supported feature - use esp32cam image!"

    cam = False
    for cnt in range(0, 3):
        console_write(f"Init OV2640 cam {cnt+1}/3")
        try:
            # ESP32-CAM (default configuration) - https://bit.ly/2Ndn8tN
            cam = camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
            if cam:
                break
        except Exception as e:
            errlog_add(f"[ERR] OV2640: {e}")
        camera.deinit()
        time.sleep(1)
    if not cam:
        return "Cannot init OV2640 cam"

    # The parameters: format=camera.JPEG, xclk_freq=camera.XCLK_10MHz are standard for all cameras.
    # You can try using a faster xclk (20MHz), this also worked with the esp32-cam and m5camera
    # but the image was pixelated and somehow green.

    ## Other settings:
    # flip up side down
    #camera.flip(1)
    # left / right
    #camera.mirror(1)

    # framesize
    camera.framesize(camera.FRAME_240X240)
    # The options are the following:
    # FRAME_96X96 FRAME_QQVGA FRAME_QCIF FRAME_HQVGA FRAME_240X240
    # FRAME_QVGA FRAME_CIF FRAME_HVGA FRAME_VGA FRAME_SVGA
    # FRAME_XGA FRAME_HD FRAME_SXGA FRAME_UXGA FRAME_FHD
    # FRAME_P_HD FRAME_P_3MP FRAME_QXGA FRAME_QHD FRAME_WQXGA
    # FRAME_P_FHD FRAME_QSXGA
    # Check this link for more information: https://bit.ly/2YOzizz

    # special effects: EFFECT_NONE (default) EFFECT_NEG EFFECT_BW EFFECT_RED EFFECT_GREEN EFFECT_BLUE EFFECT_RETRO
    camera.speffect(camera.EFFECT_NONE)
    # The options are the following:

    # white balance: WB_NONE (default) WB_SUNNY WB_CLOUDY WB_OFFICE WB_HOME
    camera.whitebalance(camera.WB_NONE)

    # saturation: -2,2 (default 0). -2 grayscale
    camera.saturation(0)

    # brightness: -2,2 (default 0). 2 brightness
    camera.brightness(0)

    # contrast: -2,2 (default 0). 2 highcontrast
    camera.contrast(0)

    # quality: 10-63 lower number means higher quality
    camera.quality(10)

    # Register rest endpoint
    rest_endpoint('cam', _image_stream_clb)
    return f"Endpoint created: /cam"


def capture():
    if camera is None:
        return "Non supported feature - use esp32cam image!"
    n_try = 0
    buf = False
    while n_try < 10:
        # wait for sensor to start and focus before capturing image
        buf = camera.capture()
        if buf:
            break
        n_try += 1
        time.sleep(0.1)
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
    rest_endpoint('photo', _img_clb)
    return "Endpoint created: /photo"


def set_test_endpoint(endpoint='test'):
    rest_endpoint(endpoint, _test_reply_clb)
    return f"Endpoint created: /{endpoint}"


def _test_reply_clb():
    text = "hello world!"
    return 'text/plain', text


def help():
    return 'set_test_endpoint endpoint="test"', 'set_photo_endpoint', 'load_n_init', 'capture', 'photo',\
        'Thanks to :) https://github.com/lemariva/micropython-camera-driver'
