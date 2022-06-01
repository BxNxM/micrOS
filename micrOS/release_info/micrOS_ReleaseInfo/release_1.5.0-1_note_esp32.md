# Release validation

measurement error of baseload: 1168 byte, 1.9%

### VERSION: 1.5.0-1

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
| 1.5.0-1   |  **5,5%** 6176 byte |    esp32    | [default_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/default_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)
[CONFIGHANDLER] Inject user config ...
[CONFIGHANDLER] Save conf struct successful
[PIN MAP] esp32
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
~~~~~ [PROFILING INFO] - [memUsage] MAIN LOAD ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 58528, free: 52640
 No. of 1-blocks: 790, 2-blocks: 172, max blk sz: 81, max free sz: 3288
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOTHOOK] EXECUTION ...
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
[IRQ] EXTIRQ SETUP - EXT IRQ1: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ2: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ3: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ4: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[NW: STA] SET WIFI STA NW your-wifi-name
        | - [NW: STA] ESSID WAS FOUND: your-wifi-name
        | [NW: STA] CONNECT TO NETWORK your-wifi-name
        | [NW: STA] Waiting for connection... 60 sec
        | [NW: STA] Waiting for connection... 59 sec
[NW: STA] Set device static IP.
[NW: STA][SKIP] StaticIP conf.: 192.168.1.216 ? 192.168.1.216
        |       | [NW: STA] network config: ('192.168.1.216', '255.255.255.0', '192.168.1.1', '192.168.1.1')
        |       | [NW: STA] CONNECTED: True
Cron: False - SKIP sync
|[ socket server ] <<constructor>>
[IRQ] TIMIRQ SETUP: False SEQ: 3000
|- [IRQ] TIMIRQ CBF:n/a
[IRQ] CRON IRQ SETUP: False SEQ: 3000
|- [IRQ] CRON CBF:n/a
~~~~~ [PROFILING INFO] - [memUsage] SYSTEM IS UP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 64704, free: 46464
 No. of 1-blocks: 1031, 2-blocks: 202, max blk sz: 81, max free sz: 2903
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] SERVER ADDR: telnet 192.168.1.216 9008
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
| 1.5.0-1   |   **13,7%** 15268 byte |   esp32     |     [heartbeat_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/heartbeat_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)
[CONFIGHANDLER] Inject user config ...
[CONFIGHANDLER] Save conf struct successful
[PIN MAP] esp32
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
~~~~~ [PROFILING INFO] - [memUsage] MAIN LOAD ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 59696, free: 51472
 No. of 1-blocks: 793, 2-blocks: 173, max blk sz: 81, max free sz: 3215
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOTHOOK] EXECUTION ...
|-[BOOTHOOK] TASKS: system heartbeat
<3 heartbeat <3
|-[BOOTHOOK] DONE
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
[IRQ] EXTIRQ SETUP - EXT IRQ1: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ2: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ3: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ4: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[NW: STA] SET WIFI STA NW your-wifi-name
        | - [NW: STA] ESSID WAS FOUND: your-wifi-name
        | [NW: STA] CONNECT TO NETWORK your-wifi-name
        | [NW: STA] Waiting for connection... 60 sec
        | [NW: STA] Waiting for connection... 59 sec
        | [NW: STA] Waiting for connection... 58 sec
[NW: STA] Set device static IP.
[NW: STA] IP was not stored: n/a
        |       | [NW: STA] network config: ('192.168.1.216', '255.255.255.0', '192.168.1.1', '192.168.1.1')
        |       | [NW: STA] CONNECTED: True
