# Release validation
### VERSION: 1.0.0-0

|  version  |       memory usage    | board type  |     config    |
| :------:  | :-------------------: | :---------: | :-----------: |
| 1.0.0-0   | **47,9%** 53 280 byte  |    esp32    |   `default`   |


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

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)
[CONFIGHANDLER] inject config:
{'gmttime': 2, 'irqmreq': 6000, 'pled': True, 'crontasks': 'n/a', 'soctout': 100, 'devip': '10.0.1.140', 'version': '1.0
.0-0', 'auth': False, 'cronseq': 3000, 'guimeta': '...', 'cron': False, 'timirqcbf': 'n/a', 'devfid': 'node01', 'cstmpma
p': 'n/a', 'boostmd': True, 'socport': 9008, 'dbg': True, 'irqmembuf': 1000, 'timirqseq': 3000, 'extirq': False, 'staess
id': '<your-wifi-name>', 'appwd': 'ADmin123', 'stapwd': '<your-wifi-passwd>', 'timirq': False, 'hwuid': 'micr240ac4592470
OS', 'extirqcbf': 'n/a', 'nwmd': 'STA', 'extirqtrig': 'n/a', 'boothook': 'n/a'}
[CONFIGHANDLER] Inject default conf struct successful
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 42976, free: 68192
 No. of 1-blocks: 569, 2-blocks: 111, max blk sz: 41, max free sz: 4262
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION ...
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 43520, free: 67648
 No. of 1-blocks: 591, 2-blocks: 113, max blk sz: 41, max free sz: 4228
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI STA NW <your-wifi-name>
I (3467) phy: phy_version: 4180, cb3948e, Sep 12 2019, 16:39:13, 0, 0
        | - [NW: STA] ESSID WAS FOUND: <your-wifi-name>
        | [NW: STA] CONNECT TO NETWORK <your-wifi-name>
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
[NW: STA][SKIP] StaticIP conf.: 10.0.1.140 ? 10.0.1.140
        |       | [NW: STA] network config: ('10.0.1.140', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2021, 3, 16, 20, 13, 31, 1, 75)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 51136, free: 60032
 No. of 1-blocks: 858, 2-blocks: 142, max blk sz: 41, max free sz: 3752
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 51856, free: 59312
 No. of 1-blocks: 880, 2-blocks: 144, max blk sz: 41, max free sz: 3707
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] TIMIRQ SETUP: False SEQ: 3000
|- [IRQ] TIMIRQ CBF:n/a
[IRQ] CRON IRQ SETUP: None SEQ: 3000
|- [IRQ] CRON CBF:n/a
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 52672, free: 58496
 No. of 1-blocks: 913, 2-blocks: 148, max blk sz: 41, max free sz: 3656
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EXTIRQ SETUP - EXTIRQ: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 53280, free: 57888
 No. of 1-blocks: 936, 2-blocks: 150, max blk sz: 41, max free sz: 3618
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] SERVER ADDR: telnet 10.0.1.140 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|  inital   |  **38,6%** 42 976 byte |  111 168 byte   |   `[memUsage] MAIN LOAD`    |
|  running  |  **47,9%** 53 280 byte |  111 168 byte   |   `[memUsage] SYSTEM IS UP` |

Config: [default_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/default_profile-node_config.json)

### CORE LOAD WITH INPTERRUPTS

