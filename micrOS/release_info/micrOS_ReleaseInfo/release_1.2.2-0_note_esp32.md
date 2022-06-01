# Release validation

measurement error of baseload: 9344 byte, 14%

### VERSION: 1.2.2-0

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
| 1.2.2-0   |  **10,6%** 6736 byte |    esp32    | [default_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/default_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)
[CONFIGHANDLER] inject config:
{'gmttime': 2, 'irqmreq': 6000, 'pled': True, 'crontasks': 'n/a', 'soctout': 100, 'devip': '192.168.1.84', 'version': '1
.2.2-0', 'auth': False, 'cronseq': 3000, 'guimeta': '...', 'cron': False, 'timirqcbf': 'n/a', 'devfid': 'node01', 'cstmp
map': 'n/a', 'boostmd': True, 'socport': 9008, 'dbg': True, 'irqmembuf': 1000, 'timirqseq': 3000, 'extirq': False, 'stae
ssid': 'your_wifi', 'appwd': 'ADmin123', 'stapwd': 'your_password', 'timirq': False, 'hwuid': 'micr3c61052fa788OS', 'extirqc
bf': 'n/a', 'nwmd': 'STA', 'extirqtrig': 'n/a', 'boothook': 'n/a'}
[CONFIGHANDLER] Inject default conf struct successful
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 47296, free: 63872
 No. of 1-blocks: 645, 2-blocks: 128, max blk sz: 41, max free sz: 3992
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOTHOOK] EXECUTION ...
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 47840, free: 63328
 No. of 1-blocks: 667, 2-blocks: 130, max blk sz: 41, max free sz: 3958
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EXTIRQ SETUP - EXTIRQ: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
~~~~~ [PROFILING INFO] - [3] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 48464, free: 62704
 No. of 1-blocks: 691, 2-blocks: 132, max blk sz: 41, max free sz: 3919
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI STA NW your_wifi
        | - [NW: STA] ESSID WAS FOUND: your_wifi
        | [NW: STA] CONNECT TO NETWORK your_wifi
        | [NW: STA] Waiting for connection... 40 sec
        | [NW: STA] Waiting for connection... 39 sec
        | [NW: STA] Waiting for connection... 38 sec
