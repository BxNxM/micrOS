# Release validation

measurement error of baseload: 256 byte, 0,4%

### VERSION: 0.4.0-0

## Deployment command

```
./devToolKit.py -m -u
```

- SELECT DEVICE TYPE 
- GENERATE DEFAULT NODE_CONFIG.JSON: **NEW**
- FROM TEST PROFILES
  - default_profile-node_config.json (core baseload)
  - heartbeat_profile-node_config.json (core + interrput baseload)
  - lamp_profile-node_config.json (application response)

# Validation & Measurements

### CORE BASELOAD TESTING

+ SocketServer with socketshell: True
+ Interrputs: False
+ Communication testing: False
+ Config: default_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    |
| :------:  | :-------------------: | :---------: | :-----------: |
| 0.4.0-0   | **~22,6%** 17250 byte |   esp32  |     [default_profile](./micrOS/release_info/node_config_profiles/default_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] inject config:
{'soctout': 100, 'socport': 9008, 'devip': '10.0.1.176', 'timirqseq': 3000, 'irqmembuf': 1000, 'cron': False, 'boothook': 'n/a', 'stapwd': '<your-password>', 'ext
irq': False, 'devfid': 'fred', 'hwuid': '0x4c0x110xae0xf70x860x0', 'crontasks': 'n/a', 'dbg': True, 'staessid': '<your-wifi-name>', 'extirqcbf': 'n/
a', 'gmttime': 2, 'boostmd': True, 'appwd': 'ADmin123', 'timirq': False, 'version': '0.4.0-0', 'nwmd': 'STA', 'timirqcbf': 'n/a', 'pled': True}
[CONFIGHANDLER] Inject default data struct successful
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 35168, free: 76000
 No. of 1-blocks: 435, 2-blocks: 90, max blk sz: 41, max free sz: 4750
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 35712, free: 75456
 No. of 1-blocks: 457, 2-blocks: 92, max blk sz: 41, max free sz: 4716
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: <your-wifi-name>
I (2777) phy: phy_version: 4180, cb3948e, Sep 12 2019, 16:39:13, 0, 0
        | [NW: STA] CONNECT TO NETWORK <your-wifi-name>
        | - [NW: STA] ESSID WAS FOUND True
        | [NW: STA] Waiting for connection... 60/60
        | [NW: STA] Waiting for connection... 59/60
        | [NW: STA] Waiting for connection... 58/60
        | [NW: STA] Waiting for connection... 57/60
        | [NW: STA] Waiting for connection... 56/60
        | [NW: STA] Waiting for connection... 55/60
        | [NW: STA] Waiting for connection... 54/60
        | [NW: STA] Waiting for connection... 53/60
        | [NW: STA] Waiting for connection... 52/60
        | [NW: STA] Waiting for connection... 51/60
        | [NW: STA] Waiting for connection... 50/60
        | [NW: STA] Waiting for connection... 49/60
        | [NW: STA] Waiting for connection... 48/60
        | [NW: STA] Waiting for connection... 47/60
        | [NW: STA] Waiting for connection... 46/60
[NW: STA] Set device static IP.
[NW: STA][SKIP] StaticIP conf.: 10.0.1.176 ? 10.0.1.176
        |       | [NW: STA] network config: ('10.0.1.176', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2020, 11, 13, 23, 33, 34, 4, 318)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 44448, free: 66720
 No. of 1-blocks: 766, 2-blocks: 131, max blk sz: 41, max free sz: 4170
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 45152, free: 66016
 No. of 1-blocks: 790, 2-blocks: 133, max blk sz: 41, max free sz: 4126
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
[IRQ] TIMIRQ SETUP - TIMIRQ: False SEQ: 3000
|- [IRQ] CRON:False CBF:n/a
|- [IRQ] SIMPLE CBF:n/a
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 51872, free: 59296
 No. of 1-blocks: 904, 2-blocks: 151, max blk sz: 41, max free sz: 3706
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 52416, free: 58752
 No. of 1-blocks: 925, 2-blocks: 152, max blk sz: 41, max free sz: 3672
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
|-[ socket server ] SERVER ADDR: telnet 10.0.1.176 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection - blocking call...
```

### CORE LOAD WITH INPTERRUPTS

+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: False
+ Config: heartbeat_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    | 
| :------:  | :-------------------: | :---------: | :-----------: |
| 0.4.0-0   | **~27,6%** 20976 byte |   esp32     |     [heartbeat_profile](./micrOS/release_info/node_config_profiles/heartbeat_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] inject config:
{'soctout': 100, 'socport': 9008, 'devip': '10.0.1.176', 'timirqseq': 3000, 'irqmembuf': 1000, 'cron': False, 'boothook': 'system heartbeat', 'stapwd': '<your-wifi-password>', 'extirq': False, 'devfid': 'fred2', 'hwuid': '0x4c0x110xae0xf70x860x0', 'crontasks': 'n/a', 'dbg': True, 'staessid': '<your-wifi-name>', 'e
xtirqcbf': 'n/a', 'gmttime': 1, 'boostmd': True, 'appwd': 'ADmin123', 'timirq': True, 'version': '0.4.0-0', 'nwmd': 'STA', 'timirqcbf': 'system heartbeat',
'pled': True}
[CONFIGHANDLER] Inject default data struct successful
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 35328, free: 75840
 No. of 1-blocks: 437, 2-blocks: 92, max blk sz: 41, max free sz: 4740
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
|-[BOOT HOOKS] SHELL EXEC: system heartbeat
|-[BOOT HOOKS] state: True
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 39744, free: 71424
 No. of 1-blocks: 581, 2-blocks: 107, max blk sz: 41, max free sz: 4464
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: <your-wifi-name>
I (3166) phy: phy_version: 4180, cb3948e, Sep 12 2019, 16:39:13, 0, 0
        | [NW: STA] CONNECT TO NETWORK <your-wifi-name>
        | - [NW: STA] ESSID WAS FOUND True
        | [NW: STA] Waiting for connection... 60/60
        | [NW: STA] Waiting for connection... 59/60
        | [NW: STA] Waiting for connection... 58/60
        | [NW: STA] Waiting for connection... 57/60
        | [NW: STA] Waiting for connection... 56/60
        | [NW: STA] Waiting for connection... 55/60
        | [NW: STA] Waiting for connection... 54/60
        | [NW: STA] Waiting for connection... 53/60
        | [NW: STA] Waiting for connection... 52/60
        | [NW: STA] Waiting for connection... 51/60
        | [NW: STA] Waiting for connection... 50/60
        | [NW: STA] Waiting for connection... 49/60
        | [NW: STA] Waiting for connection... 48/60
        | [NW: STA] Waiting for connection... 47/60
[NW: STA] Set device static IP.
[NW: STA][SKIP] StaticIP conf.: 10.0.1.176 ? 10.0.1.176
        |       | [NW: STA] network config: ('10.0.1.176', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2020, 11, 13, 22, 47, 12, 4, 318)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 46944, free: 64224
 No. of 1-blocks: 832, 2-blocks: 132, max blk sz: 41, max free sz: 4014
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 47648, free: 63520
 No. of 1-blocks: 856, 2-blocks: 134, max blk sz: 41, max free sz: 3970
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
[IRQ] TIMIRQ SETUP - TIMIRQ: True SEQ: 3000
|- [IRQ] CRON:False CBF:n/a
|- [IRQ] SIMPLE CBF:system heartbeat
|-- TIMER IRQ MODE: SIMPLE
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 55760, free: 55408
 No. of 1-blocks: 979, 2-blocks: 153, max blk sz: 63, max free sz: 3463
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 56304, free: 54864
 No. of 1-blocks: 1000, 2-blocks: 154, max blk sz: 63, max free sz: 3429
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
|-[ socket server ] SERVER ADDR: telnet 10.0.1.176 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection - blocking call...
```


### RESPONSE COMMUNICATION TEST WITH APPLICATION 


+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: True
+ Config: neopixel_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    | 
| :------:  | :-------------------: | :---------: | :-----------: |
| 0.4.0-0   | **~29,8%** 22576 byte |    esp32    |     [neopixel_profile](./micrOS/release_info/node_config_profiles/neopixel_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] inject config:
{'soctout': 100, 'socport': 9008, 'devip': '10.0.1.176', 'timirqseq': 2000, 'irqmembuf': 1000, 'cron': False, 'boothook': 'neopixel neopixel_cache_load_n_in
it', 'stapwd': '<your-wifi-password>', 'extirq': True, 'devfid': 'fred3', 'hwuid': '0x4c0x110xae0xf70x860x0', 'crontasks': 'n/a', 'dbg': True, 'staessid': '<your-wifi-name>', 'extirqcbf': 'neopixel toggle', 'gmttime': 1, 'boostmd': True, 'appwd': 'ADmin123', 'timirq': False, 'version': '0.4.0-0', 'nwmd': 'STA', 't
imirqcbf': 'system heartbeat', 'pled': True}
[CONFIGHANDLER] Inject default data struct successful
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 35424, free: 75744
 No. of 1-blocks: 439, 2-blocks: 91, max blk sz: 41, max free sz: 4734
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
|-[BOOT HOOKS] SHELL EXEC: neopixel neopixel_cache_load_n_init
|-[BOOT HOOKS] state: True
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 40912, free: 70256
 No. of 1-blocks: 568, 2-blocks: 122, max blk sz: 41, max free sz: 4391
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: <your-wifi-name>
I (2992) phy: phy_version: 4180, cb3948e, Sep 12 2019, 16:39:13, 0, 0
        | [NW: STA] CONNECT TO NETWORK <your-wifi-name>
        | - [NW: STA] ESSID WAS FOUND True
        | [NW: STA] Waiting for connection... 60/60
        | [NW: STA] Waiting for connection... 59/60
        | [NW: STA] Waiting for connection... 58/60
        | [NW: STA] Waiting for connection... 57/60
        | [NW: STA] Waiting for connection... 56/60
        | [NW: STA] Waiting for connection... 55/60
        | [NW: STA] Waiting for connection... 54/60
        | [NW: STA] Waiting for connection... 53/60
        | [NW: STA] Waiting for connection... 52/60
        | [NW: STA] Waiting for connection... 51/60
        | [NW: STA] Waiting for connection... 50/60
        | [NW: STA] Waiting for connection... 49/60
        | [NW: STA] Waiting for connection... 48/60
        | [NW: STA] Waiting for connection... 47/60
        | [NW: STA] Waiting for connection... 46/60
[NW: STA] Set device static IP.
[NW: STA][SKIP] StaticIP conf.: 10.0.1.176 ? 10.0.1.176
        |       | [NW: STA] network config: ('10.0.1.176', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2020, 11, 13, 22, 59, 17, 4, 318)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 48592, free: 62576
 No. of 1-blocks: 837, 2-blocks: 150, max blk sz: 41, max free sz: 3911
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 49296, free: 61872
 No. of 1-blocks: 861, 2-blocks: 152, max blk sz: 41, max free sz: 3867
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
[IRQ] TIMIRQ SETUP - TIMIRQ: False SEQ: 2000
|- [IRQ] CRON:False CBF:n/a
|- [IRQ] SIMPLE CBF:system heartbeat
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 57232, free: 53936
 No. of 1-blocks: 980, 2-blocks: 170, max blk sz: 63, max free sz: 3371
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ ENABLED PIN: 4 CBF: neopixel toggle
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 58000, free: 53168
 No. of 1-blocks: 1007, 2-blocks: 171, max blk sz: 63, max free sz: 3323
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
|-[ socket server ] SERVER ADDR: telnet 10.0.1.176 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection - blocking call...
```

#### COMMUNICATION TEST LOG - under load

|  version  |       memory usage    | board type  |              communication           | 
| :------:  | :-------------------: | :---------: | :----------------------------------: |
| 0.4.0-0   |  **~29%** 22576 byte   |   esp32     |     99% success rate. in 64 call    |

> NOTE: under load measurement doesn't indicate any memory degradation under high load.

Server log snippet

```
|[ socket server ] wait to accept a connection - blocking call...
|-[ socket server ] Connected with 10.0.1.61:53941
|--[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 76448
|---[ socket server ] RAW INPUT |neopixel neopixel(50, 191, 10)|
|----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 73456
|-----[ socket server ] RAW INPUT |exit|
|------[ socket server ] exit and close connection from ('10.0.1.61', 53941)
|[ socket server ] wait to accept a connection - blocking call...
|-[ socket server ] Connected with 10.0.1.61:53942
|--[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 76448
|---[ socket server ] RAW INPUT |neopixel neopixel(219, 54, 107)|
|----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 73456
|-----[ socket server ] RAW INPUT |exit|
|------[ socket server ] exit and close connection from ('10.0.1.61', 53942)
|[ socket server ] wait to accept a connection - blocking call...
|-[ socket server ] Connected with 10.0.1.61:53943
|--[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 76448
|---[ socket server ] RAW INPUT |neopixel neopixel(121, 195, 247)|
|----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 73408
|-----[ socket server ] RAW INPUT |exit|
|------[ socket server ] exit and close connection from ('10.0.1.61', 53943)
|[ socket server ] wait to accept a connection - blocking call...

```

Test log

```
Device was found: node_pro
PORT INFORMATION COMES FROM: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/node_config.json, but not exists!
	[HINT] Run /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/ConfigHandler.py script to generate default MicrOS config.
NEOPIXEL SET TO R241G233B45
- [ OK ] |NEOPIXEL SET TO R241G233B45|
Progress: 1 err / 126 / [64]
===========================
R: 72, G: 160 B: 6
CMD: ['--dev', 'node_pro', 'neopixel', 'neopixel(72, 160, 6)']
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: node_pro
PORT INFORMATION COMES FROM: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/node_config.json, but not exists!
	[HINT] Run /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/ConfigHandler.py script to generate default MicrOS config.
NEOPIXEL SET TO R72G160B6
- [ OK ] |NEOPIXEL SET TO R72G160B6|
Progress: 1 err / 127 / [64]
===========================
R: 77, G: 132 B: 239
CMD: ['--dev', 'node_pro', 'neopixel', 'neopixel(77, 132, 239)']
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: node_pro
PORT INFORMATION COMES FROM: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/node_config.json, but not exists!
	[HINT] Run /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/ConfigHandler.py script to generate default MicrOS config.
NEOPIXEL SET TO R77G132B239
- [ OK ] |NEOPIXEL SET TO R77G132B239|
Progress: 1 err / 128 / [64]
[i] Communication stability test with Lamp parameter configurations.
ERR: 1 / ALL 128 99% success rate.
```