+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: False
+ Config: heartbeat_profile-node_config.json

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)
[CONFIGHANDLER] inject config:
{'gmttime': 2, 'irqmreq': 6000, 'pled': True, 'crontasks': 'n/a', 'soctout': 100, 'devip': '10.0.1.140', 'version': '1.0
.0-0', 'auth': False, 'cronseq': 3000, 'guimeta': '...', 'cron': False, 'timirqcbf': 'system heartbeat', 'devfid': 'node
01', 'cstmpmap': 'n/a', 'boostmd': True, 'socport': 9008, 'dbg': True, 'irqmembuf': 1000, 'timirqseq': 3000, 'extirq': F
alse, 'staessid': '<your-wifi-name>', 'appwd': 'ADmin123', 'stapwd': '<your-wifi-password>', 'timirq': True, 'hwuid': 'micr
240ac4592470OS', 'extirqcbf': 'n/a', 'nwmd': 'STA', 'extirqtrig': 'n/a', 'boothook': 'system heartbeat'}
[CONFIGHANDLER] Inject default conf struct successful
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 44288, free: 66880
 No. of 1-blocks: 575, 2-blocks: 113, max blk sz: 63, max free sz: 4179
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION ...
|-[BOOT HOOKS] TASKS: system heartbeat
|-[BOOT HOOKS] DONE
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 50432, free: 60736
 No. of 1-blocks: 728, 2-blocks: 137, max blk sz: 63, max free sz: 3793
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI STA NW <your-wifi-name>
I (3991) phy: phy_version: 4180, cb3948e, Sep 12 2019, 16:39:13, 0, 0
        | - [NW: STA] ESSID WAS FOUND: <your-wifi-name>
        | [NW: STA] CONNECT TO NETWORK <your-wifi-name>
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
[NW: STA][SKIP] StaticIP conf.: 10.0.1.140 ? 10.0.1.140
        |       | [NW: STA] network config: ('10.0.1.140', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2021, 3, 16, 20, 32, 56, 1, 75)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 58048, free: 53120
 No. of 1-blocks: 995, 2-blocks: 166, max blk sz: 63, max free sz: 3320
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 58768, free: 52400
 No. of 1-blocks: 1017, 2-blocks: 168, max blk sz: 63, max free sz: 3275
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] TIMIRQ SETUP: True SEQ: 3000
|- [IRQ] TIMIRQ CBF:system heartbeat
[IRQ] CRON IRQ SETUP: None SEQ: 3000
|- [IRQ] CRON CBF:n/a
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 59728, free: 51440
 No. of 1-blocks: 1053, 2-blocks: 172, max blk sz: 63, max free sz: 3215
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EXTIRQ SETUP - EXTIRQ: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 60336, free: 50832
 No. of 1-blocks: 1076, 2-blocks: 174, max blk sz: 63, max free sz: 3177
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] SERVER ADDR: telnet 10.0.1.140 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|  inital   |  **39,8** 44288 byte |  111 168 byte   |   `[memUsage] MAIN LOAD`    |
|  running  |  **54,2%** 60336 byte |  111 168 byte   |   `[memUsage] SYSTEM IS UP` |

Config: [heartbeat_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/heartbeat_profile-node_config.json)


### RESPONSE COMMUNICATION TEST WITH APPLICATION 


