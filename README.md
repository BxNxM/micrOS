# MicrOS - IOT platfrom

## System Architecture

![MICROSARCHITECTURE](https://github.com/BxNxM/MicrOs/blob/master/media/MicrOSArchitecture.png?raw=true)

## Device Pinout

![esp8266pinout](https://github.com/BxNxM/MicrOs/blob/master/media/ESP8266-NodeMCU-kit-12-E-pinout-gpio-pin.png?raw=true)

Esp8266 Micropython based - APPlication Core - with -
User function injection over LM_<userapp>.py 

## MicrOS Features

- Config handling - node_config.json
- Socket interpreter - communication interface with the device
	- Config SET/GET/DUMP
	- Load Module function execution
- Network handling
	- STA / AP based on config
- Interrupt callback
	- Time based
	- Event based
- Socket client - interactive - non interactive mode

> Note:
To remove ^M after get source files from nodemcu in vim:
:%s/ <press^V^M> //g

## Quick guide
 
#### Dependences

- **Deploy** dependences
	- esptool.py
	- ampy 

- **Connection** dependences
	- screen (serial port connection)
	- telnet / or use dedicated **socketClient**
		- tools/socketClient.py
			- embedded device scan (arp -a dependency)
			- cache device connection data
			- non-interactive and interactive modes
	
#### Source devenv (bash)

```
source setup
```

#### Erase device & Deploy micropython & Put MicrOS resources 

```
make_all_done
```

## Socket terminal example - non interactive

### Identify device

```
socketclient --dev slim01 hello
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: slim01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Device was found: slim01
hello:slim01:0x500x20x910x680xc0xf7
```

### Get help

```
socketclient --dev slim01 help
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: slim01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Device was found: slim01
hello - default hello msg - identify device (SocketServer)
exit  - exit from shell socket prompt (SocketServer)
[CONF] Configure mode:
   configure|conf     - Enter conf mode
         Key          - Get value
         Key:Value    - Set value
         dump         - Dump all data
   noconfigure|noconf - Exit conf mod
[EXEC] Command mode:
   oled_128x64i2c
                 text
                 invert
                 clean
                 draw_line
                 draw_rect
                 show_debug_page
                 wakeup_oled_debug_page_execute
                 poweron
                 poweroff
   system
         memfree
         gccollect
         reboot
         wifirssi
         heartbeat
         time
   gpio
       RGB
       RGB_deinit
       Servo
       Servo_deinit
```
 
### Embedded config handler
 
```  
socketclient --dev slim01 conf '<a>' dump
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: slim01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Device was found: slim01
[configure] slim01
  stapwd    :  <your_wifi_password>
  gmttime   :  1
  nwmd      :  STA
  soctout   :  100
  timirq    :  True
  appwd     :  Admin123
  devfid    :  slim01
  extirq    :  True
  dbg       :  True
  timirqcbf :  oled_128x64i2c show_debug_page
  hwuid     :  0x500x20x910x680xc0xf7
  staessid  :  <your_wifi_name>
  devip     :  10.0.1.73
  extirqcbf :  oled_128x64i2c invert
  socport   :  9008
  pled      :  True
```

### Load Modules - User defined functions

```
socketclient --dev slim01 system memfree
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: slim01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Device was found: slim01
CPU[Hz]: 160000000
GC MemFree[byte]: 5552
```

## Node Configuration

| Parameters names | Reboot required | Description |
| :----------: | :-----------: | ----------- |
| staessid   |        Yes      | 	Wifi station name 
| stapwd		|        Yes      | Wifi station password
| devfid		|        No       | Device friendly name / AP name - access point mode
| appwd		|        Yes      | AP password - access point mode
| pled			|        Yes      | Progress led - heart beat
| dbg	       |        Yes      |	Debug mode - enable system printouts		
| soctout		|        Yes      | Socket / Web server connection timeout (because single user | handling)
| socport		|         Yes     | Socket / Web server service port
| timirg		|        Yes      | Timer interrupt enable - "subprocess"
|timirqcbf   |        No        | Callback function (LM) from config, example: `oled_128x64i2c show_debug_page`
| extirq     |       Yes        | External event interrupt - "subprocess"
| extirqcbf   |      No        | Callback function (LM) from config, example: `oled_128x64i2c invert`
| gmttime    |        Yes      | NTP - RTC - timezone setup 
| nwmd 		|       N/A       |STATE STORAGE - system saves nw mode here - AP / STA
| hwuid		|      N/A         | STATE STORAGE - hardwer address - dev uid
| devip		|       N/A         | STATE STORAGE - system stores device ip here


## Logical pin accociation

```
'progressled': 16,    # BUILT IN LED
'servo': 15,          # D8
'pwm_red': 2,         # D4
'pwm_green': 13,      # D7
'pwm_blue': 0,        # D3
'i2c_sda': 4,         # D2
'i2c_scl': 5,         # D1
'button': 12          # D6
```

## SocketClient

### Config:

```json
{
    "<UINIGUE ID - MAC ADDRESS (UID)>": [
        "<MICROS DEVIDE IP (DEVIP)>",
        "<MICROS DEVIDE MAC>",
        "<MICROS FRIENDLY NAME (FUID)>"
    ]
}
```

> NOTE: MUST TO HAVE DATA FOR CONNECTION: 
```
<MICROS DEVIDE IP (DEVIP)>
```

> All the other data can be dummy value :) 

### SocketClient usage:


```
source setup
socketclient

or

cd tool/
./socketClient.py
```

#### Interactive mode

```
socketclient
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: slim01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Choose a device index: 0
Device IP was set: 10.0.1.73
slim01 $  help
hello - default hello msg - identify device (SocketServer)
exit  - exit from shell socket prompt (SocketServer)
[CONF] Configure mode:
   configure|conf     - Enter conf mode
         Key          - Get value
         Key:Value    - Set value
         dump         - Dump all data
   noconfigure|noconf - Exit conf mod
[EXEC] Command mode:
   oled_128x64i2c
                 text
                 invert
                 clean
                 draw_line
                 draw_rect
                 show_debug_page
                 wakeup_oled_debug_page_execute
                 poweron
                 poweroff
   system
         memfree
         gccollect
         reboot
         wifirssi
         heartbeat
         time
   gpio
       RGB
       RGB_deinit
       Servo
       Servo_deinit
slim01 $  gpio RGB(0,0,0)
SET RGB
slim01 $  exit
Bye!
exit and close connection from ('10.0.1.7', 51733)
```

git push -u origin master
