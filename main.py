import time
try:
    import wifi
except Exception as e:
    print("MAIN IMPORT ERROR: " + str(e))
    wifi = None
import live_server

def server_template():
    time.sleep(3)
    if wifi is not None:
        wifi_set_output = wifi.auto_network_configuration(essid="elektroncsakpozitivan", pwd="BNM3,1415")
        print(wifi_set_output)
    live_server.server.run()

if __name__ == "__main__":
    try:
        server_template()
    except Exception as e:
        print("MAIN WAS BROKEN " + str(e))
