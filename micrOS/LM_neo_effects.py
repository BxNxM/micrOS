from LM_neopixel import __init_NEOPIXEL, segment
from time import sleep_ms


def meteor(r, g, b, pix=0):
    pixel_cnt = __init_NEOPIXEL().n
    fade_step = float(1.0/pixel_cnt)
    for k in range(0, pixel_cnt):
        fade_offset = pix+k+1 if pix+k+1 <= pixel_cnt else (pix+k+1)-pixel_cnt
        m = fade_offset*fade_step
        segment(int(r*m), int(g*m), int(b*m), s=k)
        sleep_ms(15)
    segment(r, g, b, s=pixel_cnt)
    return 'Meteor R{}:G{}:B{} N:{}'.format(r, g, b, pixel_cnt)


def lmdep():
    return 'LM_neopixel'


def help():
    return 'meteor r=<0-255> g=<0-255> b=<0-255>'
