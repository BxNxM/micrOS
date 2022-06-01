# Release validation

measurement error of baseload: ? byte, ?%

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
| 1.5.0-1   |  **?%** ? byte |    esp32    | [default_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/default_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
```

### CORE LOAD WITH INPTERRUPTS

+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: False
+ Config: heartbeat_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    | 
| :------:  | :-------------------: | :---------: | :-----------: |
| 1.5.0-1   |   **?%** ? byte |   esp32     |     [heartbeat_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/heartbeat_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
```


### RESPONSE COMMUNICATION TEST WITH APPLICATION 


+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: True
+ Config: neopixel_profile-node_config.json

#### EVALATION

|  version  |       memory usage    | board type  |     config    | 
| :------:  | :-------------------: | :---------: | :-----------: |
| 1.5.0-1   | **?%** ? byte |    esp32    |     [neopixel_profile](https://github.com/BxNxM/micrOS/tree/master/micrOS/release_info/node_config_profiles/neopixel_profile-node_config.json)      |

#### ATTACHED BOOT (SERIAL) LOG

```
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