+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: True
+ Config: neopixel_profile-node_config.json

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)
[CONFIGHANDLER] inject config:
{'gmttime': 2, 'irqmreq': 6000, 'pled': True, 'crontasks': 'n/a', 'soctout': 100, 'devip': '10.0.1.140', 'version': '1.0
.0-0', 'auth': False, 'cronseq': 3000, 'guimeta': '...', 'cron': False, 'timirqcbf': 'system heartbeat', 'devfid': 'node
01', 'cstmpmap': 'n/a', 'boostmd': True, 'socport': 9008, 'dbg': True, 'irqmembuf': 1000, 'timirqseq': 2000, 'extirq': T
rue, 'staessid': '<your-wifi-name>', 'appwd': 'ADmin123', 'stapwd': '<your-wifi-password>', 'timirq': False, 'hwuid': 'micr
240ac4592470OS', 'extirqcbf': 'neopixel toggle', 'nwmd': 'STA', 'extirqtrig': 'n/a', 'boothook': 'neopixel neopixel_cach
e_load_n_init'}
[CONFIGHANDLER] Inject default conf struct successful
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 44400, free: 66768
 No. of 1-blocks: 577, 2-blocks: 112, max blk sz: 63, max free sz: 4172
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION ...
|-[BOOT HOOKS] TASKS: neopixel neopixel_cache_load_n_init
|-[BOOT HOOKS] DONE
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 49248, free: 61920
 No. of 1-blocks: 681, 2-blocks: 136, max blk sz: 63, max free sz: 3869
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI STA NW <your-wifi-name>
I (3707) phy: phy_version: 4180, cb3948e, Sep 12 2019, 16:39:13, 0, 0
        | - [NW: STA] ESSID WAS FOUND: <your-wifi-name>
        | [NW: STA] CONNECT TO NETWORK <your-wifi-name>
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
[NW: STA][SKIP] StaticIP conf.: 10.0.1.140 ? 10.0.1.140
        |       | [NW: STA] network config: ('10.0.1.140', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup errer.:[Errno 110] ETIMEDOUT
NTP setup DONE: (2021, 3, 16, 20, 52, 36, 1, 75)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 57328, free: 53840
 No. of 1-blocks: 958, 2-blocks: 165, max blk sz: 63, max free sz: 3365
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 58048, free: 53120
 No. of 1-blocks: 980, 2-blocks: 167, max blk sz: 63, max free sz: 3320
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] TIMIRQ SETUP: False SEQ: 2000
|- [IRQ] TIMIRQ CBF:system heartbeat
[IRQ] CRON IRQ SETUP: None SEQ: 3000
|- [IRQ] CRON CBF:n/a
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 58928, free: 52240
 No. of 1-blocks: 1014, 2-blocks: 171, max blk sz: 63, max free sz: 3265
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EXTIRQ SETUP - EXTIRQ: True TRIG: n/a
|- [IRQ] EXTIRQ CBF: neopixel toggle
[IRQ] - event setup: n/a
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 59888, free: 51280
 No. of 1-blocks: 1053, 2-blocks: 174, max blk sz: 63, max free sz: 3205
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] SERVER ADDR: telnet 10.0.1.140 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|  inital   |  **39,9%** 44400 byte |  111 168 byte   |   `[memUsage] MAIN LOAD`    |
|  running  |  **53,8%** 59888 byte |  111 168 byte   |   `[memUsage] SYSTEM IS UP` |

Config: [neopixel_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/neopixel_profile-node_config.json)

#### COMMUNICATION TEST LOG - under load

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
R: 179, G: 133 B: 98
CMD: ['--dev', 'nodepro', 'neopixel', 'neopixel 179 133 98']
Load micrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: nodepro
NEOPIXEL SET TO R179G133B98
- [ OK ] |NEOPIXEL SET TO R179G133B98|
Progress: 0 err / 60 / [64]
===========================
R: 126, G: 49 B: 87
CMD: ['--dev', 'nodepro', 'neopixel', 'neopixel 126 49 87']
Load micrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: nodepro
NEOPIXEL SET TO R126G49B87
- [ OK ] |NEOPIXEL SET TO R126G49B87|
Progress: 0 err / 61 / [64]
===========================
R: 154, G: 62 B: 121
CMD: ['--dev', 'nodepro', 'neopixel', 'neopixel 154 62 121']
Load micrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: nodepro
NEOPIXEL SET TO R154G62B121
- [ OK ] |NEOPIXEL SET TO R154G62B121|
Progress: 0 err / 62 / [64]
===========================
R: 21, G: 177 B: 85
CMD: ['--dev', 'nodepro', 'neopixel', 'neopixel 21 177 85']
Load micrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: nodepro
NEOPIXEL SET TO R21G177B85
- [ OK ] |NEOPIXEL SET TO R21G177B85|
Progress: 0 err / 63 / [64]
===========================
R: 230, G: 241 B: 152
CMD: ['--dev', 'nodepro', 'neopixel', 'neopixel 230 241 152']
Load micrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: nodepro
NEOPIXEL SET TO R230G241B152
- [ OK ] |NEOPIXEL SET TO R230G241B152|
Progress: 0 err / 64 / [64]
```

Serial logs

```
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 76592
|----[ socket server ] RAW INPUT |neopixel neopixel 36 240 86|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 73840
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('10.0.1.61', 53762)
|-[ socket server ] wait to accept a connection
|--[ socket server ] Connected with 10.0.1.61:53763
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 76592
|----[ socket server ] RAW INPUT |neopixel neopixel 178 172 176|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 73824
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('10.0.1.61', 53763)
|-[ socket server ] wait to accept a connection
```
