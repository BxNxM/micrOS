
MONO_VLSB = None
MONO_HMSB = None


class FrameBuffer:

    def __init__(self, *args, **kwargs):
        pass

    def fill(self, color=0):
        pass

    def show(self):
        pass

    def write_cmd(self, cmd):
        pass

    def reset(self):
        pass

    def poweron(self):
        pass

    def poweroff(self):
        pass

    def flip(self, *args, **kwargs):
        pass

    def rotate(self, *args, **kwargs):
        pass

    def text(self, string, x, y, color=0):
        pass

    def pixel(self, x, y, color=0):
        pass

    def line(self, x0, y0, x1, y1, color=0):
        pass

    def rect(self, x0, y0, x1, y1, color=0):
        pass

    def fill_rect(self, x, y, w, h, color=0):
        pass

    def blit(self, fbuf, x, y, key, palette):
        pass

    def scroll(self, dx, dy):
        pass
