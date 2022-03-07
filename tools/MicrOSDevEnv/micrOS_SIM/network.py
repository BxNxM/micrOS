from sim_console import console
import socket

AP_IF = "DUMMY_AP_IF"
STA_IF = "DUMMY_STA_IF"


class WLAN:
    __instance = None

    def __new__(cls, mode, *args, **kwargs):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        cls     - class
        """
        if cls.__instance is None:
            console("[WLAN] singleton constructor mode: {} ".format(mode))
            # SocketServer singleton properties
            cls.__instance = super().__new__(cls)
            cls.__instance.name = 'WLAN'
            cls.__instance.__init(mode, *args, **kwargs)
        return cls.__instance

    def __init(self, mode, *args, **kwargs):
        console("|- [WLAN] constructor mode: {} ".format(mode))
        self.__mode = mode
        self.__isconnected = False
        self.__active = True
        self.__server_ip = None
        self.__config_dict = {'essid': None, 'password': None, 'authmode': None, 'mac': (1,2,3,4,5)}
        self.__if_config_list = [self.__get_machine_ip(), "0.0.0.0", "0.0.0.0", "0.0.0.0"]

    def isconnected(self):
        return self.__isconnected

    def active(self, state=None):
        if state is None:
            return self.__active
        self.__active = state
        return self.active()

    def config(self, *args, **kwargs):
        for key, value in kwargs.items():
            self.__config_dict[key] = value
        for key in args:
            return self.__config_dict.get(key, None)

    def ifconfig(self, addr_tuple=None):
        console("Local server IP: {}".format(self.__get_machine_ip()))
        if addr_tuple is None:
            return self.__if_config_list
        self.__if_config_list = [addr_tuple, "0.0.0.0", "0.0.0.0", "0.0.0.0"]
        return self.__if_config_list

    def __get_machine_ip(self):
        if self.__server_ip is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.__server_ip = s.getsockname()[0]
            s.close()
        return self.__server_ip

    def scan(self):
        essid = 'your_wifi_name'.encode('utf8')
        return [(essid, '1', '2', '3')]

    def connect(self, *args, **kwargs):
        self.__isconnected = True
        return True

    def status(self, key=None):
        if key == 'rssi':
            return -50
        return True

    def disconnect(self):
        return True


if __name__ == "__main__":
    w = WLAN('asd')
    print(w.ifconfig())
