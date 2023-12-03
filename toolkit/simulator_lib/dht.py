from sim_console import console


class DHT22:

    def __init__(self, pin=None):
        console(f"Init DHT22, pin: {pin}")
        self.pin = pin

    def temperature(self):
        return 50.0

    def humidity(self):
        return 40.0

    def measure(self):
        pass