[NW: STA] Set device static IP.
[NW: STA][SKIP] StaticIP conf.: 192.168.1.84 ? 192.168.1.84
        |       | [NW: STA] network config: ('192.168.1.84', '255.255.255.0', '192.168.1.1', '192.168.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2021, 9, 7, 22, 9, 56, 1, 250)
~~~~~ [PROFILING INFO] - [4] AFTER NETWORK CONFIGURATION ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 52496, free: 58672
 No. of 1-blocks: 850, 2-blocks: 146, max blk sz: 41, max free sz: 3667
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [5] AFTER SOCKET SERVER CREATION ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 53168, free: 58000
 No. of 1-blocks: 871, 2-blocks: 147, max blk sz: 41, max free sz: 3625
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] TIMIRQ SETUP: False SEQ: 3000
|- [IRQ] TIMIRQ CBF:n/a
[IRQ] CRON IRQ SETUP: None SEQ: 3000
|- [IRQ] CRON CBF:n/a
~~~~~ [PROFILING INFO] - [6] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 54032, free: 57136
 No. of 1-blocks: 907, 2-blocks: 151, max blk sz: 41, max free sz: 3571
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] SERVER ADDR: telnet 192.168.1.84 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection
```

### CORE LOAD WITH INPTERRUPTS

+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: False
+ Config: heartbeat_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    | 
| :------:  | :-------------------: | :---------: | :-----------: |
| 1.2.2-0   |   **23.1%** 14496 byte |   esp32     |     [heartbeat_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/heartbeat_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)
[CONFIGHANDLER] inject config:
{'gmttime': 2, 'irqmreq': 6000, 'pled': True, 'crontasks': 'n/a', 'soctout': 100, 'devip': '192.168.1.84', 'version': '1
.2.2-0', 'auth': False, 'cronseq': 3000, 'guimeta': '...', 'cron': False, 'timirqcbf': 'system heartbeat', 'devfid': 'no
de01', 'cstmpmap': 'n/a', 'boostmd': True, 'socport': 9008, 'dbg': True, 'irqmembuf': 1000, 'timirqseq': 3000, 'extirq':
 False, 'staessid': 'your_wifi', 'appwd': 'ADmin123', 'stapwd': 'your_password', 'timirq': True, 'hwuid': 'micr3c61052fa788O
S', 'extirqcbf': 'n/a', 'nwmd': 'STA', 'extirqtrig': 'n/a', 'boothook': 'system heartbeat'}
[CONFIGHANDLER] Inject default conf struct successful
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 48576, free: 62592
 No. of 1-blocks: 651, 2-blocks: 130, max blk sz: 63, max free sz: 3912
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOTHOOK] EXECUTION ...
|-[BOOTHOOK] TASKS: system heartbeat
|-[BOOTHOOK] DONE
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 56688, free: 54480
 No. of 1-blocks: 814, 2-blocks: 160, max blk sz: 81, max free sz: 3405
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EXTIRQ SETUP - EXTIRQ: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
~~~~~ [PROFILING INFO] - [3] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 57312, free: 53856
 No. of 1-blocks: 838, 2-blocks: 162, max blk sz: 81, max free sz: 3366
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI STA NW your_wifi
        | - [NW: STA] ESSID WAS FOUND: your_wifi
        | [NW: STA] CONNECT TO NETWORK your_wifi
        | [NW: STA] Waiting for connection... 40 sec
        | [NW: STA] Waiting for connection... 39 sec
        | [NW: STA] Waiting for connection... 38 sec
[NW: STA] Set device static IP.
[NW: STA][SKIP] StaticIP conf.: 192.168.1.84 ? 192.168.1.84
        |       | [NW: STA] network config: ('192.168.1.84', '255.255.255.0', '192.168.1.1', '192.168.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2021, 9, 7, 22, 24, 43, 1, 250)
~~~~~ [PROFILING INFO] - [4] AFTER NETWORK CONFIGURATION ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 61376, free: 49792
 No. of 1-blocks: 997, 2-blocks: 175, max blk sz: 81, max free sz: 3112
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [5] AFTER SOCKET SERVER CREATION ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 62048, free: 49120
 No. of 1-blocks: 1018, 2-blocks: 176, max blk sz: 81, max free sz: 3070
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] TIMIRQ SETUP: True SEQ: 3000
|- [IRQ] TIMIRQ CBF:system heartbeat
[IRQ] CRON IRQ SETUP: None SEQ: 3000
|- [IRQ] CRON CBF:n/a
~~~~~ [PROFILING INFO] - [6] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 63072, free: 48096
 No. of 1-blocks: 1058, 2-blocks: 180, max blk sz: 81, max free sz: 3006
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] SERVER ADDR: telnet 192.168.1.84 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection
```


### RESPONSE COMMUNICATION TEST WITH APPLICATION 


+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: True
+ Config: neopixel_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    | 
| :------:  | :-------------------: | :---------: | :-----------: |
| 1.2.2-0   | **25,3%** 15904 byte |    esp32    |     [neopixel_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/neopixel_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)
[CONFIGHANDLER] inject config:
{'gmttime': 2, 'irqmreq': 6000, 'pled': True, 'crontasks': 'n/a', 'soctout': 100, 'devip': '', 'version': 'n/a', 'auth':
 False, 'cronseq': 3000, 'guimeta': '...', 'cron': False, 'timirqcbf': 'system heartbeat', 'devfid': 'node01', 'cstmpmap
': 'n/a', 'boostmd': True, 'socport': 9008, 'dbg': True, 'irqmembuf': 1000, 'timirqseq': 2000, 'extirq': True, 'staessid
': 'your_wifi', 'appwd': 'ADmin123', 'stapwd': 'your_password', 'timirq': False, 'hwuid': 'n/a', 'extirqcbf': 'neopixel togg
le', 'nwmd': 'n/a', 'extirqtrig': 'n/a', 'boothook': 'neopixel neopixel_cache_load_n_init'}
[CONFIGHANDLER] Inject default conf struct successful
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 48512, free: 62656
 No. of 1-blocks: 648, 2-blocks: 128, max blk sz: 63, max free sz: 3916
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOTHOOK] EXECUTION ...
|-[BOOTHOOK] TASKS: neopixel load_n_init
|-[BOOTHOOK] DONE
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 56816, free: 54352
 No. of 1-blocks: 787, 2-blocks: 160, max blk sz: 81, max free sz: 3396
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EXTIRQ SETUP - EXTIRQ: True TRIG: n/a
|- [IRQ] EXTIRQ CBF: neopixel toggle
[IRQ] - event setup: n/a
~~~~~ [PROFILING INFO] - [3] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 57808, free: 53360
 No. of 1-blocks: 828, 2-blocks: 163, max blk sz: 81, max free sz: 3335
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI STA NW your_wifi
        | - [NW: STA] ESSID WAS FOUND: your_wifi
        | [NW: STA] CONNECT TO NETWORK your_wifi
        | [NW: STA] Waiting for connection... 40 sec
        | [NW: STA] Waiting for connection... 39 sec
        | [NW: STA] Waiting for connection... 38 sec
        | [NW: STA] Waiting for connection... 37 sec
        | [NW: STA] Waiting for connection... 36 sec