Cron: False - SKIP sync
|[ socket server ] <<constructor>>
[IRQ] TIMIRQ SETUP: True SEQ: 3000
|- [IRQ] TIMIRQ CBF:system heartbeat
[IRQ] CRON IRQ SETUP: False SEQ: 3000
|- [IRQ] CRON CBF:n/a
~~~~~ [PROFILING INFO] - [memUsage] SYSTEM IS UP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 74960, free: 36208
 No. of 1-blocks: 1204, 2-blocks: 248, max blk sz: 81, max free sz: 2262
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] SERVER ADDR: telnet 192.168.1.216 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection
<3 heartbeat <3
```


### RESPONSE COMMUNICATION TEST WITH APPLICATION 


+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: True
+ Config: neopixel_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    | 
| :------:  | :-------------------: | :---------: | :-----------: |
| 1.5.0-1   | **14,5%** 16192 byte |    esp32    |     [neopixel_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/neopixel_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)
[CONFIGHANDLER] Inject user config ...
[CONFIGHANDLER] Save conf struct successful
[PIN MAP] esp32
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
~~~~~ [PROFILING INFO] - [memUsage] MAIN LOAD ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 58656, free: 52512
 No. of 1-blocks: 794, 2-blocks: 174, max blk sz: 81, max free sz: 3280
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOTHOOK] EXECUTION ...
|-[BOOTHOOK] TASKS: neopixel load_n_init
|-[BOOTHOOK] DONE
[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: True
[IRQ] EXTIRQ SETUP - EXT IRQ1: True TRIG: n/a
|- [IRQ] EXTIRQ CBF: neopixel toggle
[IRQ] EXTIRQ SETUP - EXT IRQ2: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ3: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ4: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[NW: STA] SET WIFI STA NW your-wifi-name
        | - [NW: STA] ESSID WAS FOUND: your-wifi-name
        | [NW: STA] CONNECT TO NETWORK your-wifi-name
        | [NW: STA] Waiting for connection... 60 sec
        | [NW: STA] Waiting for connection... 59 sec
[NW: STA] Set device static IP.
[NW: STA][SKIP] StaticIP conf.: 192.168.1.216 ? 192.168.1.216
        |       | [NW: STA] network config: ('192.168.1.216', '255.255.255.0', '192.168.1.1', '192.168.1.1')
        |       | [NW: STA] CONNECTED: True
Cron: False - SKIP sync
|[ socket server ] <<constructor>>
[IRQ] TIMIRQ SETUP: False SEQ: 2000
|- [IRQ] TIMIRQ CBF:system heartbeat
[IRQ] CRON IRQ SETUP: False SEQ: 3000
|- [IRQ] CRON CBF:n/a
~~~~~ [PROFILING INFO] - [memUsage] SYSTEM IS UP ~~~~~
stack: 1536 out of 15360
GC: total: 111168, used: 74848, free: 36320
 No. of 1-blocks: 1225, 2-blocks: 245, max blk sz: 81, max free sz: 2269
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] SERVER ADDR: telnet 192.168.1.216 9008
|--[ socket server ] Socket bind complete
|---[ socket server ] Socket now listening
|----[ socket server ] wait to accept a connection
```

#### COMMUNICATION TEST LOG - under load

> NOTE: under load measurement doesn't indicate any memory degradation under high load.

Server log snippet

```
|[ socket server ] exit and close connection from ('192.168.1.100', 57135)
|-[ socket server ] wait to accept a connection
|--[ socket server ] Connected with 192.168.1.100:57136
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 60704
|----[ socket server ] RAW INPUT |neopixel neopixel 7 124 234 >json|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 40208
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('192.168.1.100', 57136)
|-[ socket server ] wait to accept a connection
|--[ socket server ] Connected with 192.168.1.100:57137
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 60704
|----[ socket server ] RAW INPUT |neopixel neopixel 55 190 12 >json|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 40128
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('192.168.1.100', 57137)
|-[ socket server ] wait to accept a connection
|--[ socket server ] Connected with 192.168.1.100:57138
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 60704
|----[ socket server ] RAW INPUT |neopixel neopixel 247 64 95 >json|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 40128
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('192.168.1.100', 57138)
|-[ socket server ] wait to accept a connection
|--[ socket server ] Connected with 192.168.1.100:57139
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 40832
|----[ socket server ] RAW INPUT |neopixel neopixel 210 159 102 >json|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 20208
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('192.168.1.100', 57139)
|-[ socket server ] wait to accept a connection
|--[ socket server ] Connected with 192.168.1.100:57140
|---[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 60704
|----[ socket server ] RAW INPUT |neopixel neopixel 208 91 116 >json|
|-----[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: 40128
|------[ socket server ] RAW INPUT |exit|
|[ socket server ] exit and close connection from ('192.168.1.100', 57140)
|-[ socket server ] wait to accept a connection
```

Test log

```
Device was found: node01
{"B": 95, "S": 1, "G": 64, "R": 247}
- [ OK ] |{"B": 95, "S": 1, "G": 64, "R": 247}|
Progress: 0 err / 30 / [32]
===========================
R: 210, G: 159 B: 102
CMD: ['--dev', 'node01', 'neopixel', 'neopixel 210 159 102 >json']
Socket run (raw): ['--dev', 'node01', 'neopixel', 'neopixel 210 159 102 >json']
Load micrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOS/toolkit/user_data/device_conn_cache.json
Device was found: node01
{"B": 102, "S": 1, "G": 159, "R": 210}
- [ OK ] |{"B": 102, "S": 1, "G": 159, "R": 210}|
Progress: 0 err / 31 / [32]
===========================
R: 208, G: 91 B: 116
CMD: ['--dev', 'node01', 'neopixel', 'neopixel 208 91 116 >json']
Socket run (raw): ['--dev', 'node01', 'neopixel', 'neopixel 208 91 116 >json']
Load micrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOS/toolkit/user_data/device_conn_cache.json
Device was found: node01
{"B": 116, "S": 1, "G": 91, "R": 208}
- [ OK ] |{"B": 116, "S": 1, "G": 91, "R": 208}|
Progress: 0 err / 32 / [32]
[i] Communication stability test with Lamp parameter configurations.
ERR: 0 / ALL 32 100% success rate.
```
