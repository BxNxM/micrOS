# MicrOs

To remove ^M after get source files from nodemcu in vim:
:%s/ <press^V^M> //g

## Socket terminal example

```
Trying 10.0.1.77...
Connected to 10.0.1.77.
Escape character is '^]'.
local variable referenced before assignment
>>>  help
Configure mode:
   configure|conf     - Enter conf mode
         Key          - Get value
         Key:Value    - Set value
         dump         - Dump all data
   noconfigure|noconf - Exit conf mod
Command mode:
   LM_commands
              listdir
              mem_free
              wifi_rssi
              reboot
              wifi_scan
              add2numbs

>>>  LM_commands mem_free()
CPU[Hz]: 80000000
GC MemFree[byte]: 12272

>>>  LM_commands wifi_rssi()
('elektroncsakpozitivan', -37, 11, ('VeryGood', 3))

>>>  LM_commands wifi_scan()
['DavesMesh', 'Reka', 'UPC1685588', 'UPCCCF2C9E', 'UPC Wi-Free', 'UPC Wi-Free', 'UPC8249168', 'UPC Wi-Free', 'UPC7261536', 'UPC Wi-Free', 'Telekom-xzbTXP', 'Telekom Fon WiFi HU', 'Neirabi', 'Telekom-582251', 'T-CCAF63', '70mai_d01_C569', 'JeanettesCrib', 'UPC Wi-Free', 'UPC Wi-Free', 'UPC9998718', 'UPC Wi-Free', 'TOKYO', 'UPC Wi-Free', 'UPC Wi-Free', 'UPC Wi-Free', 'UPC8F62714', 'UPC92B4E15', 'UPC Wi-Free', 'PZs', 'UPC Wi-Free', 'UPC Wi-Free', 'Telekom Fon WiFi HU', 'UPC1432833', 'UPC1201446', 'ecsp-guest', 'elektroncsakpozitivan', 'Salina', 'BusyBee', 'UPC9183317', 'UPC Wi-Free', 'Mamipapi', 'DIRECT-fm-BRAVIA', 'UPC Wi-Free']

>>>  LM_commands mem_free()
CPU[Hz]: 80000000
GC MemFree[byte]: 13488

>>>  LM_commands add2numbs(1, 10)
1 + 10 = 11

>>>  configure
[configure] >>>  dump
{'nw_mode': 'STA', 'ap_passwd': 'admin', 'debug_print': True, 'shell_timeout': 30, 'sta_essid': 'elektroncsakpozitivan', 'node_name': 'slim01', 'progressled': True, 'sta_pwd': '*****'}
[configure] >>>  noconfigure
```
