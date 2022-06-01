# Release validation

measurement error of baseload: ~n/a byte, ~n/a%%

### VERSION: 1.0.0-0

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
| 0.4.0-0   | **~n/a%** n/a byte  |   esp8266   |     [default_profile](./micrOS/release_info/node_config_profiles/default_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
n/a
```

### CORE LOAD WITH INPTERRUPTS

+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: False
+ Config: heartbeat_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    | 
| :------:  | :-------------------: | :---------: | :-----------: |
| 1.0.0-0   | **~n/a%**  n/a byte |   esp8266     |     [heartbeat_profile](./micrOS/release_info/node_config_profiles/heartbeat_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
n/a
```


### RESPONSE COMMUNICATION TEST WITH APPLICATION 


+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: True
+ Config: neopixel_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    | 
| :------:  | :-------------------: | :---------: | :-----------: |
| 1.0.0-0   | **~n/a%**  n/a byte |    esp8266    |     [neopixel_profile](./micrOS/release_info/node_config_profiles/neopixel_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
n/a
```

#### COMMUNICATION TEST LOG - under load

|  version  |       memory usage    | board type  |              communication           | 
| :------:  | :-------------------: | :---------: | :----------------------------------: |
| 0.4.0-0   | **~n/a%**  n/a byte |   esp8266     |     100% success rate. in 64 call    |

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
