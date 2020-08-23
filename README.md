# micrOS - IOT platform

## micrOS system, message-function visualization 

![MICROSVISUALIZATION](https://github.com/BxNxM/MicrOs/blob/master/media/micrOS.gif?raw=true)

>Note: **Python Socket Client** for application development also available besides smartphone application (example below).


## MicrOS Framework Features

- **Config handling** - node_config.json
- **Boot phase** handling - preload modules - I/O initialization from node_config
- **Socket interpreter** - wireless communication interface with the devices/nodes
	- **System commands**: `help, version, reboot, etc.` 
	- **Config** SET/GET/DUMP
	- **LM** - Load Module function execution
- **Network handling** - based on node_config 
	- STA / AP 
	- NTP setup
	- static IP configuration
- **Scheduling / External events** - Interrupt callback - based on node_config 
	- Time based
	- Event based
- Load Module **application** handling
	- Lot of built-in functions
	- Clreate you own module with 2 easy steps
		- Create a file in `MicrOS` folder like: `LM_<your_app_name>.py`
		- Copy your py file to the board `devToolKit.py -m` or `devToolKit.py -i` or `ampy`	  
	
- Socket client - interactive - non interactive mode 


## System Architecture

![MICROSARCHITECTURE](https://github.com/BxNxM/MicrOs/blob/master/media/MicrOSArchitecture.png?raw=true)

## Device Pinout

![MicrOSESP8266pinout](https://github.com/BxNxM/MicrOs/blob/master/media/NodeMCUPinOutESP8266.png?raw=true)

![MicrOSESP8266pinout](https://github.com/BxNxM/MicrOs/blob/master/media/NodeMCUPinOutESP32.png?raw=true)

### RELESE NOTE

|  VERSION (TAG) |    RELEASE INFO    |  MICROS CORE MEMORY USAGE  |         COMMIT         |  SUPPORTED DEVICE(S) | APP PROFILES | Load Modules  |     NOTE       |
| :----------: | :----------------: | :------------------------: | :--------------------: |  :-----------------: | :------------: | :------------:| -------------- |
|  **v0.1.0.0** | [release_Info-0.1.0-0](https://github.com/BxNxM/MicrOs/tree/master/release_info/micrOS_ReleaseInfo/release_0.1.0-0_note.md)| 13 - 28 % (1216-2544byte) | `aee52442c6577783c5230a51fbd0e660e08df3e6` | nodemcu - esp8266 | [App Profiles](https://github.com/BxNxM/MicrOs/tree/master/release_info/node_config_profiles) | [LM manual](https://github.com/BxNxM/MicrOs/tree/master/release_info/micrOS_ReleaseInfo/release_sfuncman_0.1.0-0.json)| Stable Core with applications - first release

## MicrOS Tutorial

> **Coming soon**

- How to deploy to device
- Configuration
- Built in function + Load Modules
- Client examples - terminal
- Client examples - smartphone app
- Backup config - cluster monitoring
- Create custom Load Modules (LMs)

> **Coming soon**

----------------------------------------

## Quick guide

### Supported OS for development

- MacOS
- Linux (Raspbain, Ubuntu, Debian) - beta

### Setup development environment

- Clone MicrOS repo:

```
git clone https://github.com/BxNxM/MicrOs.git
```

#### External Dependences

- **Deploy** dependences
	- esptool.py
	- ampy

- **Connection** dependences
	- screen (serial port connection)
	- tools/socketClient.py (devToolKit.py -c)
		- arp -a (device scanner)
		- ping (device scanner)

#### Erase device & Deploy micropython & Install MicrOS 

Go to micrOS repo, where the `devToolKit.py` located.

```
cd MicrOs 
./devToolKit.py --make
```
> Note: Follow the steps :)


Search and Connect to the device

```
./devToolKit.py -s -c
```

----------------------------------------

## micrOS **node configuration**, parameters with description

| Parameters names |   Default value and type    | Reboot required |          Description            |
| ---------------- | :-------------------------: | :-------------: | ------------------------------- |
| staessid         |   `your_wifi_name` `<str>`  |       Yes       | Wifi station name 
| stapwd		   | `your_wifi_passwd` `<str>`  |       Yes       | Wifi station password
| devfid		   |    `node01`  `<str>`        |       No        | Device friendly name / AP name  - access point mode
| appwd		       |   `ADmin123`  `<str>`       |       Yes       | AP password - access point mode
| pled			   |     `True`    `<bool>`      |      Yes        | Progress led - heart beat
| dbg	           |     `True`    `<bool>`      |       Yes       | Debug mode - enable system printout
| soctout		   |   `100`      `<int>`        |       Yes       | Socket / Web server connection timeout (because single user | handling)
| socport		   |    `9008`  `<int>`          |       Yes       | Socket / Web server service port
| timirq		   |     `False`  `<bool>`       |       Yes       | Timer interrupt enable - "subprocess"
| timirqcbf        |      `n/a`   `<str>`        |      Yes        | Callback function (LM) from config, example: `oled_128x64i2c show_debug_page`
| timirqseq        |    `3000`   `<int>`         |      Yes        | Timer interrupt period / sequence in ms, default: 3000 ms
| extirq           |     `False`  `<bool>`       |      Yes        | External event interrupt - "subprocess"
| extirqcbf        |     `n/a`  `<str>`          |      Yes        | Callback function (LM) from config, example: `oled_128x64i2c invert`
| boothook         |    `n/a` `<str>`            |      Yes        | Hook init functions from LMs, to be executed right after system boot up [before network setup!]
| irqmembuf        |    `1000` `<int>`           |       Yes       | IRQ emergency memory buffer configuration in case of `timirq` or `exitirq` is/are enabled: default 1000 byte.
| gmttime          |     `+1`   `<int>`          |        Yes      | NTP - RTC - timezone setup 
| nwmd 		       |     `n/a`  `<str>`          |       N/A       | STATE STORAGE - system saves nw mode here - AP / STA
| hwuid		       |      `n/a`  `<str>`         |       N/A       | STATE STORAGE - hardware address - dev uid
| devip		       |      `n/a`  `<str>`         |      N/A        | first stored IP in STA mode will be the device static IP on the network or set static IP manually here
| boostmd          |      `True`  `<bool>`       |     Yes         | boost mode - set up cpu frequency low or high

## Logical pin association

[MicrOS/LogicalPins.py](https://github.com/BxNxM/MicrOs/blob/master/MicrOS/LogicalPins.py)

```
'builtin': 16,    # BUILT IN LED - progress_led
'pwm_0': 15,      # D8 - servo
'pwm_1': 13,      # D7 - pwm_red
'pwm_2': 2,       # D4 - pwm_green / servo2
'pwm_3': 0,       # D3 - pwm_blue / neopixel
'i2c_sda': 4,     # D2 - OLED
'i2c_scl': 5,     # D1 - OLED
'pwm_4': 12,      # D6 - extirqpin
'simple_0': 16,   # D0 - dist_trigger
'pwm_5': 14,      # D5 - dist_echo
'simple_1': 10,   # SD3 - dht_pin
'adc_0': 0,       # ADC0 - CO2
'simple_2': 9     # SD2 - PIR
```

----------------------------------------

### Development toolkit in details

**User commands**

```
./devToolKit.py -h

optional arguments:
  -h, --help            show this help message and exit

Base commands:
  -m, --make            Erase & Deploy & Precompile (MicrOS) & Install (MicrOS)
  -r, --update          Update/redeploy connected (usb) MicrOS. - node config will be restored
  -c, --connect         Connect via socketclinet
  -p CONNECT_PARAMETERS, --connect_parameters CONNECT_PARAMETERS
                        Parameters for connection in non-interactivve mode.
```

**Search devices**

```
./devToolKit.py --search_devices

or

./devToolKit.py -s
```

**List discovered devices with status updates**

```
./devToolKit.py-stat

or

./devToolKit.py --node_status
```

Output:

```
       [ UID ]                [ FUID ]	[ IP ]		[ STATUS ]	[ MEMFREE ]	[ VERSION ]
420c0xf40x420x440xc420d6      Lamp	     10.0.1.12	ONLINE		4864 byte	0.1.0-0
420e00x980420x910xb420a2      airquality 10.0.1.50	ONLINE		3792 byte	0.0.9-27
420x500x204200x680x420f7      slim01	 10.0.1.157	ONLINE		890 byte    0.0.9-27	
```

**Developer commands**

```
Development & Deployment & Connection:
  -e, --erase           Erase device
  -d, --deploy          Deploy micropython
  -i, --install         Install MicrOS on micropython
  -l, --list_devs_n_bins
                        List connected devices & micropython binaries.
  -cc, --cross_compile_micros
                        Cross Compile MicrOS system [py -> mpy]
  -v, --version         Get micrOS version - repo + connected device.
  -ls, --node_ls        List micrOS node filesystem content.
  -u, --connect_via_usb
                        Connect via serial port - usb

Toolkit development:
  --dummy               Skip subshell executions - for API logic test.
```

## Socket terminal example - non interactive

### Identify device

```
./devToolKit.py -c -p '--dev slim01 hello'
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: slim01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Device was found: slim01
hello:slim01:0x500x20x910x680xc0xf7
```

### Get help

```
./devToolKit.py -c -p '--dev slim01 help'
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
./devToolKit.py -c -p '--dev slim01 conf <a> dump'
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
./devToolKit.py -c -p '--dev slim01 system memfree'
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: slim01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Device was found: slim01
CPU[Hz]: 160000000
GC MemFree[byte]: 5552
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

#### Interactive mode

```
./devToolKit.py -c 
or
./devToolKit.py -connect
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

## Project structure

### MicrOS resources library

```
├── MicrOS
│   ├── ConfigHandler.py
│   ├── Hooks.py
│   ├── InterpreterCore.py
│   ├── InterpreterShell.py
│   ├── LogicalPins.py
│   ├── Network.py
│   ├── SocketServer.py
│   ├── InterruptHandler.py
│   ├── boot.py
│   ├── main.py
```
> Note: Core MicrOS components

```
│   ├── LM_distance_HCSR04.py
│   ├── LM_light.py
│   ├── LM_motion_sensor.py
│   ├── LM_oled_128x64i2c.py
│   ├── LM_oled_widgets.py
│   ├── LM_servo.py
│   ├── LM_system.py
```
> LM (Load Modules) - Application logic - accessable over socket server as a command

```
│   └── node_config.json
```
> Note: System description config

### MicrOS development tools library

```
├── devToolKit.py
├── tools
│   ├── MicrOSDevEnv
```
> Note: devToolKit wrapper resources for development, deployment, precompile, etc.

```
│   ├── nwscan.py
│   ├── socketClient.py
```
> Note: devToolKit wrapper socket based connection handling

```
├── user_data
│   ├── device_conn_cache.json
│   └── node_config_archive
```
> Note: User data dir: conatins node connection informations (devToolKit --search_devices) and deployed node config backups are here.


### MicrOS deployment resources

Precompiled components with the actual user configured config location

```
├── mpy-MicrOS
│   ├── ConfigHandler.mpy
│   ├── Hooks.mpy
│   ├── InterpreterCore.mpy
│   ├── InterpreterShell.mpy
│   ├── InterruptHandler.mpy
│   ├── LM_distance_HCSR04.py
│   ├── LM_light.mpy
│   ├── LM_motion_sensor.py
│   ├── LM_oled_128x64i2c.mpy
│   ├── LM_oled_widgets.mpy
│   ├── LM_servo.py
│   ├── LM_system.mpy
│   ├── LogicalPins.mpy
│   ├── Network.mpy
│   ├── SocketServer.mpy
│   ├── boot.py
│   ├── main.py
│   └── node_config.json
```

> Note: These resources will be copy to the micropython base.

### Release info and Application Profiles

```
├── release_info
│   ├── MicrOS_Release_Info-0.1.0-0
│   └── node_config_profiles
```
> Note:  Under node_config_profiles you can find **configuration temaples**, named **profiles** (devenv automatically able to inject these under deployment) - there are also **command examples** for each application.

> **MicrOS_Release_Info** folder(s) conatins system verification logs like:
> 
> - bootup log with different configurations
> - application execution log
> - memory measurements

### Other project resoures 

```
├── apps
│   ├── CatGame_app.py
│   ├── Template.app.py
├── driver_cp210x
│   ├── Mac_OSX_VCP_Driver
│   └── SiLabsUSBDriverDisk.dmg
├── framework
│   └── esp8266-20191220-v1.12.bin
```

## HINTS

- Save **screen** console buffer (**output**)
Press `ctrl + A :` and type `hardcopy -h <filename>`

- Create callgraph: [pycallgraph](http://pycallgraph.slowchop.com/en/master/)

- Convert PNG/JPG-s to GIF: `convert -delay 60 ./*.png mygif.gif`  

- Build micropython with frozen resources: https://github.com/micropython/micropython/tree/master/ports/esp8266

GIT:
- Add git tag: `git tag -a vX.Y.Z-K -m "tag message"`

- Publish tags: `git push origin --tags`

- Pretty git view: `git log --pretty=oneline`


git push -u origin master
