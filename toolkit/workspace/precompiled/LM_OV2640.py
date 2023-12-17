try:
    import camera
except Exception as e:
    camera = None
import time
from Debug import errlog_add
from Common import rest_endpoint


def load_n_init():

    if camera is None:
        errlog_add("Non supported feature - use esp32cam image!")
        return "Non supported feature - use esp32cam image!"

    try:
        # ESP32-CAM (default configuration) - https://bit.ly/2Ndn8tN
        cam = camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
    except Exception:
        camera.deinit()
        time.sleep(1)
        cam = camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
    errlog_add(f"INIT CAM: {cam}")

    # The parameters: format=camera.JPEG, xclk_freq=camera.XCLK_10MHz are standard for all cameras.
    # You can try using a faster xclk (20MHz), this also worked with the esp32-cam and m5camera
    # but the image was pixelated and somehow green.

    ## Other settings:
    # flip up side down
    camera.flip(1)
    # left / right
    camera.mirror(1)

    # framesize
    #camera.framesize(camera.FRAME_240x240)
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
    camera.quality(30)

    # Register rest endpoint
    rest_endpoint('img', _image_stream_clb)

    return cam


def capture():
    if camera is None:
        return "Non supported feature - use esp32cam image!"
    return camera.capture()


def photo():
    with open('photo.jpg', 'w') as f:
        f.write(capture())
    return "Image saved as photo.jpg"


def _image_stream_clb():
    try:
        # option A
        # image = cam.capture()
        # option B
        photo()
        with open("photo.jpg", 'rb') as f:
            image = f.read()
    except Exception as e:
        return f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nContent-Length:{len(e)}\r\n\r\n{e}"
    # headers = { 'Last-Modified' : 'Fri, 1 Jan 2018 23:42:00 GMT',\
    #            'Cache-Control' : 'no-cache, no-store, must-revalidate' }
    return f"HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nContent-Length:{len(image)}\r\n\r\n{image}"


def set_test_endpoint():
    rest_endpoint('test', _tet_reply)
    return True

def _tet_reply():
    text = "hello"
    return f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length:{len(text)}\r\n\r\n{text}"


def help():
    return 'set_test_endpoint', 'load_n_init', 'capture', 'photo', 'Thanks to :) https://github.com/lemariva/micropython-camera-driver'
