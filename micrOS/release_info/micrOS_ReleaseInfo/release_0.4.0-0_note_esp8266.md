# Release validation

measurement error of baseload: ~1230 byte, ~10%%

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
| 0.4.0-0   | **~25,9%** 2512 byte  |   esp8266   |     [default_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/default_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] inject config:
{'soctout': 100, 'socport': 9008, 'devip': '10.0.1.157', 'timirqseq': 3000, 'irqmembuf': 1000, 'cron': False, 'boothook'
: 'n/a', 'stapwd': 'your-wifi-password', 'extirq': False, 'devfid': 'fred', 'hwuid': '0x500x20x910x680xc0xf7', 'crontasks': 'n/a'
, 'dbg': True, 'staessid': '<your-wifi-name>', 'extirqcbf': 'n/a', 'gmttime': 2, 'boostmd': True, 'appwd': 'ADmi
n123', 'timirq': False, 'version': '0.4.0-0', 'nwmd': 'STA', 'timirqcbf': 'n/a', 'pled': True}
[CONFIGHANDLER] Inject default data struct successful
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 28256, free: 9696
 No. of 1-blocks: 342, 2-blocks: 76, max blk sz: 41, max free sz: 606
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 25616, free: 12336
 No. of 1-blocks: 286, 2-blocks: 71, max blk sz: 41, max free sz: 603
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: <your-wifi-name>
        | [NW: STA] ALREADY CONNECTED TO <your-wifi-name>
NTP setup errer.:[Errno 110] ETIMEDOUT
NTP setup DONE: (2020, 11, 14, 20, 22, 14, 5, 319)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 28320, free: 9632
 No. of 1-blocks: 374, 2-blocks: 82, max blk sz: 41, max free sz: 599
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 29024, free: 8928
 No. of 1-blocks: 398, 2-blocks: 84, max blk sz: 41, max free sz: 558
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
[IRQ] TIMIRQ SETUP - TIMIRQ: False SEQ: 3000
|- [IRQ] CRON:False CBF:n/a
|- [IRQ] SIMPLE CBF:n/a
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 30224, free: 7728
 No. of 1-blocks: 333, 2-blocks: 82, max blk sz: 41, max free sz: 399
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 30768, free: 7184
 No. of 1-blocks: 354, 2-blocks: 83, max blk sz: 41, max free sz: 399
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
|-[ socket server ] SERVER ADDR: telnet 10.0.1.157 9008
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
| 0.4.0-0   | **~52,8%**  5072 byte |   esp8266     |     [heartbeat_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/heartbeat_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] inject config:
{'soctout': 100, 'socport': 9008, 'devip': '10.0.1.157', 'timirqseq': 3000, 'irqmembuf': 1000, 'cron': False, 'boothook'
: 'system heartbeat', 'stapwd': '<your-wifi-password>', 'extirq': False, 'devfid': 'fred2', 'hwuid': '0x500x20x910x680xc0xf7', 'cro
ntasks': 'n/a', 'dbg': True, 'staessid': '<your-wifi-name>', 'extirqcbf': 'n/a', 'gmttime': 1, 'boostmd': True,
'appwd': 'ADmin123', 'timirq': True, 'version': '0.4.0-0', 'nwmd': 'STA', 'timirqcbf': 'system heartbeat', 'pled': True}
[CONFIGHANDLER] Inject default data struct successful
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 28352, free: 9600
 No. of 1-blocks: 344, 2-blocks: 78, max blk sz: 41, max free sz: 600
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
|-[BOOT HOOKS] SHELL EXEC: system heartbeat
|-[BOOT HOOKS] state: True
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 29696, free: 8256
 No. of 1-blocks: 409, 2-blocks: 86, max blk sz: 41, max free sz: 516
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: <your-wifi-name>
        | [NW: STA] ALREADY CONNECTED TO <your-wifi-name>
NTP setup errer.:[Errno 110] ETIMEDOUT
NTP setup DONE: (2020, 11, 14, 20, 4, 46, 5, 319)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 29616, free: 8336
 No. of 1-blocks: 379, 2-blocks: 89, max blk sz: 41, max free sz: 509
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 30320, free: 7632
 No. of 1-blocks: 403, 2-blocks: 91, max blk sz: 41, max free sz: 477
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
[IRQ] TIMIRQ SETUP - TIMIRQ: True SEQ: 3000
|- [IRQ] CRON:False CBF:n/a
|- [IRQ] SIMPLE CBF:system heartbeat
|-- TIMER IRQ MODE: SIMPLE
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 32880, free: 5072
 No. of 1-blocks: 356, 2-blocks: 90, max blk sz: 63, max free sz: 218
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 33424, free: 4528
 No. of 1-blocks: 377, 2-blocks: 91, max blk sz: 63, max free sz: 218
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
|-[ socket server ] SERVER ADDR: telnet 10.0.1.157 9008
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
| 0.4.0-0   | **~67,9%**  8336 byte |    esp8266    |     [neopixel_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/neopixel_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] inject config:
{'soctout': 100, 'socport': 9008, 'devip': '10.0.1.157', 'timirqseq': 2000, 'irqmembuf': 1000, 'cron': False, 'boothook': 'neopixel neopixel_cache_load_n_init', 'stapwd': '<your-wifi-password>', 'extirq': True, 'devfid': 'fred3', 'hwuid': '0x500x20x910x680xc0xf7', 'crontasks': 'n/a', 'dbg': True, 'staessid': '<your-wifi-name>', 'extirqcbf': 'neopixel toggle', 'gmttime': 1, 'boostmd': True, 'appwd': 'ADmin123', 'timirq': False, 'version': '0.4.0-0', 'nwmd': 'STA', 'timirqcbf': 'system heartbeat', 'pled': True}
[CONFIGHANDLER] Inject default data struct successful
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 25680, free: 12272
 No. of 1-blocks: 282, 2-blocks: 71, max blk sz: 41, max free sz: 601
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
|-[BOOT HOOKS] SHELL EXEC: neopixel neopixel_cache_load_n_init
|-[BOOT HOOKS] state: True
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 27616, free: 10336
 No. of 1-blocks: 305, 2-blocks: 84, max blk sz: 41, max free sz: 453
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: <your-wifi-name>
        | [NW: STA] ALREADY CONNECTED TO <your-wifi-name>
NTP setup DONE: (2020, 11, 14, 20, 13, 17, 5, 319)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 29808, free: 8144
 No. of 1-blocks: 381, 2-blocks: 93, max blk sz: 41, max free sz: 453
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 30512, free: 7440
 No. of 1-blocks: 405, 2-blocks: 95, max blk sz: 41, max free sz: 453
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
[IRQ] TIMIRQ SETUP - TIMIRQ: False SEQ: 2000
|- [IRQ] CRON:False CBF:n/a
|- [IRQ] SIMPLE CBF:system heartbeat
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 33248, free: 4704
 No. of 1-blocks: 353, 2-blocks: 94, max blk sz: 63, max free sz: 159
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ ENABLED PIN: 12 CBF: neopixel toggle
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 2896 out of 8192
GC: total: 37952, used: 34016, free: 3936
 No. of 1-blocks: 380, 2-blocks: 95, max blk sz: 63, max free sz: 159
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
|-[ socket server ] SERVER ADDR: telnet 10.0.1.157 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection - blocking call...
```

#### COMMUNICATION TEST LOG - under load

|  version  |       memory usage    | board type  |              communication           | 
| :------:  | :-------------------: | :---------: | :----------------------------------: |
| 0.4.0-0   | **~73,1%**  8976 byte |   esp8266     |     100% success rate. in 64 call    |

> NOTE: under load measurement shows ~640byte traffic load memory usage

Server log snippet

```
|--[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 3248
|---[ socket server ] RAW INPUT |neopixel neopixel(78, 65, 255)|
|----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 752
|-----[ socket server ] RAW INPUT |exit|
|------[ socket server ] exit and close connection from ('10.0.1.61', 64542)
|[ socket server ] wait to accept a connection - blocking call...
|-[ socket server ] Connected with 10.0.1.61:64543
|--[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 3296
|---[ socket server ] RAW INPUT |neopixel neopixel(226, 173, 54)|
|----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 800
|-----[ socket server ] RAW INPUT |exit|
|------[ socket server ] exit and close connection from ('10.0.1.61', 64543)
|[ socket server ] wait to accept a connection - blocking call...
```

Test log

```
Device was found: Lamp
PORT INFORMATION COMES FROM: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/node_config.json, but not exists!
	[HINT] Run /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/ConfigHandler.py script to generate default MicrOS config.
NEOPIXEL SET TO R164G17B230
- [ OK ] |NEOPIXEL SET TO R164G17B230|
Progress: 0 err / 62 / [64]
===========================
R: 62, G: 10 B: 153
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(62, 10, 153)']
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
PORT INFORMATION COMES FROM: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/node_config.json, but not exists!
	[HINT] Run /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/ConfigHandler.py script to generate default MicrOS config.
NEOPIXEL SET TO R62G10B153
- [ OK ] |NEOPIXEL SET TO R62G10B153|
Progress: 0 err / 63 / [64]
===========================
R: 99, G: 177 B: 178
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(99, 177, 178)']
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
PORT INFORMATION COMES FROM: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/node_config.json, but not exists!
	[HINT] Run /Users/bnm/Documents/NodeMcu/MicrOs/tools/../MicrOS/ConfigHandler.py script to generate default MicrOS config.
NEOPIXEL SET TO R99G177B178
- [ OK ] |NEOPIXEL SET TO R99G177B178|
Progress: 0 err / 64 / [64]
[i] Communication stability test with Lamp parameter configurations.
ERR: 0 / ALL 64 100% success rate.
```
