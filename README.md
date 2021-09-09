# ![LOGO](./media/logo_mini.png?raw=true) micrOS

### micropython based IoT framework for wifi capable arm based microcontrollers and much more...

![MICROSVISUALIZATION](./media/micrOS_welcome.png?raw=true)

✉️ 📡 Generic communication API (expose module functions) <br/>
⚙️ 📝 Device initialization from user config <br/>
📲 💻 Communication over WiFi: application calls and configuration <br/>
🧩  Codeless end user experience via phone client <br/>
🚪 No external server or service required <br/>
⚠️ 🛡 Works on Local Network (WiFi-WLAN) <br/>
🛠 Easy to customize, create your own Load Modules: <br/>
Just write and copy **LM_** your_app **.py** python script to your device and call any function.<br/>
🦾 Built-in scheduling (IRQ):<br/>
- Time stamp based <br/>
- Simple periodic <br/>

🚀🎈Lightweight and high performance core system that leaves you space 😎<br/>

## ◉ Shortcuts:
1. micrOS Client Application [link](https://github.com/BxNxM/micrOS#micrOS-Client-Application)
2. micrOS Installer [link](https://github.com/BxNxM/micrOS#installing-micros-with-devtoolkit-from-macos--windows--linux)
3. micrOS Tutorials [link](https://github.com/BxNxM/micrOS#micros-tutorial)
4. micrOS System and features [link](https://github.com/BxNxM/micrOS#micros-system-message-function-visualization)
5. micrOS Node configuration [link](https://github.com/BxNxM/micrOS#micros-node-configuration-parameters-with-description)

Thingiverse 3D print projects: [link](https://www.thingiverse.com/micros_framework/designs)

----------------------------------------
----------------------------------------

## micrOS Client Application

### AppStore
[![AppStoreURL](./media/store/AppStoreBadge.svg)](https://apps.apple.com/hu/app/micros-client/id1562342296)

### PlayStore
[![PlayStore](./media/store/GooglePlayBadge.png)](https://play.google.com/store/apps/details?id=com.BMT.micrOSClient)

----------------------------------------

## Installing micrOS with DevToolKit from macOS / Windows / Linux

That repo not only contains the micrOS core codes provide several tools like

- Install new device via USB
- Device scan
- OTA updates (over wifi)
- Host side python app execution with device communication
- etc.

> Note: The main purpose to install micropython on the board and put all micrOS resources from micrOS/mpy-MicrOS to the board.

### 1. Clone **micrOS** repo:

Contains code for the supported boards for installation, the development, deployment and server tools, all written in python.

> Note: Install git manually for Windows before this step

```
git clone https://github.com/BxNxM/micrOs.git
```

### 2. Download python 3.8

Link for python 3.8 [download](https://www.python.org/downloads/release/python-383/)

> Note: Allow extend system path with that python version (installation parameter)
> On **Windows**: RUN AS ADMINISTARTOR

### 3. Install serial driver for board connection via USB

Find the required driver in the cloned repo.

- For Windows
	
```
micrOs/driver_cp210x/CP210x_Universal_Windows_Driver
```
	
- For macOS
	
```
micrOs/driver_cp210x/SiLabsUSBDriverDisk.dmg
```

### 4. ONLY ON WINDOWNS: Special dependencies

You will need **C++ compiler** to able to install all python pip dependencies (defined in the tool/requirements.txt)

Link for download:

```
https://support.microsoft.com/en-us/topic/the-latest-supported-visual-c-downloads-2647da03-1eea-4433-9aff-95f26a218cc0?fbclid=IwAR3_sC43aIkQ7TaCIyO3LnJAH5YEM22GavxngTS-X08Z2p1rJq12_vrX6FU
```

### 5. Execute **devToolKit** GUI

It will open a graphical user interface for micrOS device management.

```
python3 micrOS/devToolKit.py
```

- Verified OS list for development and deployment:
	- macOS
	- Raspbian (pyQT5 limitation)
	- Windows

	
- Example

```
1. Select BOARD TYPE
2. Select MICROPYTHON VERSION
3. Click on [Deploy (USB)] button
```

It will install your board via USB with default settings. Continue with your mobile app...  

![MICROSVISUALIZATION](./media/micrOSToolkit.gif?raw=true)

----------------------------------------

## micrOS Video Tutorials

### 1.1 Prepare micrOS devToolKit for deployment [macOS]

[![micrOSAppBasics](./media/thumbnails/install_on_mac.jpg)](https://www.youtube.com/watch?v=heqZMTUAWcg&t)

### 1.2 Prepare micrOS devToolKit for deployment [Windows]

**Coming Soon**

### 2. Basic setup with micrOS Client App

[![micrOSAppBasics](./media/thumbnails/first_configuration.jpg)](https://www.youtube.com/watch?v=xVNwHnBs1Tw)

	
### 3. How to OTA update device
### 4. Widgets and Load Modules via micrOS Client  

How to get available module list
Overview of micrOS Client UI

### 5. Configuration via micrOS Client

Idea behind: network, time, boothook, irqs, cron
Set some stuff in config ...

### 6. Get familier with micrOS shell

micrOS terminal
built-in commands, Load Modules

### 7. How to customize or contribute to micrOS

Create custom Load Modules (LMs)

----------------------------------------

## micrOS System, message-function visualization

![MICROSVISUALIZATION](./media/micrOS.gif?raw=true)

>Note: **Python Socket Client** for application development also available besides smartphone application (example below).


----------------------------------------

## micrOS Framework Features💡

- **micrOS loader** - starts micrOS or WEBREPL(update / recovery modes)
	- **OTA update** - push update over wifi (webrepl automation) / monitor update and auto restart node
- **Config handling(*)** - user config - node_config.json
	- Accessable over socket interface or Phone client
- **[L]oad [M]odule** aka **application** handling
	- Lot of built-in functions
	- Create your own module with 2 easy steps
		- Create a file in `MicrOS` folder like: `LM_<your_app_name>.py`
		- Copy your py file to the board `devToolKit.py -m` or `devToolKit.py -i` or `ampy
- **Boot phase** handling - preload Load Module(s) - pinout initialization from node_config
- **Network handling** - based on node_config 
	- STA / AP
	- NTP setup
	- Static IP configuration
- **Socket interpreter** - wireless communication interface with the nodes
	- **System commands**: `help, version, reboot, webrepl, etc.`
		- webrepl <--> micrOS interface switch  
	- **Config(*)** SET/GET/DUMP
	- **LM** - Load Module function execution (application modules)
- **Scheduling / External events** - Interrupt callback - based on node_config 
	- Time based
		- simple LM task pool execution
			- `Timer(0)` 
		- cron [time stump:LM task] pool execution
			- `Timer(1)` 
	- Event based
		-  Set trigger event up/down/both with LM callback function
- **Background Job** aka **BgJob**
		- Capable of execute [L]oad [M]odules in a background thread
		- WARNING, limitation: not use with IRQs and in micrOS config
		- Invoke with single execution `&` or loop execution `&&`
		- Example:
			- In loop: `system heartbeat &&`
			- Single call: `system heartbeat &`
		- Stop thread: `bgjob stop`
		- Show thread ouput and status: `bgjob show` 
- **[L]ogical [P]inout** handling - lookuptables for each board
	- Predefined pinout modules for esp32, tinyPico, esp8266
	- Create your pinout based on `LP_esp32.py`, naming convencion: `LP_<name>.py`
	- To activate your custom pinout set `cstmpmap` config parameter to `<name>`


DevToolKit CLI feature:

- Socket client python plugin - interactive - non interactive mode

## Built in pheriphery support

### Sensors / inputes

![micrOS project Pheriphery Support](./media/microsPheriphery_sensors.png)</br>

### Actuators / outputs

![micrOS project Pheriphery Support](./media/microsPheriphery_actuators.png)</br>

### Power supply

![micrOS project Pheriphery Support](./media/microsPheriphery_power.png)</br>

----------------------------------------

## Device Pinouts for wiring

### Logical pin association handling

[MicrOS/LogicalPins.py](./micrOS/LogicalPins.py)

LogicalPin lookup tables:

- [tinypico](./micrOS/LP_tinypico.py)
- [esp32](./micrOS/LP_esp32.py)
- [esp8266](./micrOS/LP_esp8266.py)

> Note: Good idea to use costant variable for pin map declaration, check the files for more info, These files are also precompiled automatically into byte steams -> `.mpy`

![MicrOSESP8266pinout](./media/NodeMCUPinOutTinyPico.png?raw=true)

![MicrOSESP8266pinout](./media/NodeMCUPinOutESP32.png?raw=true)

![MicrOSESP8266pinout](./media/NodeMCUPinOutESP8266.png?raw=true)


----------------------------------------

# System Architecture 

![MICROSARCHITECTURE](./media/MicrOSArchitecture.png?raw=true)

> Secure Core (OTA static modules): `boot.py`, `micrOSloader.mpy`, `Network.mpy`

## Networking - automatic network modes

![MICROSNWMODES](./media/micrOSNetworking.png?raw=true)

### RELESE NOTE

|  VERSION (TAG) |    RELEASE INFO    |  MICROS CORE MEMORY USAGE  |  SUPPORTED DEVICE(S) | APP PROFILES | Load Modules  |     NOTE       |
| :----------: | :----------------: | :------------------------:   |  :-----------------: | :------------: | :------------:| -------------- |
|  **v0.1.0-0** | [release_Info-0.1.0-0](./release_info/micrOS_ReleaseInfo/release_0.1.0-0_note.md)| 13 - 28 % (1216-2544byte) | esp8266 | [App Profiles](./release_info/node_config_profiles) | [LM manual](./release_info/micrOS_ReleaseInfo/release_sfuncman_0.1.0-0.json)| Stable Core with applications - first release
|  **v0.4.0-0** | [release_Info-0.4.0-0](./release_info/micrOS_ReleaseInfo/release_0.4.0-0_note_esp8266.md)| 26 - 53 % (2512-5072byte) | esp8266 | [App Profiles](./release_info/node_config_profiles) | [LM manual](./release_info/micrOS_ReleaseInfo/release_sfuncman_0.4.0-0.json)| micrOS multi device support with finalized core and so more. OTA update feature.
|  **v0.4.0-0** | [release_Info-0.4.0-0](./release_info/micrOS_ReleaseInfo/release_0.4.0-0_note_esp32.md)| 23 - 28 % (17250-20976byte) | esp32 | [App Profiles](./release_info/node_config_profiles) | [LM manual](./release_info/micrOS_ReleaseInfo/release_sfuncman_0.4.0-0.json)| micrOS multi device support with finalized core and advanced task scheduler based on time, and and so more. OTA update feature.
|  **v1.0.0-0** | [release_Info-1.0.0-0](./release_info/micrOS_ReleaseInfo/release_1.0.0-0_note_esp32.md)| 15 - 23 % (10394-15488byte) | esp32 | [App Profiles](./release_info/node_config_profiles) | [LM manual](./release_info/micrOS_ReleaseInfo/release_sfuncman_1.0.0-0.json)| Release of v1 micrOS, timer and event based irqs, cron task scheduling, realtime communication, multiple device support. OTA, etc. 
|  **v1.2.2-0** | [release_Info-1.2.2-0](./release_info/micrOS_ReleaseInfo/release_1.2.2-0_note_esp32.md)|  10-25 % | esp32 | [App Profiles](./release_info/node_config_profiles) | [LM manual](./release_info/micrOS_ReleaseInfo/release_sfuncman_1.2.2-0.json)| Public Release of v1 micrOS, timer and event based irqs, cron task scheduling, realtime communication, multiple device support. OTA update, thread from socket shell (beta) etc.


----------------------------------------

## micrOS **node configuration**, parameters with description

|        Config keys   |   Default value and type    | Reboot required |       Description       |
| -------------------- | :-------------------------: | :-------------: | ----------------------- |
| **devfid**           |    `node01`  `<str>`        |       Yes        | Device friendly "unique" name - also used for AccessPoint nw mode (AP name)
| **boostmd**          |      `True`  `<bool>`       |      Yes        | boost mode - set up cpu frequency low or high 8MHz-16Mhz-24MHz (depends on boards)
| **staessid**         |   `your_wifi_name` `<str>`  |       Yes       | Wifi router name (for default connection mode)
| **stapwd**           | `your_wifi_passwd` `<str>`  |       Yes       | Wifi router password (for default connection mode)
| **appwd**            |   `ADmin123`  `<str>`       |       Yes       | Device system password.: Used in AP password (access point mode) + webrepl password
| **auth**             |     `False` `<bool>`        |       Yes       | Enables socket password authentication, password: `appwd`. Passwordless functions: `hello`, `version`, `exit`. **WARNING** OTA upade not supported in this mode.
| **gmttime**          |     `1`   `<int>`           |       Yes       | NTP - RTC - timezone setup (GMT)
| **boothook**         |    `n/a` `<str>`            |      Yes        | Callback function(s) list for priority Load Module(s) execution in boot sequence [before network setup!]. Add LoadModule(s) here, separator `;`. Example: Set LED colors / Init custom module(s) / etc.
| **timirq**           |     `False`  `<bool>`       |       Yes       | Timer(0) interrupt enabler - background "subprocess" emulation, timer based infinite loop for the LoadModule execution
| **timirqcbf**        |      `n/a`   `<str>`        |      Yes        | if `timirq` enabled, calls the given Load Module(s), e.x.: `module function optional_parameter(s)`, task separator: `;`
| **timirqseq**        |    `1000`   `<int>`         |      Yes        | Timer interrupt period in ms, default: `3000` ms (for `timirq` infinite loop timer value)
| **cron**             |     `False`  `<bool>`       |       Yes       | Cron enabler, Timer(1) interrupt enabler - time based task scheduler.
| **cronseq**          |    `3000`   `<int>`         |       Yes        | Cron (Timer(1)) interrupt period in ms, default: `3000` ms (for `cron` infinite loop timer value) 
| **crontasks**        |     `n/a`  `<str>`          |       Yes        | Cron scheduler input, task format: `WD:H:M:S!module function` e.g.: `1:8:0:0!system heartbeat`, task separator in case of multiple tasks: `;`. [WD:0-6, H:0-23, M:0-59, S:0-59] in case of each use: `*` **Note**: If the value was `n/a` default, then reboot required.
| **extirq**           |     `False`  `<bool>`       |      Yes        | External event interrupt enabler - Triggers when "input signal upper edge detected" - button press happens
| **extirqcbf**        |     `n/a`  `<str>`          |      Yes        | `extirq ` enabled, calls the given Load Module, e.x.: `module function optional_parameter(s)`
| **extirqtrig**       |     `n/a`   `<str>`         |      Yes        | Sets trigger mode for external irq, signal phase detection, values `up` (default: `n/a`) or `down` or `both`.
| **cstmpmap**         |      `n/a`  `<str>`          |      Yes       | Custom pin mapping for custom function setups. (1) copy your pinmap aka [L]ogical[P]ins (python variables in module) to the board, file format: `LP_<pin_map_name>.py` or `.mpy`, (2) set `<pin_map_name>` as a parameter.
| **pled**             |     `True`    `<bool>`      |      Yes        | Progress led enabler - light pulse under processing - "heart beat"
| **dbg**	            |     `True`    `<bool>`      |       Yes       | Debug mode - enable micrOS system printout, server info, etc.
| **soctout**          |   `100`      `<int>`        |      Yes        | Socket server connection timeout (because single process socket interface)
| **socport**          |    `9008`  `<int>`          |      Yes        | Socket server service port (should not be changed due to client and API inconpatibility)
| **irqmreq**          |      `6000`  `<int>`        |       No        | Controlls memory overload avoidance (byte). `timirq` requires this amount of memory for activation. `irqmreq`*0.7 is the memory limit for `extirq` enabling. **WARNING**: If the system gets memory overloaded with irq(s) micropython crashes and stucks in cycling reboot!!!
| **irqmembuf**        |    `1000` `<int>`           |       Yes       | IRQ emergency memory buffer allocation (in byte) when `timirq` or `exitirq` enabled.
| **devip**            |      `n/a`  `<str>`         |    Yes(N/A)      | Device IP address, (first stored IP in STA mode will be the device static IP on the network), you are able to provide specific static IP here.
| **nwmd**             |     `n/a`  `<str>`          |      N/A        | USED BY SYSTEM (state storage) - system saves network mode here - `AP` or `STA`
| **hwuid**            |      `n/a`  `<str>`         |      N/A        | USED BY SYSTEM (state storage) - hardware address - dev uid
| **guimeta**          |      `n/a`  `str`           |      No        | USED BY micrOS Client (state storage) - stores - offloaded parameter type in config. Clinet widget meta data.

> Note: Default empty value: `n/a` in case of string parameter.
> Note: Cron is only available on devices with Timer(**1**): esp32
> 


----------------------------------------
----------------------------------------


## Developer Quick guide

#### Erase device & Deploy micropython & Install micrOS 

Go to micrOS repo, where the `devToolKit.py` located.

```
cd micrOs 
./devToolKit.py --make
```
> Note: Follow the steps :)


Search and Connect to the device

```
./devToolKit.py -s -c
```

----------------------------------------

**User commands**

```
./devToolKit.py -h

optional arguments:
  -h, --help            show this help message and exit

Base commands:
  -m, --make            Erase & Deploy & Precompile (MicrOS) & Install (MicrOS)
  -r, --update          Update/redeploy connected (usb) MicrOS. - node config will be restored
  -c, --connect         Connect via socketclinet
  -o, --OTA				 OTA update, over wifi (webrepl)
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
./devToolKit.py -stat

or

./devToolKit.py --node_status
```

Output:

```
       [ UID ]                [ FUID ]		[ IP ]		[ STATUS ]	[ VERSION ]	[COMM SEC]
micr123c8456OS            RingLamp          10.0.1.75	ONLINE		1.0.1-0		0.319
micr123456OS            BigRGB            10.0.1.119	ONLINE		1.0.1-0		0.418
micr12345c860OS                CamLed            10.0.1.84	ONLINE		1.0.1-0		0.498
micr12c83456OS                airquality        10.0.1.50	ONLINE		1.0.1-0		0.495
micr5123456OS            tinyPico          10.0.1.189	ONLINE		<n/a>		n/a
micr212345670OS            nodepro           10.0.1.140	OFFLINE		<n/a>		n/a
micrf1234562a0OS            BedLamp           10.0.1.45	ONLINE		1.0.1-0		0.317
micr212345661xOS            CatGamePro       10.0.1.23	ONLINE		1.0.1-0		0.393
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
./devToolKit.py -c -p '--dev node01 help'
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: node01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Device was found: node01
node01 $  help
[MICROS]   - commands (SocketServer built-in)
   hello   - default hello msg - identify device
   version - shows micrOS version
   exit    - exit from shell socket prompt
   reboot  - system safe reboot
   webrepl - start web repl for file transfers - update
[CONF] Configure mode (InterpreterShell built-in):
  conf       - Enter conf mode
    dump       - Dump all data
    key        - Get value
    key value  - Set value
  noconf     - Exit conf mode
[EXEC] Command mode (LMs):
   L298N_DCmotor
                help
   VL53L0X
          measure
          help
   adc
      measure
      action_fltr
      help
   air
      help
   bledns
         advert
         scan
         list
         make
         help
   bme280
         help
   co2
      help
   dht11
        help
   dht22
        help
   dimmer
         help
   distance_HCSR04
                  distance_mm
                  distance_cm
                  deinit
                  help
   esp32
        hall
        temp
        touch
        battery
        help
   i2c
      scan
      help
   intercon
           help
   light_sensor
               help
   motion_sensor
                get_PIR_state
                PIR_deinit
                help
   neopixel
           help
   oled_128x64i2c
                 help
   oled_widgets
               help
   ph_sensor
            measure
            help
   repair
         help
   rgb
      help
   rgbfader
           help
   servo
        help
   switch
         help
   system
         help
   test
       run
       help
   tinyrgb
          help
   tinyrgb
          setrgb
          getstate
          toggle
          wheel
          help
```
 
### Embedded config handler
 
```  
./devToolKit.py -c -p '--dev node01 conf <a> dump'
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: node01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Device was found: node01
[configure] node01
  gmttime   :        1
  irqmreq   :        6000
  pled      :        True
  crontasks :        *:19:2:0!rgbfader fade 0 107 6 120;*:19:4:0!rgbfader fade 0 92 2 120;*:19:6:0!rgbfader fade 128 0 7 120;*:19:8:0!rgbfader fade 107 7 0 120;*:19:10:0!rgbfader fade 0 31 9 120;*:19:12:0!rgbfader fade 310 1 2 120;*:19:14:0!rgbfader fade 11 1 0 120;*:23:0:0!rgbfader fade 0 0 0 3600;*:7:0:0!rgbfader fade 0 107 6 3600
  soctout   :        100
  devip     :        10.0.1.119
  version   :        1.0.1-0
  auth      :        False
  cronseq   :        3000
  guimeta   :        ...
  cron      :        True
  timirqcbf :        rgbfader transition
  devfid    :        BigRGB
  cstmpmap  :        n/a
  boostmd   :        True
  socport   :        9008
  dbg       :        True
  irqmembuf :        1000
  timirqseq :        1000
  extirq    :        False
  staessid  :        <your-wifi-name>; <your-wifi-name2>
  appwd     :        ADmin123
  stapwd    :        <your-wifi-pwd>; <your-wifi-pwd2>
  timirq    :        True
  hwuid     :        micr8caab594d4c4OS
  extirqcbf :        n/a
  nwmd      :        STA
  extirqtrig:        n/a
  boothook  :        rgbfader fader_cache_load_n_init
```

### Load Modules - User defined functions

```
./devToolKit.py -c -p '--dev node01 system info'
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Device was found: node01
CPU clock: 24 [MHz]
MemFree: 25 kB 80 byte
FSFREE: 88 %
Plaform: esp32
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
[0] Device: node01 - 10.0.1.119 - 0x500x20x910x680xc0xf7
Choose a device index: 0
Device IP was set: 10.0.1.119
node01 $  help
[MICROS]   - commands (SocketServer built-in)
   hello   - default hello msg - identify device
   version - shows micrOS version
   exit    - exit from shell socket prompt
   reboot  - system safe reboot
   webrepl - start web repl for file transfers - update
[CONF] Configure mode (InterpreterShell built-in):
  conf       - Enter conf mode
    dump       - Dump all data
    key        - Get value
    key value  - Set value
  noconf     - Exit conf mode
[EXEC] Command mode (LMs):
   L298N_DCmotor
                help
   VL53L0X
          measure
          help
   adc
      measure
      action_fltr
      help
   air
      help
   ...
node01 $  exit
Bye!

```

## Project structure

### MicrOS resources library

```
micrOS/
├── BleHandler.py
├── Common.py
├── ConfigHandler.py
├── Hooks.py
├── InterConnect.py
├── InterpreterCore.py
├── InterpreterShell.py
├── InterruptHandler.py
├── LP_esp32.py
├── LP_esp8266.py
├── LP_tinypico.py
├── LogicalPins.py
├── Network.py
├── Scheduler.py
├── SocketServer.py
├── TinyPLed.py
├── boot.py
├── micrOS.py
├── micrOSloader.py
├── node_config.json
├── reset.py
```
> Note: Core MicrOS components

```
micrOS/
├── LM_L298N_DCmotor.py
├── LM_VL53L0X.py
├── LM_bledns.py
├── LM_bme280.py
├── LM_co2.py
├── LM_dht11.py
├── LM_dht22.py
├── LM_dimmer.py
├── LM_distance_HCSR04.py
├── LM_esp32.py
├── LM_i2c.py
├── LM_intercon.py
├── LM_light_sensor.py
├── LM_neopixel.py
├── LM_oled_128x64i2c.py
├── LM_oled_widgets.py
├── LM_ph_sensor.py
├── LM_repair.py
├── LM_rgb.py
├── LM_rgbfader.py
├── LM_servo.py
├── LM_switch.py
├── LM_system.py
├── LM_tinyrgb.py
```
> LM (Load Modules) - Application logic - accessable over socket server as a command

```
micrOS/
├── node_config.json
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
mpy-micrOS/
├── BleHandler.mpy
├── Common.mpy
├── ConfigHandler.mpy
├── Hooks.mpy
├── InterConnect.mpy
├── InterpreterCore.mpy
├── InterpreterShell.mpy
├── InterruptHandler.mpy
├── LM_L298N_DCmotor.mpy
├── LM_VL53L0X.py
├── LM_bledns.py
├── LM_bme280.mpy
├── LM_co2.mpy
├── LM_dht11.mpy
├── LM_dht22.mpy
├── LM_dimmer.mpy
├── LM_distance_HCSR04.py
├── LM_esp32.py
├── LM_i2c.py
├── LM_intercon.mpy
├── LM_light_sensor.mpy
├── LM_neopixel.mpy
├── LM_oled_128x64i2c.mpy
├── LM_oled_widgets.mpy
├── LM_ph_sensor.py
├── LM_repair.mpy
├── LM_rgb.mpy
├── LM_rgbfader.mpy
├── LM_servo.mpy
├── LM_switch.mpy
├── LM_system.mpy
├── LM_tinyrgb.mpy
├── LP_esp32.mpy
├── LP_esp8266.mpy
├── LP_tinypico.mpy
├── LogicalPins.mpy
├── Network.mpy
├── Scheduler.mpy
├── SocketServer.mpy
├── TinyPLed.mpy
├── boot.py
├── micrOS.mpy
├── micrOSloader.mpy
└── reset.mpy
44 files
```

> Note: These resources will be copy to the micropython base image, all `LM_`s are optional.

### Release info and Application Profiles

```
├── release_info
│   ├── micrOS_ReleaseInfo
│   │   ├── release_0.1.0-0_note.md
│   │   ├── release_0.4.0-0_note_esp32.md
│   │   ├── release_0.4.0-0_note_esp8266.md
│   │   ├── release_sfuncman_0.1.0-0.json
│   │   └── release_sfuncman_0.4.0-0.json
│   └── node_config_profiles
│       ├── README.md
│       ├── catgame_profile-node_config.json
│       ├── catgame_profile_command_examples.txt
│       ├── default_profile-node_config.json
│       ├── default_profile_command_examples.txt
│       ├── dimmer_profile-node_config.json
│       ├── dimmer_profile_command_examples.txt
│       ├── heartbeat_profile-node_config.json
│       ├── heartbeat_profile_command_examples.txt
│       ├── lamp_profile-node_config.json
│       ├── lamp_profile_command_examples.txt
│       ├── neopixel_profile-node_config.json
│       └── neopixel_profile_command_examples.txt
```

> Note:  Under node_config_profiles you can find **configuration temaples**, named **profiles** (devenv automatically able to inject these under deployment) - there are also **command examples** for each application.

> **MicrOS_Release_Info** folder(s) conatins system verification logs like:
> 
> - bootup log with different configurations
> - application execution log
> - memory measurements

### Other project resoures 

```
apps/
├── AirQualityBME280_app.py
├── AirQualityDHT22_CO2_app.py
├── AnanlogLED_app.py
├── CatGame_app.py
├── Dimmer_app.py
├── GetVersion_app.py
├── NeopixelTest_app.py
├── Template_app.py
```

----------------------------------------

## HINTS

- Save **screen** console buffer (**output**)
Press `ctrl + A :` and type `hardcopy -h <filename>`

- Create callgraph: [pycallgraph](http://pycallgraph.slowchop.com/en/master/)

- Convert PNG/JPG-s to GIF: `convert -delay 60 ./*.png mygif.gif`

- Build micropython with frozen resources: https://github.com/micropython/micropython/tree/master/ports/esp8266

- micrOS source code lines of code:

```bash
Ferenc@Bans-MBP:micrOS$ core_files=($(ls -1 | grep '.py' | grep -v 'LM_')); all_line_codes=0; for coref in ${core_files[@]}; do content_lines_cnt=$(cat $coref | grep -v -e '^$' | wc -l); all_line_codes=$((all_line_codes+content_lines_cnt)); echo -e "$content_lines_cnt\t$coref"; done; echo -e "SUM OF CODE LINES: $all_line_codes"
      65	BgJob.py
     154	BleHandler.py           -> beta code
      17	Common.py               -> decorators for LMs
     232	ConfigHandler.py
      53	Hooks.py
      42	InterConnect.py
      83	InterpreterCore.py
     180	InterpreterShell.py
     111	InterruptHandler.py
      37	LP_esp32.py
      21	LP_esp8266.py
      54	LP_tinypico.py
      41	LmExecCore.py
      28	LogicalPins.py
     168	Network.py              -> FSCO (ForceCoreOTA update)
     124	Scheduler.py
     283	SocketServer.py
      24	TinyPLed.py
      16	boot.py                 -> FSCO
      54	micrOS.py
     101	micrOSloader.py         -> FSCO
       5	reset.py                -> only used for webrepl manual reset
SUM OF CODE LINES: 1893
```

GIT:
- Add git tag: `git tag -a vX.Y.Z-K -m "tag message"`

- Publish tags: `git push origin --tags`

- Pretty git view: `git log --pretty=oneline`

- File change list: `git diff --name-only fbb4875609a3c0ee088b6a118ebf9f8a500be0fd HEAD | grep 'mpy-MicrOS'`

- GitHub embed youtube link: `https://github.com/itskeshav/Add-youtube-link-in-Readme.md`

git push -u origin master
