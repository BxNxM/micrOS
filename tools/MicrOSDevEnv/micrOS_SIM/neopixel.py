

class NeoPixel:
    __instance = None
    __pix_list = []

    def __new__(cls, pin, n):
        if NeoPixel.__instance is None:
            NeoPixel.__instance = super().__new__(cls)
            NeoPixel.__instance.n = n
            NeoPixel.__instance.pin = pin
            for _ in range(0, n):
                NeoPixel.__pix_list.append((0, 0, 0))
        return NeoPixel.__instance

    def __getitem__(cls, key):
        return cls.__pix_list[key]

    def __setitem__(cls, key, value):
        cls.__pix_list[key] = value

    def write(cls):
        pass


