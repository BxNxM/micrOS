# ![LOGO](./media/logo_mini.png?raw=true) micrOS

> **"The mini yet powerful operating system for DIY projects."**

![stable](https://img.shields.io/badge/master-HEAD-success)
![stable](https://img.shields.io/badge/micropython-OS-gold)
![async](https://img.shields.io/badge/async-task_manager-olive)
![config](https://img.shields.io/badge/config-manager-olive)
![cron](https://img.shields.io/badge/IRQs-Cron-olive)
![events](https://img.shields.io/badge/IRQs-Events-olive)
![web](https://img.shields.io/badge/Web-Rest-olive)
![web](https://img.shields.io/badge/Web-UI-olive)
![socket](https://img.shields.io/badge/Socket-Shell-olive)
![GPIO](https://img.shields.io/badge/GPIO-I2C-olive)
![clock](https://img.shields.io/badge/RTC-NTP-olive)
![wifi](https://img.shields.io/badge/Wifi-STA_or_AP-blue)
![OTA](https://img.shields.io/badge/OTA-Update-blue)
![ic1](https://img.shields.io/badge/InterCon-socket-blue)
![ic2](https://img.shields.io/badge/InterCon-espnow-blue)
<br/>
![tinypico](https://img.shields.io/badge/esp32-tinypico-purple)
![esp32S3](https://img.shields.io/badge/esp32-S3-purple)
![esp32S3](https://img.shields.io/badge/esp32-S3_RAM-purple)
![espCAM-esp-s](https://img.shields.io/badge/esp32-CAM_OV2640-purple)
![esp32-c6](https://img.shields.io/badge/esp32-C6_RISCV-purple)
![esp32-c3](https://img.shields.io/badge/esp32-C3_RISCV-purple)
![esp32S2](https://img.shields.io/badge/esp32-S2-purple)
![PYQT](https://img.shields.io/badge/esp32-PYQT-purple)
![raspberry-pico-w](https://img.shields.io/badge/raspberry-pico_W-critical)
![esp32-etc](https://img.shields.io/badge/esp32-etc.-purple)
<br/>


Thanks for ![GitHub stars](https://img.shields.io/github/stars/BxNxM/micrOS), follow us on:

[![Instagram](https://img.shields.io/badge/Instagram-%40micros_framework-%23E4405F?logo=instagram&logoColor=white)](https://www.instagram.com/micros_framework/)
[![YouTube](https://img.shields.io/badge/YouTube-micrOS_framework-red?logo=youtube&logoColor=white)](https://www.youtube.com/channel/UChRlJw7OYAoKroC-Mi75joA)
[![Facebook](https://img.shields.io/badge/Facebook-micrOS_framework-%231877F2?logo=facebook&logoColor=white)](https://www.facebook.com/Micros-Framework-103501302140755)
[![Thingiverse](https://img.shields.io/badge/Thingiverse-micrOS_3Dprints-%231489FF?logo=thingiverse&logoColor=white)](https://www.thingiverse.com/micros_framework/designs)
[![DockerHub](https://img.shields.io/badge/DockerHub-micrOS%20Gateway-blue)](https://hub.docker.com/r/bxnxm/micros-gateway)<br/>

[![PyPI Version](https://img.shields.io/pypi/v/micrOSDevToolKit)](https://pypi.org/project/micrOSDevToolKit/)


**micrOS** is a [micropython](http://micropython.org) based mini **application** execution **platform** with ShellCli (socket) and WebCli (http) **servers** and several **other** embedded **features**. 
> It uses direct wifi connection to access the exposed functionalities.<br/>

In case of any technical comments or requests, please use [![GitHub Discussions](https://img.shields.io/badge/GitHub-Discussions-green?logo=github&style=flat)](https://github.com/BxNxM/micrOS/discussions).

![MICROSVISUALIZATION](./media/micrOS_welcome.png?raw=true)
[![SHORTCUTS](./media/micrOS_shortcuts.png)](https://www.icloud.com/shortcuts/898c2a8033d64ff0b7aadc46ee491a35)<br/>
Example shortcut (usage of the API): [link](https://www.icloud.com/shortcuts/fab936abb34b45b5bda4c9f7abb256e9)<br/>
Access rest api over browser: `http://<nodename>.local`

----------------------------------------
----------------------------------------

📲 💻 ShellCli: Generic session-based communication API (OAM Interface) <br/>
📲 WebCli: Apple shortcuts compatible **REST API** and **HTTP Homepage** <br/>
&nbsp;&nbsp; ✉️ Expose upython module functions - telnet **TCP/IP** and **REST API** <br/>
⚙️ 📝 Device initialization from user config <br/>
🧩  Codeless end user experience via phone client <br/>
⚠️  No external server or service required for client-device communication <br/>
&nbsp;&nbsp; ⚠️ 🛡 Works on Local Network (WiFi-WLAN) <br/>
🛠 Easy to create custom application(s) aka create your own Load Modules: <br/>
🦾 Built-in scheduling (IRQs):<br/>
&nbsp;&nbsp; - Time stamp based <br/>
&nbsp;&nbsp; - Geolocation based clock setup + time tags: sunset, sunrise <br/>
&nbsp;&nbsp; - Simple periodic <br/>
🔄 Async **task manager** - start (&/&&) / list / kill / show <br/>

🚀🎈Lightweight and high performance core system that leaves you space 😎

## ◉ Shortcuts:
1. 📲 micrOS Client Application [link](https://github.com/BxNxM/micrOS/#micros-client-application)
2. micrOS Installer [link](https://github.com/BxNxM/micrOS/#installing-micros-with-devtoolkit-esp32-and-more)
3. ▶️ micrOS Tutorials [link](https://github.com/BxNxM/micrOS/#micros-video-tutorials)
4. micrOS System and features [link](https://github.com/BxNxM/micrOS/#micros-framework-features)
5. 🎮 Built-in app modules: [link](https://htmlpreview.github.io/?https://github.com/BxNxM/micrOS/blob/master/micrOS/client/sfuncman/sfuncman.html)
5. Pin mapping - GPIO [link](https://github.com/BxNxM/micrOS/#device-pinouts-for-wiring)
6. ⚙️ micrOS Node configuration [link](https://github.com/BxNxM/micrOS/#micros-node-configuration-parameters-with-description)
7. 🧑‍💻 micrOS create custom Load Modules: [link](./APPLICATION_GUIDE.md)
8. 📦 micrOS Package Management: [link](https://github.com/BxNxM/micrOSPackages)
9. micrOS Gateway server with Prometheus&Grafana: [link](https://github.com/BxNxM/micrOS/#micros-gateway-in-docker)
10. Release notes: [release-note](https://github.com/BxNxM/micrOS/#release-note)

----------------------------------------
----------------------------------------

## micrOS Client Application

[![AppStore](./media/store/AppStoreBadge.svg)](https://apps.apple.com/hu/app/micros-client/id1562342296) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; [![AppStore](./media/store/GooglePlayBadge.png)](https://play.google.com/store/apps/details?id=com.BMT.micrOSClient)

----------------------------------------
----------------------------------------

## Installing micrOS with DevToolKit #ESP32 and more
**macOS / Windows / Linux to install any esp32 board**

[![pypi](./media/pipy.png)](https://pypi.org/project/micrOSDevToolKit/)

End-to-End solution for deployment, update, monitor and develop micrOS boards.

I would suggest to use micrOS GUI as a primary interface for micrOS development kit, but you can use cli as well if you prefer.

> Note: The main purpose of the USB deployment scripts to install micropython on the board and put all micrOS resources from `micrOs/toolkit/workspace/precompiled` to the connected board.

<br/>

## 1. Prerequisites

### 1.1 Install python3.12+

Download Python 3.12+ [link](https://www.python.org/downloads/release/python-3120/)

> Note: **Allow extend system path** with that python version (installation parameter) </br>
> On **Windows**: RUN AS ADMINISTARTOR

Check Python3 version

```bash
python3 --version
```

----------------------------------------

### 2. Install micrOS devToolKit GUI

#### On macOS/Linux

&nbsp;Open **command line** on mac, press: `commnd+space` + type: `terminal` + press: `enter`

##### Download and install **micrOS devToolKit** python package:

```bash
pip3 install --upgrade pip; pip3 install micrOSDevToolKit
```

> Later on you can **update** the package with

```bash
pip3 install --upgrade micrOSDevToolKit
```

----------------------------------------
<br/>

#### On Windows:

##### Download and install **micrOS devToolKit** python package:

Open Windows **PowerShell**, press `windows+R` + type: `powershell` + press `enter`

Copy the following lines to the PowerShell and press enter.

```bash
python -m pip install --upgrade pip
python -m pip install micrOSDevToolKit
```

Later on you can **update** the package with

```bash
python -m pip install --upgrade micrOSDevToolKit
```

----------------------------------------
<br/>

### 3. Start micrOS devToolKit GUI

Copy the following command to the command line and press enter to start.

**```devToolKit.py```**

It will open a graphical user interface for micrOS device management, like usb deploy, update, OTA operations, test executions, etc...

----------------------------------------

![MICROSVISUALIZATION](./media/micrOSToolkit.png?raw=true)

- Example

```
1. Select BOARD TYPE
2. Click on [Deploy (USB)] button -> presss YES
```

It will install your board via USB with default settings. **Continue with micrOS Client app...**

> Note: At the first USB deployment, devToolKit will ask to install **SerialUSB driver** and it will open the driver installer as well, please follow the steps and install the necessary driver.


```
╔╗ ╔╗                  ╔═══╗╔╗ ╔╗╔═╗ ╔╗       ╔═══╗
║║ ║║                  ║╔══╝║║ ║║║║╚╗║║       ╚╗╔╗║
║╚═╝║╔══╗ ╔╗╔╗╔══╗     ║╚══╗║║ ║║║╔╗╚╝║    ╔═╗ ║║║║
║╔═╗║╚ ╗║ ║╚╝║║╔╗║     ║╔══╝║║ ║║║║╚╗║║    ╚═╝ ║║║║
║║ ║║║╚╝╚╗╚╗╔╝║║═╣    ╔╝╚╗  ║╚═╝║║║ ║║║    ╔═╗╔╝╚╝║
╚╝ ╚╝╚═══╝ ╚╝ ╚══╝    ╚══╝  ╚═══╝╚╝ ╚═╝    ╚═╝╚═══╝
```

----------------------------------------

## micrOS Projects


[![RingLamp](./media/projects/RingLamp.gif?raw=true)](https://youtu.be/BlQzAnFtpLk)

![RoboArm](./media/projects/RoboArm.gif?raw=true)

![RGB_CCT](./media/projects/RGB_CCT.gif?raw=true)

----------------------------------------
----------------------------------------


## micrOS Video Tutorials

[![YoutubeChannel](./media/YoutubeChannel.png)](https://www.youtube.com/channel/UChRlJw7OYAoKroC-Mi75joA)

----------------------------------------
<br/>

## micrOS System, message-function visualization

![MICROSVISUALIZATION](./media/micrOS.gif?raw=true)

>Note: micrOS development kit contains command line interface for socket communication. Example: `devToolKit.py --connect`

----------------------------------------

## micrOS Framework Features💡

![MICROSARCHITECTURE](./media/micrOSArchitecture.png?raw=true)

- 🕯**micrOS loader** - starts micrOS or WEBREPL(update / recovery modes)
	- **OTA update** - push update over wifi (webrepl automation: monitor update and auto restart node)
- 📄**Config handling** - user config - **node_config.json**
    - ⏳**Boot phase** - preload Load Module(s) - based on node_config
        - Parameter: `boothook` Device initialization (optional), load applications (pinout and last state initialization)
        	- It runs **as soon as possible** in the boot sequence (before network setup) 
        - Example values: `rgb load; neopixel load`
        - Comments `#` can be used: `#rgb load; neopixel load`, excellect for experimentation.
    - 📡**Network handling** - based on node_config 
        - Parameter: `nwmd` network modes: `STA` Station OR `AP` AccessPoint
        - In STA mode: NTP + UTC aka clock setup
          - API: [ip-api.com](http://ip-api.com/json/?fields=lat,lon,timezone,offset)
        - Static IP configuration, `devip`
        - dhcp hostname setup, `devfid`.local
        - system `uptime` measurement
    - ⚙️**Scheduling / External events** - Interrupt callback - based on node_config 
        - Time based
            - ⌛️simple LM task pool execution on `Timer(0)`
                - To enable the feature set `timirq` to `True`
                - Set period in milliseconds with `timirqseq` like: `5000`
                - Configure callbalcks with `timirqcbf`
                		- Example: `bme280 measure`, so this will measure with the sensor every 5 seconds.
                - Comments `#` can be used in `timirqcbf`
            - 🗓cron [time stump!LM task] pool execution `Timer(1)`
                - To enable this feature set `cron` to `True`
                - Configure callbalcks with `crontasks `
                - timestamp: `WD:H:M:S!LM FUNC`, ranges: `0-6:0-23:0-59:0-59!LM FUNC`
                    - example: `*:8:0:0!rgb rgb r=10 g=60 b=100; etc.`, it will set rgb color on analog rgb periphery at 8am every day.
                    - `WD: 0...6` 0=Monday, 6=Sunday
                        - optional **range handling**: 0-2 means Monday to Wednesday
                - tag: `sunset` / `sunrise`
                    - example: `sunset!rgb rgb r=10 g=60 b=100; etc.`, it will set rgb color on analog rgb periphery at every sunset, every day.
                    - optional minute offset (+/-): sunrise+30
                - Comments cannot be used in `crontasks`! No multiple commands in this mode!

                - API: [api.sunrise-sunset.org](https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date=today&formatted=0)
        - 💣Event based
            - Set trigger event `irqX`
                - Trigger up/down/both `irqX_trig`
                - With LM callback function `irqX_cbf`
                - Comments `#` can be used in `irqX_cbf`
            - `X` can be = 1, 2, 3 or 4


- ⚙️**[L]oad [M]odule** aka **application** execution
	- Lot of built-in functions (table below)
	- Create your own module with 3 easy steps
		- Create a python file, naming convention: `LM_<your_app_name>.py`
			- Replace `<your_app_name>` for anything you prefer!
		- Write python functions, you can call any function from that module...
		- Upload modul with "drag&Drop" devToolKit GUI `devToolKit.py`

- 📨**ShellCli** - wireless communication interface with the nodes
	- **System commands**: `help, version, reboot, modules, webrepl, webrepl --update, etc.`
		- After `webrepl --update` command the micrOS system reboots and waits for ota update in webrepl mode about 20 seconds.
	- **Config handling** SET/GET/DUMP - **node_config.json**
		- enter configuration mode: `conf`
		- Print out all parameters and values: `dump`
		- exit configuration mode:`noconf`
	- **LM** - Load Module function execution (application modules)
		- Example: `system info`
		- That points to `/modules/LM_system.py` file `info()` function and calls it.
- 🖇**microIO** pinout handling - lookuptables for each board
	- Predefined pinout modules for esp32, tinyPico, etc. (files under: `modules/IO_*.py`)
	- Create your pinout based on `IO_esp32.py`, naming convencion: `IO_<name>.py`
	- To activate your custom pinout set `cstmpmap` config parameter to `<name>`
	- HINT: to get pin number you can get it by pin label, like: `system pinamp`
	- HINT: with `cstmpmap` you can overwrite pin mapping as well, like: `neop:25` set neop virtual pin to pin 25 real pinout. 

- 🔄 **Task manager** aka **Async LM jobs**
	- Capable of execute [L]oad [M]odules in the background 
	- Invoke with single execution `&` or for loop execution `&&`
	- Example:
		- In loop: `system heartbeat &&`
			- Loop frequency conrol: `system heartbeat &&1000`, it will execute every sec 
		- Single call: `system heartbeat &`
			- Delayed execution (ms): `system heartbeat &1000`, waits 1 sec before execution.
	- Stop task: `task kill system.heartbeat`
	- Show task live ouput: `task show system.heartbeat`
	- List tasks with `task list`:
	
```
TinyDevBoard $ task list
---- micrOS  top ----
#queue: 18 #load: 3%

#Active   #taskID
Yes       server
Yes       idle
Yes       telegram.server_bot
Yes       espnow.server
```


⌘ DevToolKit CLI feature:

- Socket client python plugin - interactive - non interactive mode

```bash
./devToolKit.py --search --connect
```


----------------------

### Boards and suggestions

There are multiple types of MCU-s (esp32, esp32s3, etc.) available to order, **BUT** to be able to enable **more features** (~2 Load Modules) and **full capable WebUI** interface you need to have more then **190-210kb** of ram (basic boards)(ℹ️).

There is a solution ✅, additinal psram: **~2-4-8Mb** boards are available. It used to name as **psram** or **spiram**, even there is a type **octo-psram**, so check it before buy!!! Psram needs to be **supported on micropython** side as well !!!

**Suggestions - 🔮futureproof hardware:**

**`esp32s3`**: Very fast new espressif module that supports psram detection, so you can freely select any module with this MCU with additinal ram, and micros will work with the best performance, typical ram sizes: **2Mb** (more then enough for everage usage), **4-8Mb** (capacble of image and sound processing tasks and load all GPIO-s 🚀)

**`esp32s3-octo`** Same sa normal psram, just uses 8 pins to connect to the MCU, basically faster...

**`tinypico`** excellet hardware, bit pricy, with 4Mb of ram.

**`esp32cam`** it has a custom image and attached 8Mb of ram.

So prefer boards with more psram 2Mb-8Mb, **minumum requirement for the full flatched setup ~400kb** but smallest psram is **2Mb**, in practive:

- max measured 4Mb is 3.2% 128kb - oled_ui and lot of things loaded...
- camera stream can use about 50% of ram, that means about 2Mb of ram usage.

ℹ️ With basic 190-210kb of ram you can use the system with ShellCli with no issue, just webUI dashboard cannot be load due to memory limitations..., **under 140kb of system ram the system not reliable**, so these boards are not supported.

> Note:

**`esp32`** also can be totally fine with ShellCli, WebCli and 1 load module or multiple modules based on module size... just can be limited by the available memory soonor the later ... (WebCli javascript, htmls are quite small but can be few tens of kilobytes, also multiple async tasks in the background can take same, and roughly around 80% of memory usage system can be instable and restarts.) **So if you have a spare one try out micrOS with a range of features :)**

----------------------

## Built in periphery support

`#Sensors / inputes` `#Actuators / outputs`

[![pheriphery-io-preview](./media/pheriphery-io-preview.png)](https://htmlpreview.github.io/?https://github.com/BxNxM/micrOS/blob/master/micrOS/client/sfuncman/sfuncman.html)

[[CLICK] Show micrOS Load Module functions](https://htmlpreview.github.io/?https://github.com/BxNxM/micrOS/blob/master/micrOS/client/sfuncman/sfuncman.html)</br>

----------------------------------------

## Device Pinouts for wiring

### Logical pin association handling

[micrOS/source/microIO.py](./micrOS/source/microIO.py)

LogicalPin lookup tables:

- [tinypico](micrOS/source/modules/IO_tinypico.py)
- [esp32](micrOS/source/modules/IO_esp32.py)
- [esp32s2](micrOS/source/modules/IO_esp32s2.py)
- [esp32s3](micrOS/source/modules/IO_esp32s3.py)
- [raspberryPicoW](micrOS/source/modules/IO_rp2.py) - reset needed after ota update (webrepl limitation)
- `IO_*.py` [etc.](./micrOS/source)

> Note: Good idea to use costant variable for pin map declaration, check the files for more info, These files are also precompiled automatically into byte streams -> `.mpy`

![MicrOStinyPicopinout](./media/NodeMCUPinOutTinyPico.png?raw=true)

GENERAL CONTROLLER CONCEPT: [microPLC](./media/microPLC.png)


![MicrOSESP23pinout](./media/NodeMCUPinOutESP32.png?raw=true)


![MicrOSESP23S2pinout](./media/NodeMCUPinOutESP32S2_mini.png?raw=true)


![PYQT_PinOutESP32pinout](./media/PYQT_PinOutESP32.png?raw=true)

----------------------------------------

## micrOS **node configuration**, parameters with description

These parameters controlls micrOS core functionalities, so you can define an entire system by setting your custom configurations via these values.

### Basic parameters:

|      Config keys    |   Default value and type    | Reboot required |              Description                     |
| :-----------------: | :-------------------------: | :-------------: | ----------------------------------------- |
|   **`devfid`**      |    `node01`  `<str>`        |       No       | Device friendly "unique" ID - (1) defines AccessPoint (AP) network name and (2) in Station (STA) network mode the DHCP device name for IP address resolve also (3) this is the ShellCli prompt.
|   **`staessid`**    |   `your_wifi_name` `<str>`  |       Yes       | Wifi router name to connect (for STA default connection mode). You can list multiple wifi names separated with `;`
|   **`stapwd`**      | `your_wifi_passwd` `<str>`  |       Yes       | Wifi router password (for STA default connection mode). You can list multiple wifi passwords separated with `;` connected in order to `staessid` wifi names.
|   **`appwd`**       |   `ADmin123`  `<str>`       |       Yes       | Device system password.: Used in AP password (access point mode) + webrepl password + micrOS auth
| **`boothook`**      |    `n/a` `<str>`            |      Yes        | Add Load Module execution(s) to the boot sequence. Separator `;`. Examples: `rgb load; cct load` but you can call any load module function here if you want to run it at boot time.
| **`webui`**         |       `False`  `bool`       |      Yes        | Launch http rest server on port 80 (in parallel with micrOS shell on port 9008 aka `socport`). It has 2 endpoints: / aka main page (index.html) and /rest aka rest (json) interface for load module execution. Example: `<devfid>.local` or `<devfid>.local/rest` + optional parameters: `/rgb/toggle`. **Apple shortcuts compatible**
| **`espnow`**         |     `False`  `bool`       |      Yes        | Enable **ESPNow communication protocol**. It starts `espnow.server` task, that can receive espnow messages and execute Load Module commands. It is an extension for **InterCon** feature example: `system heartbeat >>target.local`. 
| | |
| **`cron`**          |     `False`  `<bool>`       |       Yes       | Enable timestamp based Load Module execution aka Cron scheduler (linux terminology), Timer(1) hardware interrupt enabler.
| **`crontasks`**     |     `n/a`  `<str>`          |       No       | Cron scheduler input, task format: `WD:H:M:S!module function` e.g.: `1:8:0:0!system heartbeat`, task separator in case of multiple tasks: `;`. [WD:0-6, H:0-23, M:0-59, S:0-59] in case of each use: `*`. Instead `WD:H:M:S` you can use suntime tags: `sunset`, `sunrise`, optional offset: `sunset+-<minutes>`, `sunrise+-<minutes>`, example: `sunset-30!system heartbeat`. Range of days: WD can be conrete day number or range like: 0-2 means Monday to Wednesday.
| | |
| **`irq1`**          |     `False`  `<bool>`       |      Yes        | External event interrupt enabler - Triggers when desired signal state detected - button press happens / motion detection / etc.
| **`irq1_cbf`**      |     `n/a`  `<str>`          |      Yes        | `irq1` enabled, calls the given Load Modules, e.x.: `module function optional_parameter(s)` when external trigger happens.
| **`irq1_trig`**     |     `n/a`   `<str>`         |      Yes        | Sets trigger mode for external irq, signal phase detection, values `up` (default: `n/a`) or `down` or `both`.
| **`irq2`**          |     `False`  `<bool>`       |      Yes        | External event interrupt enabler - Triggers when desired signal state detected - button press happens / motion detection / etc.
| **`irq2_cbf`**      |     `n/a`  `<str>`          |      Yes        | `irq2` enabled, calls the given Load Modules, e.x.: `module function optional_parameter(s)` when external trigger happens.
| **`irq2_trig`**     |     `n/a`   `<str>`         |      Yes        | Sets trigger mode for external irq, signal phase detection, values `up` (default: `n/a`) or `down` or `both`.
| **`irq3`**          |     `False`  `<bool>`       |      Yes        | External event interrupt enabler - Triggers when desired signal state detected - button press happens / motion detection / etc.
| **`irq3_cbf`**      |     `n/a`  `<str>`          |      Yes        | `irq3` enabled, calls the given Load Modules, e.x.: `module function optional_parameter(s)` when external trigger happens.
| **`irq3_trig`**     |     `n/a`   `<str>`         |      Yes        | Sets trigger mode for external irq, signal phase detection, values `up` (default: `n/a`) or `down` or `both`.
| **`irq4`**          |     `False`  `<bool>`       |      Yes        | External event interrupt enabler - Triggers when desired signal state detected - button press happens / motion detection / etc.
| **`irq4_cbf`**      |     `n/a`  `<str>`          |      Yes        | `irq4` enabled, calls the given Load Modules, e.x.: `module function optional_parameter(s)` when external trigger happens.
| **`irq4_trig`**     |     `n/a`   `<str>`         |      Yes        | Sets trigger mode for external irq, signal phase detection, values `up` (default: `n/a`) or `down` or `both`.
| **`irq_prell_ms`**  |      `300`   `<int>`        |      Yes        | "Prell": contact recurrence (hw property), for fake event filtering... :D Time window to ignore external IRQ events in ms.
| | |
| **`timirq`**        |     `False`  `<bool>`       |       Yes       | Timer(0) interrupt enabler - background "subprocess" like execution, timer based infinite loop for the LoadModule execution.
| **`timirqcbf`**     |      `n/a`   `<str>`        |      Yes        | if `timirq` enabled, calls the given Load Module(s), e.x.: `module function optional_parameter(s)`, task separator: `;`
| **`timirqseq`**     |    `1000`   `<int>`         |      Yes        | Timer interrupt period in ms, default: `3000` ms (for `timirq` infinite loop timer value)

### Advanced parameter options:

|       Config keys   |   Default value and type    | Reboot required |               Description                      |
| :-----------------: | :-------------------------: | :-------------: | ---------------------------------------- |
| **`utc`**           |     `60`   `<int>`          |       Yes       | NTP-RTC - timezone setup (UTC in minute) - it is automatically calibrated in STA mode based on geolocation.
| **`cstmpmap`**      |      `n/a`  `<str>`          |      Yes       | Default (`n/a`), select pinmap automatically based on platform (`IO_<platform>`). Manual control / customization of application pins, syntax: `pin_map_name; pin_name:pin_number; ` etc. [1][optional] `pin_map_name` represented as `IO_<pin_map_name>.py/.mpy` file on device. [2+][optinal] `dht:22` overwrite individual existing load module pin(s). Hint: `<module> pinmap()` to get app pins, example: `neopixel pinmap()`
| **`boostmd`**       |      `True`  `<bool>`       |      Yes        | boost mode - set up cpu frequency low or high 16Mhz-24MHz (depends on the board).
| **`aioqueue`**      |    `3` `<int>`              |       Yes       | System async queue controller (resource limiter).: `#1` Set asyc task queue limit (for soft tasks: `&`). Furthermore `#2` Socker server-s (webCli, ShellCli) client number limiter. 3 means: 3 cooperative connection (queue) shared by webCli and shellCli. It can be increased based on available resources.
| | |
| **`devip`**         |      `n/a`  `<str>`         |    Yes(N/A)      | Device IP address, (first stored IP in STA mode will be the device static IP on the network), you can set specific static IP address here.
| **`nwmd`**          |     `n/a`  `<str>`          |      Yes        | Prefered network mode - `AP` or `STA`, default is `STA`.
| **`soctout`**       |   `30`      `<int>`         |      Yes        | Socket server connection timeout. If user is passive for `soctout` sec, and new connection incoming, then close passive connection. So it is time limit per connection in the `aioqueue`.
| **`socport`**       |    `9008`  `<int>`          |      Yes        | Socket server service port (should not be changed due to client and API inconpatibility).
| **`auth`**          |     `False` `<bool>`        |       Yes       | Enables socket password authentication, password: `appwd`. Passwordless functions: `hello`, `version`, `exit`. Plus access for loaded modules. Auth protects the configuration and new module loads.
| | |
| **`dbg`**	         |     `True`    `<bool>`      |       Yes       | Debug mode - enable micrOS system printout, server info, etc. + progress LED.
| **`hwuid`**         |      `n/a`  `<str>`         |      N/A        | USED BY SYSTEM (state storage) - hardware address - dev uid
| **`guimeta`**       |      `n/a`  `str`           |      No         | USED BY micrOS Client (state storage) - stores - offloaded parameter type in config. Clinet widget meta data storage.

> Note: Default empty value: `n/a` in case of string parameter.
> Note: Cron is only available on devices with Timer(**1**): esp32

----------------------------------------
----------------------------------------

# Networking - automatic network modes

![MICROSNWMODES](./media/micrOSNetworking.png?raw=true)

# micrOS Gateway in docker

![MICROSVISUALIZATION](./media/micrOS_gateway.png?raw=true)

With prometheus database.
Check the micrOS Gateway docker [README](./env/docker/README.md) for details.

Resources:

> modify `prometheus.yml` regarding what sensors on which endpoint do you want to scrapre data from.

* [docker-compose](./env/docker/docker-compose.yaml)
* [prometheus config](./env/docker/prometheus.yml)

```bash
cd ./env/docker
docker-compose -p gateway up -d
```

Official [DockerHub](https://hub.docker.com/repository/docker/bxnxm/micros-gateway/general)

# micrOS Customization

[![app_templates](./media/app_templates.png?raw=true)](./APPLICATION_GUIDE.md)

----------------------------------------
----------------------------------------


## FUTURE MAIN RELEASE PLANS

Version **3.0.0-0** `micrOS-Autonomous`

```
    Core:
    - (1) Async SSL/TLS integration (micropython 1.22+ required)                [DONE]
        - urequest module async redesign for rest clients                       [OK]
            - LM_telegram (Notify) + server (listener - chatbot)                [OK]
    - (2) ESP-NOW (peer-to-peer communication) integration into InterCon        [DONE]
       - Multi command same device improvement (session ID handling)            [DONE]
    - (3) New intercon syntax - command level integration:                      [DONE]
    	- rgb toggle >>RingLight.local
    	- similar as (obsolete): intercon sendcmd host="RingLight.local" cmd="rgb toggle"
    	- espnow integration into `rgb toggle >>RingLight.local` syntax (when available on target)
    - (4) Create multi level project structure (curret is flat fs)              [DONE]
		- New micrOS FS structure:
			- Automatic dir creation at bootup: '/logs', '/web', '/data', '/config', '/modules'
			- Automatic sub-dir handling /source and /precompiled
			- Automatic dir creation over USB
			
			System Core File Structure:
			- [DONE] root fs (stays untouched (approx.: 24)): /
				- micrOS.py (core)
				- Config.py (core)
				- Tasks.py (core)
				- Shell.py (core)
				- Web.py (core)
				- Server.py (core)
				- etc... (core)
			- [DONE] web folder: /web
				- *.html
				- *.js
				- *.css
				- etc.
			- [DONE][RUNTIME] data folder: /data
			   - Dynamic/Runtime (approx.: 0-8):
				   - *.pds (LM app cache - persistent data storage)
					- *.dat (Common datalogger output)
				- Or store any application data here
			- [DONE][RUNTIME] logs folder: /logs
				- *.log
				- *.sys.log
			- [DONE] config folder /config
             - node_config.json (core config)
             - *.key files (offloaded core config values, like: guimeta)
          - [DONE] module folder /modules - (mip complient: /modules/lib)
				- LM_* (approx.: 54)
				- IO_* (approx.: 5)


		- (5) [DONE] Universal task creation response: `{taskID: verdict}`

		- (6) [DONE] Proper mip installer support (/modules or /lib or /web)
			- Note: Autonomous package management over wifi (github)
				- pacman install             [DONE]
				- pacman uninstall           [DONE]
				- pacman ls                  [DONE]
				- pacman dirtree             [DONE]
				- pacman ...

		- (7) [DONE] /config/requirements.txt handling (native micropython requirements syntax)
			-  pacman download "requirements.txt"

		- (8) [DONE] micrOS/packages - submodule to create individual installable applications for micrOS
			- Application registry (package.json and pacman.json): https://github.com/BxNxM/micrOSPackages 

		- (9) [TODO] micropython uplift to `1.27`
			- [DONE] fix micrOS USB update config restore issue 

			
	RELEASE  `./micrOS/release_info/micrOS_ReleaseInfo`
		- Create release notes (legacy: `release_3.0.0-0_note_esp32.md`)
		- Introduce automatic release metrics generation...
			- `system_analysis_sum.json` and `devices_system_metrics.json` 

```

Version **3.1.0-0** `micrOS-Waterbear`

```
    Core:
    - Low power mode (wake on event, hibernate command)?
    	- Remote controller / Sensor UseCase
```


Version **3.X.0-0** `micrOS-SecurePower`

```
    Core:
    - Async socket servers with SSL/TLS integration (with auth.)
        - ShellCli (with TLS) and InterCon adaptation (default port: 9008, new secure port 9009)
        - WebCli (https) and webUI adaptation
    - Intercon-Wire (?)
    	- Idea of wired message communication protocol same as Intercon-Shell/Intercon-ESPNow
    	- Possible HW protocols: i2c / onewire / uart BUT it should support bidirectional message transfers
    	- Goal: CoProcessor easy integration feature - Arduino env support
    - Application deployment automation: /config/compose.json
    	- enables application deployment:
    		- configuration (node_config.json) handling - safe parameter injection (boothook and irqs)
    		- [done] requirements.txt handling
    	- Automatic behaviour in core system if file exists in STA mode
```

<a id="release-note"></a>
## Release notes

|  VERSION (TAG) |    RELEASE INFO    |  MICROS CORE MEMORY USAGE  |  SUPPORTED DEVICE(S) | APP PROFILES | Load Modules  |     NOTE       |
| :----------: | :----------------: | :------------------------:   |  :-----------------: | :------------: | :------------:| -------------- |
|  **v0.1.0-0** | [release_Info-0.1.0-0](./micrOS/release_info/micrOS_ReleaseInfo/release_0.1.0-0_note.md)| **78,4%** 29 776 byte | esp8266 | [App Profiles](./micrOS/release_info/node_config_profiles/) | [LM manual](./micrOS/client/sfuncman/sfuncman_0.1.0-0.json)| Stable Core with applications - first release
|  **v0.4.0-0** | [release_Info-0.4.0-0](./micrOS/release_info/micrOS_ReleaseInfo/release_0.4.0-0_note_esp8266.md)| **81,0%** 30768 byte | esp8266 | [App Profiles](./micrOS/release_info/node_config_profiles/) | [LM manual](./micrOS/client/sfuncman/sfuncman_0.4.0-0.json)| micrOS multi device support with finalized core and so more. OTA update feature.
|  **v0.4.0-0** | [release_Info-0.4.0-0](./micrOS/release_info/micrOS_ReleaseInfo/release_0.4.0-0_note_esp32.md)| **47,1%** 52 416 byte | esp32 | [App Profiles](./micrOS/release_info/node_config_profiles/) | [LM manual](./micrOS/client/sfuncman/sfuncman_0.4.0-0.json)| *micrOS multi device support with finalized core and advanced task scheduler based on time, and and so more. OTA update feature.*
|  **v1.0.0-0** | [release_Info-1.0.0-0](./micrOS/release_info/micrOS_ReleaseInfo/release_1.0.0-0_note_esp32.md)| **47,9%** 53 280 byte | esp32 | [App Profiles](./micrOS/release_info/node_config_profiles/) | [LM manual](./micrOS/client/sfuncman/sfuncman_1.0.0-0.json)| Release of v1 micrOS, timer and event based irqs, cron task scheduling, realtime communication, multiple device support. OTA, etc.
|  **v1.2.2-0** | [release_Info-1.2.2-0](./micrOS/release_info/micrOS_ReleaseInfo/release_1.2.2-0_note_esp32.md)|  **48,6%** 54 032 byte | esp32 | [App Profiles](./micrOS/release_info/node_config_profiles/) | [LM manual](./micrOS/client/sfuncman/sfuncman_1.2.2-0.json)| Public Release of v1 micrOS, timer and event based irqs, cron task scheduling, realtime communication, multiple device support. OTA update, thread from socket shell (beta) etc.
|  **v light-1.3.0-0** | - |  - | **esp8266** | [lightweight branch](https://github.com/BxNxM/micrOS/tree/lightweight)| - |remove esp8266 due to memory limitation - BUT still supported with limited functionalities on **`lightweight`** branch. Hint: Change branch on github and download zip file, then start micrOSDevToolKit dashboard GUI
|  **v 1.5.0-1** | [release_Info-1.5.0-1](./micrOS/release_info/micrOS_ReleaseInfo/release_1.5.0-1_note_esp32.md) |  **58,2%** 64 704 byte | esp32 (tinyPico) | [App Profiles](./micrOS/release_info/node_config_profiles/) | [LM manual](./micrOS/client/sfuncman/sfuncman_1.5.0-1.json) | Advanced Timer IRQ based scheduling (cron & timirq), Geolocation based timing features, External IRQs with 4 channel (event filtering), finalized light controls, Device-Device comminucation support, etc.
|  **v 1.21.0-4** | [release_Info-1.21.0-4](./micrOS/release_info/micrOS_ReleaseInfo/release_1.21.0-4_note_esp32.md) |  **57.3%** 63 728 byte | esp32 (tinyPico, esp32s2, esp32s3) | [App Profiles](./micrOS/release_info/node_config_profiles/) | [LM manual](./micrOS/client/sfuncman/sfuncman_1.21.0-4.json) | Full async core system with advanced task management and device to device communication, task scheduling and much more ... with more then 30 application/pheriphery support.
|  **v 2.0.0-0** | [release_Info-2.0.0-0](./micrOS/release_info/micrOS_ReleaseInfo/release_2.0.0-0_note_esp32.md) |  **45.4%** 68.7 kb | esp32 (tinyPico, esp32s2, esp32s3) | [App Profiles](./micrOS/release_info/node_config_profiles/) | [LM manual](./micrOS/client/sfuncman/sfuncman_2.0.0-0.json) | Optimizations, WebCli with web frontends, Camera support. Micropython 1.21 async maxed out :D
|  **v 2.6.0-0** | [release_Info-2.6.0-0](./micrOS/release_info/micrOS_ReleaseInfo/release_2.6.0-0_note_esp32.md) |  **48.3%** 72.6 kb  | esp32 (tinyPico, esp32s2, esp32s3) | [App Profiles](./micrOS/release_info/node_config_profiles/) | [LM manual](./micrOS/client/sfuncman/sfuncman_2.6.0-0.json) | WebCli http server enhancements. New webapps: dashboard. Core system official interface finalization towards Load Modules: Common.py, Types.py (frontend generation), microIO.py (pinout handling).

----------------------------------------
----------------------------------------


## Developer Quick guide

Note:

> Secure Core (OTA static modules) (GUI): `boot.py`, `micrOSloader.mpy`, `Network.mpy`, `ConfigHandler.mpy`, `Debug.mpy`


#### Erase device & Deploy micropython & Install micrOS 

Go to micrOS repo, where the `devToolKit.py` located.

```bash
devToolKit.py --make
```
> Note: Follow the steps :)


Search and Connect to the device

```
devToolKit.py -s -c
```

----------------------------------------

**User commands**

```
devToolKit.py -h

optional arguments:
  -h, --help            show this help message and exit

Base commands:
  -m, --make            Erase & Deploy & Precompile (micrOS) & Install (micrOS)
  -r, --update          Update/redeploy connected (usb) micrOS. - node config will be restored
  -s, --search_devices  Search devices on connected wifi network.
  -o, --OTA             OTA (OverTheArir update with webrepl)
  -c, --connect         Connect via socketclinet
  -p CONNECT_PARAMETERS, --connect_parameters CONNECT_PARAMETERS
                        Parameters for connection in non-interactivve mode.
  -a APPLICATIONS, --applications APPLICATIONS
                        List/Execute frontend applications. [list]
  -stat, --node_status  Show all available micrOS devices status data.
  -cl, --clean          Clean user connection data: device_conn_cache.json
```

**Search devices**

```
devToolKit.py --search_devices

or

devToolKit.py -s
```

**List discovered devices with status updates**

```
devToolKit.py -stat

or

devToolKit.py --node_status
```

Output:

```
       [ UID ]                [ FUID ]		[ IP ]		[ STATUS ]	[ VERSION ]	[COMM SEC]
__localhost__                 __simulator__     127.0.0.1	OFFLINE		<n/a>		n/a
micr<ID>OS            TinyDevBoard      10.0.1.72	ONLINE		1.16.2-2		0.072
micr<ID>OS            LivingKitchen     10.0.1.200	ONLINE		1.16.2-2		0.076
micr<ID>OS            RoboArm           10.0.1.232	ONLINE		1.15.4-0		0.072
micr<ID>S            Cabinet           10.0.1.204	ONLINE		1.16.2-2		0.074
micr<ID>4OS            TestBird          10.0.1.179	ONLINE		1.16.2-1		0.083
micr<ID>OS            RingLamp          10.0.1.75	ONLINE		1.16.2-2		0.099
micr<ID>OS            CatFeeder         10.0.1.111	OFFLINE		<n/a>		n/a
micr<ID>OS            ImpiGamePro       10.0.1.23	OFFLINE		<n/a>		n/a
micr<ID>S            micrOSPublic02    10.0.1.47	ONLINE		1.16.2-2		0.101
micr<ID>cOS            micrOSPublic01    10.0.1.197	ONLINE		1.16.2-2		0.099
micr<ID>cOS            experipurple      10.0.1.94	OFFLINE		<n/a>		n/a
```

**Other Developer commands**

```
Development & Deployment & Connection:
  -f, --force_update    Force mode for -r/--update and -o/--OTA
  -e, --erase           Erase device
  -d, --deploy          Deploy micropython
  -i, --install         Install micrOS on micropython
  -l, --list_devs_n_bins
                        List connected devices & micropython binaries.
  -ls, --node_ls        List micrOS node filesystem content.
  -u, --connect_via_usb
                        Connect via serial port - usb
  -b, --backup_node_config
                        Backup usb connected node config.
  -sim, --simulate      start micrOS on your computer in simulated mode
  -cc, --cross_compile_micros
                        Cross Compile micrOS system [py -> mpy]
  -gw, --gateway        Start micrOS Gateway rest-api server
  -v, --version         Get micrOS version - repo + connected device.
```

## Socket terminal example - non interactive

### Identify device

```
devToolKit.py -c -p '--dev slim01 hello'
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/device_conn_cache.json
Activate MicrOS device connection address
[i]         FUID        IP               UID
[0] Device: slim01 - 10.0.1.73 - 0x500x20x910x680xc0xf7
Device was found: slim01
hello:slim01:0x500x20x910x680xc0xf7
```

### Get help

```bash
devToolKit.py -c -p '--dev BedLamp help'

[MICROS]   - built-in shell commands
   hello   - hello msg - for device identification
   version - returns micrOS version
   exit    - exit from shell socket prompt
   reboot  - system soft reboot (vm), hard reboot (hw): reboot -h
   webrepl - start webrepl, for file transfers use with --update
[CONF] Configure mode - built-in shell commands
  conf       - Enter conf mode
    dump       - Dump all data
    key        - Get value
    key value  - Set value
  noconf     - Exit conf mode
[TASK] postfix: &x - one-time,  &&x - periodic, x: wait ms [x min: 20ms]
  task list         - list tasks with <tag>s
  task kill <tag>   - stop task
  task show <tag>   - show task output
[EXEC] Command mode (LMs):
   help lm  - list ALL LoadModules
   cct
      help
   co2
      help
   dht22
        help
   robustness
             help
   system
         help
```
 
### Embedded config handler
 
```  
devToolKit.py -c -p '--dev BedLamp conf <a> dump'
  
  staessid  :        <your-wifi-passwd>
  devip     :        10.0.1.204
  version   :        1.11.0-1
  devfid    :        BedLamp
  cron      :        True
  cronseq   :        3000
  soctout   :        10
  irq2_cbf  :        n/a
  stapwd    :        <your-wifi-name>
  dbg       :        False
  irq2      :        False
  irq1      :        False
  irq1_cbf  :        n/a
  appwd     :        ADmin123
  irq2_trig :        n/a
  hwuid     :        micr7c9ebd623ff8OS
  crontasks :        sunset!cct toggle True;*:0:30:0!cct toggle False;*:5:0:0!cct toggle False
  timirq    :        True
  irq3      :        False
  irq3_cbf  :        n/a
  irq4      :        False
  irq4_cbf  :        n/a
  irq4_trig :        n/a
  nwmd      :        STA
  timirqcbf :        system ha_sta
  irq_prell_ms:      300
  boothook  :        cct load
  aioqueue  :        3
  auth      :        False
  timirqseq :        60000
  utc       :        60
  boostmd   :        True
  socport   :        9008
  irq3_trig :        n/a
  irq1_trig :        n/a
  guimeta   :        ...
  cstmpmap  :        n/a
```

### Load Modules - User defined functions

```
devToolKit.py -c -p '--dev BedLamp system info'

CPU clock: 24 [MHz]
Mem usage: 71.0 %
FS usage: 14.6 %
upython: v1.19.1 on 2022-06-18
board: ESP32 module with ESP32
mac: 7c:9e:bd:62:3f:f8
uptime: 0 1:29:19
```

## SocketClient

### Config:

micrOS/toolkit/user_data/device_conn_cache.json

```json
{
    "__devuid__": [
        "192.168.4.1",
        9008,
        "__device_on_AP__"
    ],
    "__localhost__": [
        "127.0.0.1",
        9008,
        "__simulator__"
    ],
    "micr500291863428OS": [
        "10.0.1.72",
        9008,
        "BedLamp"
    ]
}
```

#### Interactive mode

```
devToolKit.py -c 
or
devToolKit.py -connect

[i]         FUID        IP               UID
[0] Device: __device_on_AP__ - 192.168.4.1 - __devuid__
[1] Device: __simulator__ - 127.0.0.1 - __localhost__
[2] Device: BedLamp - 10.0.1.72 - micr500291863428OS

Choose a device index: 5
Device was selected: ['10.0.1.204', 9008, 'Cabinet']
BedLamp $ help
[MICROS]   - built-in shell commands
   hello   - hello msg - for device identification
   version - returns micrOS version
   exit    - exit from shell socket prompt
   reboot  - system soft reboot (vm), hard reboot (hw): reboot -h
   webrepl - start webrepl, for file transfers use with --update
[CONF] Configure mode - built-in shell commands
  conf       - Enter conf mode
    dump       - Dump all data
    key        - Get value
    key value  - Set value
  noconf     - Exit conf mode
[TASK] postfix: &x - one-time,  &&x - periodic, x: wait ms [x min: 20ms]
  task list         - list tasks with <tag>s
  task kill <tag>   - stop task
  task show <tag>   - show task output
[EXEC] Command mode (LMs):
   help lm  - list ALL LoadModules
   cct
      help
   co2
      help
   dht22
        help
   robustness
             help
   system
         help
BedLamp $  exit
Bye!

```

## Project structure

```
./micrOS/source
├── Common.py
├── Config.py
├── Debug.py
├── Espnow.py
├── Files.py
├── Hooks.py
├── InterConnect.py
├── Interrupts.py
├── Logger.py
├── Network.py
├── Notify.py
├── Scheduler.py
├── Server.py
├── Shell.py
├── Tasks.py
├── Time.py
├── Types.py
├── Web.py
├── main.py
├── micrOS.py
├── micrOSloader.py
├── reset.py
├── urequests.py
├── microIO.py
├── config
│   └── _git.keep
├── modules
│   ├── IO_esp32.py
│   ├── IO_esp32c3.py
│   ├── IO_esp32c6.py
│   ├── IO_esp32s2.py
│   ├── IO_esp32s3.py
│   ├── IO_m5stamp.py
│   ├── IO_qtpy.py
│   ├── IO_rp2.py
│   ├── IO_s3matrix.py
│   ├── IO_tinypico.py
│   ├── LM_L298N.py
│   ├── LM_L9110_DCmotor.py
│   ├── LM_OV2640.py
│   ├── LM_VL53L0X.py
│   ├── LM_aht10.py
│   ├── LM_bme280.py
│   ├── LM_buzzer.py
│   ├── LM_cct.py
│   ├── LM_cluster.py
│   ├── LM_co2.py
│   ├── LM_dashboard_be.py
│   ├── LM_dht11.py
│   ├── LM_dht22.py
│   ├── LM_dimmer.py
│   ├── LM_distance.py
│   ├── LM_ds18.py
│   ├── LM_esp32.py
│   ├── LM_espnow.py
│   ├── LM_gameOfLife.py
│   ├── LM_genIO.py
│   ├── LM_haptic.py
│   ├── LM_i2c.py
│   ├── LM_i2s_mic.py
│   ├── LM_keychain.py
│   ├── LM_ld2410.py
│   ├── LM_light_sensor.py
│   ├── LM_mqtt_client.py
│   ├── LM_neoeffects.py
│   ├── LM_neomatrix.py
│   ├── LM_neopixel.py
│   ├── LM_oled.py
│   ├── LM_oled_sh1106.py
│   ├── LM_oled_ui.py
│   ├── LM_oledui.py
│   ├── LM_pacman.py
│   ├── LM_presence.py
│   ├── LM_qmi8658.py
│   ├── LM_rencoder.py
│   ├── LM_rest.py
│   ├── LM_rgb.py
│   ├── LM_rgbcct.py
│   ├── LM_roboarm.py
│   ├── LM_robustness.py
│   ├── LM_rp2w.py
│   ├── LM_sdcard.py
│   ├── LM_servo.py
│   ├── LM_sound_event.py
│   ├── LM_stepper.py
│   ├── LM_switch.py
│   ├── LM_system.py
│   ├── LM_tcs3472.py
│   ├── LM_telegram.py
│   ├── LM_tinyrgb.py
│   ├── LM_trackball.py
│   └── LM_veml7700.py
└── web
    ├── dashboard.html
    ├── index.html
    ├── matrix_draw.html
    ├── uapi.js
    ├── udashboard.js
    ├── ustyle.css
    ├── uwidgets.js
    └── uwidgets_pro.js

4 directories, 98 files
```


----------------------------------------

## HINTS

- Save **screen** console buffer (**output**)
Press `ctrl + A :` and type `hardcopy -h <filename>`

- Create callgraph: [pycallgraph](http://pycallgraph.slowchop.com/en/master/)

- Convert PNG/JPG-s to GIF: `convert -delay 60 ./*.png mygif.gif`

- **micrOS core and Load Module source code info**:

```bash
devToolKit.py -lint
OR
devToolKit.py --linter
```

### micrOS gateway - Linux service template

> [BETA] service setup tool: `toolkit/helper_scripts/linux_service/make.bash`

- Prerequisite: install micrOS devtoolkit **PiP package**

- Create service: [micrOS gateway service](https://domoticproject.com/creating-raspberry-pi-service/)

- [1] create `micros-gw.service` file:

```bash
[Unit]
Description=micrOS gateway REST API service
After=network-online.target

[Service]
Environment="API_AUTH=<usr_name>:<password>"  <-- replace
ExecStart=/usr/bin/python3 -m devToolKit -gw  <-- check (depends on deployment) OR /bin/bash
WorkingDirectory=/home/gateway                <-- replace
StandardOutput=inherit
StandardError=inherit
Restart=always
User=<user>                                   <-- replace

[Install]
WantedBy=multi-user.target
```

- [2] copy service to `sudo cp micros-gw.service /lib/systemd/system/`

- [3] start service: `sudo systemctl start micros-gw.service`

- [4] enable service at bootup: `sudo systemctl enable micros-gw.service`

- [5] show service state: `sudo systemctl status micros-gw.service`


### GIT

- Add git tag: `git tag -a vX.Y.Z-K -m "tag message"`

- Publish tags: `git push origin --tags`

- Pretty git view: `git log --pretty=oneline`

- File change list: `git diff --name-only fbb4875609a3c0ee088b6a118ebf9f8a500be0fd HEAD | grep 'mpy-MicrOS'`

- GitHub embed youtube link: `https://github.com/itskeshav/Add-youtube-link-in-Readme.md`

- Git history visualization with Gource

```bash
gource \
    --highlight-users \
    --hide filenames \
    --file-idle-time 0 \
    --max-files 0 \
    --seconds-per-day 0.01 \
    --auto-skip-seconds 1 \
    --title "micrOS Evolution" \
    --output-ppm-stream - \
    | ffmpeg -y -r 30 -f image2pipe -vcodec ppm -i - -vcodec libx264 -preset ultrafast -pix_fmt yuv420p -crf 1 -threads 0 -bf 0 output.mp4
```

git push -u origin master

