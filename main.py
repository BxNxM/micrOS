import time
try:
    import wifi
except Exception as e:
    print("MAIN IMPORT ERROR: " + str(e))
    wifi = None
try:
    import live_server
except Exception as e:
    print("MAIN IMPORT ERROR: " + str(e))
    live_server = None
try:
    import oled
except Exception as e:
    print("MAIN IMPORT ERROR: " + str(e))
    oled = None
try:
    import ConfigHandler
except Exception as e:
    print("MAIN IMPORT ERROR: " + str(e))
    ConfigHandler = None



def server_template():
    time.sleep(3)
    if wifi is not None:
        wifi_set_output = wifi.auto_network_configuration(essid="elektroncsakpozitivan", pwd="BNM3,1415")
        print(wifi_set_output)
    if live_server is not None:
        live_server.server.run()

def network_page(display):
    if wifi is not None:
        network_info_dict = wifi.wifi_info()
    else:
        network_info_dict = {}
    display.text("Network", 50, 0)
    display.text("AP | STA", 50, 10)
    text = "STATE:" + str(network_info_dict['ap_state']) + str(network_info_dict['sta_state'])
    display.text(text, 0, 20)
    text = "CONN.:" + str(network_info_dict['ap_isconnected']) + str(network_info_dict['sta_isconnected'])
    display.text(text, 0, 30)
    text = "APip: " + str(network_info_dict['ap_iplist'][0])
    display.text(text, 0, 40)
    text = "STAip:" + str(network_info_dict['sta_iplist'][0])
    display.text(text, 0, 50)


if __name__ == "__main__":
    try:
        server_template()
    except Exception as e:
        print("MAIN WAS BROKEN " + str(e))
    try:
        oled_frame = oled.GUI()
        rssi = wifi.wifi_rssi(str(ConfigHandler.cfg.get('sta_essid')))[3][1]
        oled_frame.draw_page_function(network_page)
    except Exception as e:
        print("MAIN WAS BROKEN " + str(e))
