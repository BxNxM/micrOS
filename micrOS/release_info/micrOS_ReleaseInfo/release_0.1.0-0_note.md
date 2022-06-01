# Release validation

measurement error of baseload: 144 byte, 1,5%

### VERSION: 0.1.0-0

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
| 0.1.0-0   |   **~13%** 1216 byte  |  esp8266    |     [default_profile](./micrOS/release_info/node_config_profiles/default_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
???o?r??n|?l$$l`b????|{?l?o??n?$`??r?l?$?$`??r?p????l`??r?l???$l`rl??o????b|lb??b|????l$#??n?n?[CONFIGHANDLER] inject config:
{'boostmd': True, 'pled': True, 'staessid': 'wifi-name_2G', 'nwmd': 'STA', 'socport': 9008, 'boothook': 'n/a', 'version': '0.1.0-0', 'soctout'
: 100, 'timirqcbf': 'n/a', 'irqmembuf': 1000, 'devip': '10.0.1.84', 'timirqseq': 3000, 'hwuid': '0xc80x2b0x960x1e0x140x5c', 'timirq': False, 'appwd': 'ADmi
n123', 'extirq': False, 'devfid': 'node007', 'dbg': True, 'stapwd': 'wifi-password', 'extirqcbf': 'n/a', 'gmttime': 2}
[CONFIGHANDLER] Inject default data struct successful
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 28560, free: 9392
 No. of 1-blocks: 299, 2-blocks: 73, max blk sz: 264, max free sz: 587
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
[BOOT HOOKS] Set up CPU 16MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29088, free: 8864
 No. of 1-blocks: 321, 2-blocks: 75, max blk sz: 264, max free sz: 554
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: wifi-name_2G
        | [NW: STA] CONNECT TO NETWORK wifi-name_2G
        | - [NW: STA] ESSID WAS FOUND True
        | [NW: STA] Waiting for connection... 60/60
        | [NW: STA] Waiting for connection... 59/60
        | [NW: STA] Waiting for connection... 58/60
        | [NW: STA] Waiting for connection... 57/60
        | [NW: STA] Waiting for connection... 56/60
        | [NW: STA] Waiting for connection... 55/60
        | [NW: STA] Waiting for connection... 54/60
[NW: STA] Set device static IP.
[NW: STA] StaticIP was already set: 10.0.1.84
        |       | [NW: STA] network config: ('10.0.1.84', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2020, 8, 3, 17, 43, 50, 0, 216)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29808, free: 8144
 No. of 1-blocks: 361, 2-blocks: 78, max blk sz: 264, max free sz: 432
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 30512, free: 7440
 No. of 1-blocks: 385, 2-blocks: 80, max blk sz: 264, max free sz: 432
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
[IRQ] TIMIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29232, free: 8720
 No. of 1-blocks: 291, 2-blocks: 73, max blk sz: 264, max free sz: 393
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29776, free: 8176
 No. of 1-blocks: 312, 2-blocks: 74, max blk sz: 264, max free sz: 393
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
|-[ socket server ] SERVER ADDR: telnet 10.0.1.84 9008
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
| 0.1.0-0   |   **~28%** 2544 byte  |  esp8266    |     [heartbeat_profile](./micrOS/release_info/node_config_profiles/heartbeat_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
????N?s??o|?$lll b???2r?l?o??N?l`??r?l???l`?N?$???$`??r?$???$$`sd??b??cB??b|lc???b|????$lb??o?N?[CONFIGHANDLER] inject config:
{'boostmd': True, 'pled': True, 'staessid': 'wifi-name_2G', 'nwmd': 'STA', 'socport': 9008, 'boothook': 'n/a', 'version': '0.1.0-0', 'soctout'
: 100, 'timirqcbf': 'system heartbeat', 'irqmembuf': 1000, 'devip': '10.0.1.84', 'timirqseq': 3000, 'hwuid': '0xc80x2b0x960x1e0x140x5c', 'timirq': True, 'a
ppwd': 'ADmin123', 'extirq': False, 'devfid': 'node007', 'dbg': True, 'stapwd': 'wifi-password', 'extirqcbf': 'n/a', 'gmttime': 2}
[CONFIGHANDLER] Inject default data struct successful
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 28608, free: 9344
 No. of 1-blocks: 300, 2-blocks: 74, max blk sz: 264, max free sz: 584
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
[BOOT HOOKS] Set up CPU 16MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29136, free: 8816
 No. of 1-blocks: 322, 2-blocks: 76, max blk sz: 264, max free sz: 551
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: wifi-name_2G
        | [NW: STA] CONNECT TO NETWORK wifi-name_2G
        | - [NW: STA] ESSID WAS FOUND True
        | [NW: STA] Waiting for connection... 60/60
[NW: STA] Set device static IP.
[NW: STA] StaticIP was already set: 10.0.1.84
        |       | [NW: STA] network config: ('10.0.1.84', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup errer.:[Errno 110] ETIMEDOUT
NTP setup DONE: (2020, 8, 3, 17, 47, 13, 0, 216)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29600, free: 8352
 No. of 1-blocks: 350, 2-blocks: 81, max blk sz: 264, max free sz: 431
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 30304, free: 7648
 No. of 1-blocks: 374, 2-blocks: 83, max blk sz: 264, max free sz: 431
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
[IRQ] TIMIRQ ENABLED: SEQ: 3000 CBF: system heartbeat
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 30608, free: 7344
 No. of 1-blocks: 299, 2-blocks: 76, max blk sz: 264, max free sz: 386
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 31152, free: 6800
 No. of 1-blocks: 320, 2-blocks: 77, max blk sz: 264, max free sz: 386
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
|-[ socket server ] SERVER ADDR: telnet 10.0.1.84 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection - blocking call...
```


### RESPONSE COMMUNICATION TEST WITH APPLICATION 


+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: True
+ Config: lamp_profile-node_config.json

#### EVALATION

|  version  |   memory usage   | board type  |     config    | 
| :------:  | :--------------: | :---------: | :-----------: |
| 0.1.0-0   |**~38%** 3520 byte|  esp8266    |     [lamp_profile](./micrOS/release_info/node_config_profiles/lamp_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
????N?|??o|?l$ll c????|{??l?o??o?l ??r?l?$?l ??r?l?d?l ??r?l???ll rd??o???b??"|$b???b|????$lc??o?n?[CONFIGHANDLER] inject config:
{'boostmd': True, 'pled': True, 'staessid': 'wifi-name_2G', 'nwmd': 'STA', 'socport': 9008, 'boothook': 'neopixel neopixel(0,0
,0)', 'version': '0.1.0-0', 'soctout': 100, 'timirqcbf': 'system heartbeat', 'irqmembuf': 1000, 'devip': '10.0.1.12', 'timirqseq': 3000,
'hwuid': '0x2c0xf40x320x440xcb0xd6', 'timirq': True, 'appwd': 'ADmin123', 'extirq': True, 'devfid': 'Lamp', 'dbg': True, 'stapwd': 'BNM3,1
415', 'extirqcbf': 'neopixel neopixel_toggle', 'gmttime': 2}
[CONFIGHANDLER] Inject default data struct successful
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 28704, free: 9248
 No. of 1-blocks: 302, 2-blocks: 76, max blk sz: 264, max free sz: 578
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
|-[BOOT HOOKS] SHELL EXEC: neopixel neopixel(0,0,0)
|-[BOOT HOOKS] state: True
[BOOT HOOKS] Set up CPU 16MHz - boostmd: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 30224, free: 7728
 No. of 1-blocks: 325, 2-blocks: 97, max blk sz: 264, max free sz: 354
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: wifi-name_2G
        | [NW: STA] CONNECT TO NETWORK wifi-name_2G
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
        | [NW: STA] Waiting for connection... 45/60
        | [NW: STA] Waiting for connection... 44/60
        | [NW: STA] Waiting for connection... 43/60
        | [NW: STA] Waiting for connection... 42/60
        | [NW: STA] Waiting for connection... 41/60
        | [NW: STA] Waiting for connection... 40/60
        | [NW: STA] Waiting for connection... 39/60
        | [NW: STA] Waiting for connection... 38/60
        | [NW: STA] Waiting for connection... 37/60
        | [NW: STA] Waiting for connection... 36/60
        | [NW: STA] Waiting for connection... 35/60
        | [NW: STA] Waiting for connection... 34/60
        | [NW: STA] Waiting for connection... 33/60
        | [NW: STA] Waiting for connection... 32/60
[NW: STA] Set device static IP.
[NW: STA] StaticIP was already set: 10.0.1.12
        |       | [NW: STA] network config: ('10.0.1.12', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2020, 8, 3, 18, 2, 24, 0, 216)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29488, free: 8464
 No. of 1-blocks: 309, 2-blocks: 90, max blk sz: 264, max free sz: 238
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [4] AFTER SOCKET SERVER CREATION ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 30192, free: 7760
 No. of 1-blocks: 333, 2-blocks: 92, max blk sz: 264, max free sz: 238
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
[IRQ] TIMIRQ ENABLED: SEQ: 3000 CBF: system heartbeat
~~~~~ [PROFILING INFO] - [5] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 31424, free: 6528
 No. of 1-blocks: 296, 2-blocks: 87, max blk sz: 264, max free sz: 271
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ ENABLED PIN: 12 CBF: neopixel neopixel_toggle
~~~~~ [PROFILING INFO] - [6] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 32224, free: 5728
 No. of 1-blocks: 321, 2-blocks: 90, max blk sz: 264, max free sz: 271
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|[ socket server ] <<constructor>>
|-[ socket server ] SERVER ADDR: telnet 10.0.1.12 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection - blocking call...
```

#### COMMUNICATION TEST LOG

|  version  |       memory usage    | board type  |              communication           | 
| :------:  | :-------------------: | :---------: | :----------------------------------: |
| 0.1.0-0   |   **~49%** 4544 byte  |  esp8266    |     100% success rate. in 64 call    |


Server log snippet

```
|[ socket server ] wait to accept a connection - blocking call...
|-[ socket server ] Connected with 10.0.1.61:64900
|--[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 4096
|---[ socket server ] RAW INPUT |neopixel neopixel(93, 72, 31)|
|----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 4896
|-----[ socket server ] RAW INPUT |exit|
|------[ socket server ] exit and close connection from ('10.0.1.61', 64900)
|[ socket server ] wait to accept a connection - blocking call...
|-[ socket server ] Connected with 10.0.1.61:64901
|--[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 4096
|---[ socket server ] RAW INPUT |neopixel neopixel(157, 88, 249)|
|----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 4992
|-----[ socket server ] RAW INPUT |exit|
|------[ socket server ] exit and close connection from ('10.0.1.61', 64901)
|[ socket server ] wait to accept a connection - blocking call...
|-[ socket server ] Connected with 10.0.1.61:64903
|--[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 4704
|---[ socket server ] RAW INPUT |neopixel neopixel(252, 109, 116)|
|----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 2656
|-----[ socket server ] RAW INPUT |exit|
|------[ socket server ] exit and close connection from ('10.0.1.61', 64903)
|[ socket server ] wait to accept a connection - blocking call...
```

Test log

```
[ RUN ] LightTest
[APP] import LightTest_app
[APP] LightTest_app.app()
===========================
R: 75, G: 184 B: 70
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(75, 184, 70)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R75G184B70
- [ OK ] |NEOPIXEL WAS SET R75G184B70|
Progress: 0 err / 1 / [64]
===========================
R: 218, G: 188 B: 121
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(218, 188, 121)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R218G188B121
- [ OK ] |NEOPIXEL WAS SET R218G188B121|
Progress: 0 err / 2 / [64]
===========================
R: 252, G: 168 B: 46
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(252, 168, 46)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R252G168B46
- [ OK ] |NEOPIXEL WAS SET R252G168B46|
Progress: 0 err / 3 / [64]
===========================
R: 73, G: 36 B: 34
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(73, 36, 34)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R73G36B34
- [ OK ] |NEOPIXEL WAS SET R73G36B34|
Progress: 0 err / 4 / [64]
===========================
R: 59, G: 79 B: 115
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(59, 79, 115)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R59G79B115
- [ OK ] |NEOPIXEL WAS SET R59G79B115|
Progress: 0 err / 5 / [64]
===========================
R: 159, G: 195 B: 56
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(159, 195, 56)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R159G195B56
- [ OK ] |NEOPIXEL WAS SET R159G195B56|
Progress: 0 err / 6 / [64]
===========================
R: 107, G: 91 B: 72
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(107, 91, 72)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R107G91B72
- [ OK ] |NEOPIXEL WAS SET R107G91B72|
Progress: 0 err / 7 / [64]
===========================
R: 115, G: 69 B: 138
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(115, 69, 138)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R115G69B138
- [ OK ] |NEOPIXEL WAS SET R115G69B138|
Progress: 0 err / 8 / [64]
===========================
R: 235, G: 155 B: 196
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(235, 155, 196)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R235G155B196
- [ OK ] |NEOPIXEL WAS SET R235G155B196|
Progress: 0 err / 9 / [64]
===========================
R: 86, G: 45 B: 186
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(86, 45, 186)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R86G45B186
- [ OK ] |NEOPIXEL WAS SET R86G45B186|
Progress: 0 err / 10 / [64]
===========================
R: 36, G: 13 B: 130
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(36, 13, 130)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R36G13B130
- [ OK ] |NEOPIXEL WAS SET R36G13B130|
Progress: 0 err / 11 / [64]
===========================
R: 239, G: 22 B: 248
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(239, 22, 248)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R239G22B248
- [ OK ] |NEOPIXEL WAS SET R239G22B248|
Progress: 0 err / 12 / [64]
===========================
R: 127, G: 245 B: 209
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(127, 245, 209)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R127G245B209
- [ OK ] |NEOPIXEL WAS SET R127G245B209|
Progress: 0 err / 13 / [64]
===========================
R: 14, G: 167 B: 157
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(14, 167, 157)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R14G167B157
- [ OK ] |NEOPIXEL WAS SET R14G167B157|
Progress: 0 err / 14 / [64]
===========================
R: 19, G: 191 B: 180
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(19, 191, 180)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R19G191B180
- [ OK ] |NEOPIXEL WAS SET R19G191B180|
Progress: 0 err / 15 / [64]
===========================
R: 180, G: 79 B: 127
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(180, 79, 127)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R180G79B127
- [ OK ] |NEOPIXEL WAS SET R180G79B127|
Progress: 0 err / 16 / [64]
===========================
R: 26, G: 16 B: 118
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(26, 16, 118)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R26G16B118
- [ OK ] |NEOPIXEL WAS SET R26G16B118|
Progress: 0 err / 17 / [64]
===========================
R: 72, G: 255 B: 91
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(72, 255, 91)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R72G255B91
- [ OK ] |NEOPIXEL WAS SET R72G255B91|
Progress: 0 err / 18 / [64]
===========================
R: 99, G: 97 B: 15
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(99, 97, 15)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R99G97B15
- [ OK ] |NEOPIXEL WAS SET R99G97B15|
Progress: 0 err / 19 / [64]
===========================
R: 27, G: 121 B: 3
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(27, 121, 3)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R27G121B3
- [ OK ] |NEOPIXEL WAS SET R27G121B3|
Progress: 0 err / 20 / [64]
===========================
R: 149, G: 31 B: 16
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(149, 31, 16)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R149G31B16
- [ OK ] |NEOPIXEL WAS SET R149G31B16|
Progress: 0 err / 21 / [64]
===========================
R: 154, G: 78 B: 175
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(154, 78, 175)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R154G78B175
- [ OK ] |NEOPIXEL WAS SET R154G78B175|
Progress: 0 err / 22 / [64]
===========================
R: 102, G: 152 B: 110
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(102, 152, 110)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R102G152B110
- [ OK ] |NEOPIXEL WAS SET R102G152B110|
Progress: 0 err / 23 / [64]
===========================
R: 200, G: 215 B: 111
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(200, 215, 111)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R200G215B111
- [ OK ] |NEOPIXEL WAS SET R200G215B111|
Progress: 0 err / 24 / [64]
===========================
R: 27, G: 26 B: 176
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(27, 26, 176)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R27G26B176
- [ OK ] |NEOPIXEL WAS SET R27G26B176|
Progress: 0 err / 25 / [64]
===========================
R: 159, G: 132 B: 138
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(159, 132, 138)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R159G132B138
- [ OK ] |NEOPIXEL WAS SET R159G132B138|
Progress: 0 err / 26 / [64]
===========================
R: 212, G: 199 B: 140
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(212, 199, 140)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R212G199B140
- [ OK ] |NEOPIXEL WAS SET R212G199B140|
Progress: 0 err / 27 / [64]
===========================
R: 92, G: 4 B: 173
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(92, 4, 173)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R92G4B173
- [ OK ] |NEOPIXEL WAS SET R92G4B173|
Progress: 0 err / 28 / [64]
===========================
R: 11, G: 78 B: 165
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(11, 78, 165)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R11G78B165
- [ OK ] |NEOPIXEL WAS SET R11G78B165|
Progress: 0 err / 29 / [64]
===========================
R: 16, G: 220 B: 104
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(16, 220, 104)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R16G220B104
- [ OK ] |NEOPIXEL WAS SET R16G220B104|
Progress: 0 err / 30 / [64]
===========================
R: 204, G: 159 B: 53
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(204, 159, 53)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R204G159B53
- [ OK ] |NEOPIXEL WAS SET R204G159B53|
Progress: 0 err / 31 / [64]
===========================
R: 165, G: 169 B: 76
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(165, 169, 76)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R165G169B76
- [ OK ] |NEOPIXEL WAS SET R165G169B76|
Progress: 0 err / 32 / [64]
===========================
R: 20, G: 145 B: 25
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(20, 145, 25)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R20G145B25
- [ OK ] |NEOPIXEL WAS SET R20G145B25|
Progress: 0 err / 33 / [64]
===========================
R: 107, G: 5 B: 248
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(107, 5, 248)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R107G5B248
- [ OK ] |NEOPIXEL WAS SET R107G5B248|
Progress: 0 err / 34 / [64]
===========================
R: 109, G: 190 B: 174
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(109, 190, 174)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R109G190B174
- [ OK ] |NEOPIXEL WAS SET R109G190B174|
Progress: 0 err / 35 / [64]
===========================
R: 88, G: 17 B: 183
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(88, 17, 183)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R88G17B183
- [ OK ] |NEOPIXEL WAS SET R88G17B183|
Progress: 0 err / 36 / [64]
===========================
R: 71, G: 144 B: 99
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(71, 144, 99)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R71G144B99
- [ OK ] |NEOPIXEL WAS SET R71G144B99|
Progress: 0 err / 37 / [64]
===========================
R: 189, G: 15 B: 27
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(189, 15, 27)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R189G15B27
- [ OK ] |NEOPIXEL WAS SET R189G15B27|
Progress: 0 err / 38 / [64]
===========================
R: 148, G: 160 B: 191
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(148, 160, 191)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R148G160B191
- [ OK ] |NEOPIXEL WAS SET R148G160B191|
Progress: 0 err / 39 / [64]
===========================
R: 180, G: 217 B: 194
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(180, 217, 194)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R180G217B194
- [ OK ] |NEOPIXEL WAS SET R180G217B194|
Progress: 0 err / 40 / [64]
===========================
R: 141, G: 37 B: 190
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(141, 37, 190)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R141G37B190
- [ OK ] |NEOPIXEL WAS SET R141G37B190|
Progress: 0 err / 41 / [64]
===========================
R: 59, G: 245 B: 55
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(59, 245, 55)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R59G245B55
- [ OK ] |NEOPIXEL WAS SET R59G245B55|
Progress: 0 err / 42 / [64]
===========================
R: 97, G: 252 B: 153
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(97, 252, 153)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R97G252B153
- [ OK ] |NEOPIXEL WAS SET R97G252B153|
Progress: 0 err / 43 / [64]
===========================
R: 94, G: 152 B: 59
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(94, 152, 59)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R94G152B59
- [ OK ] |NEOPIXEL WAS SET R94G152B59|
Progress: 0 err / 44 / [64]
===========================
R: 45, G: 182 B: 27
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(45, 182, 27)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R45G182B27
- [ OK ] |NEOPIXEL WAS SET R45G182B27|
Progress: 0 err / 45 / [64]
===========================
R: 43, G: 195 B: 186
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(43, 195, 186)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R43G195B186
- [ OK ] |NEOPIXEL WAS SET R43G195B186|
Progress: 0 err / 46 / [64]
===========================
R: 221, G: 77 B: 224
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(221, 77, 224)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R221G77B224
- [ OK ] |NEOPIXEL WAS SET R221G77B224|
Progress: 0 err / 47 / [64]
===========================
R: 153, G: 199 B: 182
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(153, 199, 182)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R153G199B182
- [ OK ] |NEOPIXEL WAS SET R153G199B182|
Progress: 0 err / 48 / [64]
===========================
R: 168, G: 196 B: 73
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(168, 196, 73)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R168G196B73
- [ OK ] |NEOPIXEL WAS SET R168G196B73|
Progress: 0 err / 49 / [64]
===========================
R: 204, G: 143 B: 123
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(204, 143, 123)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R204G143B123
- [ OK ] |NEOPIXEL WAS SET R204G143B123|
Progress: 0 err / 50 / [64]
===========================
R: 14, G: 24 B: 215
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(14, 24, 215)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R14G24B215
- [ OK ] |NEOPIXEL WAS SET R14G24B215|
Progress: 0 err / 51 / [64]
===========================
R: 122, G: 60 B: 26
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(122, 60, 26)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R122G60B26
- [ OK ] |NEOPIXEL WAS SET R122G60B26|
Progress: 0 err / 52 / [64]
===========================
R: 176, G: 191 B: 97
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(176, 191, 97)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R176G191B97
- [ OK ] |NEOPIXEL WAS SET R176G191B97|
Progress: 0 err / 53 / [64]
===========================
R: 78, G: 68 B: 46
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(78, 68, 46)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R78G68B46
- [ OK ] |NEOPIXEL WAS SET R78G68B46|
Progress: 0 err / 54 / [64]
===========================
R: 222, G: 251 B: 146
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(222, 251, 146)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R222G251B146
- [ OK ] |NEOPIXEL WAS SET R222G251B146|
Progress: 0 err / 55 / [64]
===========================
R: 100, G: 151 B: 130
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(100, 151, 130)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R100G151B130
- [ OK ] |NEOPIXEL WAS SET R100G151B130|
Progress: 0 err / 56 / [64]
===========================
R: 92, G: 172 B: 223
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(92, 172, 223)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R92G172B223
- [ OK ] |NEOPIXEL WAS SET R92G172B223|
Progress: 0 err / 57 / [64]
===========================
R: 221, G: 72 B: 73
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(221, 72, 73)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R221G72B73
- [ OK ] |NEOPIXEL WAS SET R221G72B73|
Progress: 0 err / 58 / [64]
===========================
R: 207, G: 187 B: 5
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(207, 187, 5)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R207G187B5
- [ OK ] |NEOPIXEL WAS SET R207G187B5|
Progress: 0 err / 59 / [64]
===========================
R: 225, G: 188 B: 121
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(225, 188, 121)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R225G188B121
- [ OK ] |NEOPIXEL WAS SET R225G188B121|
Progress: 0 err / 60 / [64]
===========================
R: 181, G: 13 B: 157
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(181, 13, 157)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R181G13B157
- [ OK ] |NEOPIXEL WAS SET R181G13B157|
Progress: 0 err / 61 / [64]
===========================
R: 93, G: 72 B: 31
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(93, 72, 31)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R93G72B31
- [ OK ] |NEOPIXEL WAS SET R93G72B31|
Progress: 0 err / 62 / [64]
===========================
R: 157, G: 88 B: 249
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(157, 88, 249)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R157G88B249
- [ OK ] |NEOPIXEL WAS SET R157G88B249|
Progress: 0 err / 63 / [64]
===========================
R: 252, G: 109 B: 116
CMD: ['--dev', 'Lamp', 'neopixel', 'neopixel(252, 109, 116)']
Load MicrOS device cache: /MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
NEOPIXEL WAS SET R252G109B116
- [ OK ] |NEOPIXEL WAS SET R252G109B116|
Progress: 0 err / 64 / [64]
[i] Communication stability test with Lamp parameter configurations.
ERR: 0 / ALL 64 100% success rate.
```
