# Relese validation

### VERSION: x.y.z-h

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

|  vesrion  | memory usage  | board type  |     config    | 
| :------:  | :-----------: | :---------: | :-----------: |
| x.y.z-h   |   X% Y byte   |    espXY    |     link      |

#### ATTACHED BOOT (SERIAL) LOG

```
TODO
```

### CORE LOAD WITH INPTERRUPTS

+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: False
+ Config: heartbeat_profile-node_config.json

#### EVALATION

|  vesrion  | memory usage  | board type  |     config    | 
| :------:  | :-----------: | :---------: | :-----------: |
| x.y.z-h   |   X% Y byte   |    espXY    |     link      |

#### ATTACHED BOOT (SERIAL) LOG

```
TODO
```


### RESPONSE COMMUNICATION TEST WITH APPLICATION 


+ SocketServer with socketshell: True
+ Interrputs: True
+ Communication testing: True
+ Config: lamp_profile-node_config.json

#### EVALATION

|  vesrion  | memory usage  | board type  |     config    | 
| :------:  | :-----------: | :---------: | :-----------: |
| x.y.z-h   |   X% Y byte   |    espXY    |     link      |

#### ATTACHED BOOT (SERIAL) LOG

```
TODO
```

#### COMMUNICATION TEST LOG


|  vesrion  | memory usage  | board type  |     communication    | 
| :------:  | :-----------: | :---------: | :-----------: |
| x.y.z-h   |   X% Y byte   |    espXY    |     x% success rate / call      |


Server log snippet

```
```

Test log

```
```