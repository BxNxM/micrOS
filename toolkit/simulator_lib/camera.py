import os
import time
MYPATH = os.path.dirname(__file__)

JPEG = None
XCLK_20MHz = None
PSRAM = None
FRAME_SVGA = None
FRAME_HD = None
FRAME_HVGA = None

EFFECT_NEG = None
EFFECT_BW = None
EFFECT_RED = None
EFFECT_GREEN = None
EFFECT_BLUE = None
EFFECT_RETRO = None
EFFECT_NONE = None

WB_SUNNY = None
WB_CLOUDY = None
WB_OFFICE = None
WB_HOME = None
WB_NONE = None


def _dummy_images_gen():
    images = [os.path.join(MYPATH, 'view01.jpg'), os.path.join(MYPATH, 'view02.jpg')]
    while True:
        for img in images:
            yield img

_DUMMY_IMAGES = _dummy_images_gen()

def init(*args, **kwargs):
    print("Init dummy camera module")
    print(args)
    print(kwargs)
    return True

def deinit(*args, **kwargs):
    print("DeInit dummy camera module")
    print(args)
    print(kwargs)
    return True

def framesize(*args, **kwargs):
    pass

def flip(*args, **kwargs):
    pass

def mirror(*args, **kwargs):
    pass

def speffect(*args, **kwargs):
    pass

def whitebalance(*args, **kwargs):
    pass

def saturation(*args, **kwargs):
    pass

def brightness(*args, **kwargs):
    pass

def contrast(*args, **kwargs):
    pass

def quality(*args, **kwargs):
    pass

def capture():
    print("Load dummy image")
    image = next(_DUMMY_IMAGES)
    try:
        time.sleep(1)
        with open(image, 'rb') as f:
            image_bin = f.read()
            return image_bin
    except Exception as e:
        print(f"Cannot load {image}: {e}")
        return b''