[NW: STA] Set device static IP.
[NW: STA] IP was not stored:
        |       | [NW: STA] network config: ('192.168.1.84', '255.255.255.0', '192.168.1.1', '192.168.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2021, 9, 7, 22, 35, 27, 1, 250)
~~~~~ [PROFILING INFO] - [4] AFTER NETWORK CONFIGURATION ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 62816, free: 48352
 No. of 1-blocks: 986, 2-blocks: 181, max blk sz: 81, max free sz: 3022
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [5] AFTER SOCKET SERVER CREATION ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 63488, free: 47680
 No. of 1-blocks: 1007, 2-blocks: 182, max blk sz: 81, max free sz: 2980
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] TIMIRQ SETUP: False SEQ: 2000
|- [IRQ] TIMIRQ CBF:system heartbeat
[IRQ] CRON IRQ SETUP: None SEQ: 3000
|- [IRQ] CRON CBF:n/a
~~~~~ [PROFILING INFO] - [6] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 1488 out of 15360
GC: total: 111168, used: 64416, free: 46752
 No. of 1-blocks: 1044, 2-blocks: 186, max blk sz: 81, max free sz: 2922
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] SERVER ADDR: telnet 192.168.1.84 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection
```

#### COMMUNICATION TEST LOG - under load

> NOTE: under load measurement doesn't indicate any memory degradation under high load.

Server log snippet

```
|-[ socket server ] wait to accept a connection
|--[ socket server ] Connected with 192.168.1.149:59323
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 70784
|----[ socket server ] RAW INPUT |neopixel neopixel 122 15 92|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 67936
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('192.168.1.149', 59323)
|-[ socket server ] wait to accept a connection
|--[ socket server ] Connected with 192.168.1.149:59324
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 70864
|----[ socket server ] RAW INPUT |neopixel neopixel 160 17 114|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 68016
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('192.168.1.149', 59324)
|-[ socket server ] wait to accept a connection
|--[ socket server ] Connected with 192.168.1.149:59325
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 70784
|----[ socket server ] RAW INPUT |neopixel neopixel 234 207 211|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 67920
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('192.168.1.149', 59325)
|-[ socket server ] wait to accept a connection
```

Test log

```
R: 160, G: 17 B: 114
CMD: ['--dev', 'node01', 'neopixel', 'neopixel 160 17 114']
Load micrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: node01
NEOPIXEL SET TO R160G17B114
- [ OK ] |NEOPIXEL SET TO R160G17B114|
Progress: 0 err / 63 / [64]
===========================
R: 234, G: 207 B: 211
CMD: ['--dev', 'node01', 'neopixel', 'neopixel 234 207 211']
Load micrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: node01
NEOPIXEL SET TO R234G207B211
- [ OK ] |NEOPIXEL SET TO R234G207B211|
Progress: 0 err / 64 / [64]
[i] Communication stability test with Lamp parameter configurations.
ERR: 0 / ALL 64 100% success rate.
```
