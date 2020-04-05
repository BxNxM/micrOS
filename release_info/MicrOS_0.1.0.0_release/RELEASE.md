# MicrOS 0.1.0.0 Stabile release info

# COMMIT ON MASTER: 

## Memory usage - with minimal config:

Configuration profile: `MicrOs/release_info/MicrOS_0.1.0.0_release/node_config_profiles/baseload-node_confing.json`


|         Features          |    Status  |
| ------------------------- | ---------- |
| 1. Bootup hook				  |    NO      |
| 2. Network setup          |     YES    |
| 3. Timer IRQ              |     NO     |
| 4. External / evant IRQ   |     NO     |
| 5. Socket Shell Server    |     YES    |

|           Phase             |    Free memory [byte]
| --------------------------- | :---------------------: |
| MicrOS memory usage         |   ~ **3280** byte [ on nodemcu - esp8266: **32 %** ] 
| Micropython baseload, free memory       |   10160 byte |
| MicrOS baseload, free memory|    **6880 byte** |

Boot up log: `MicrOs/release_info/MicrOS_0.1.0.0_release/release_0.1.0.0_baseload.log`


## Memory usage - with light application config:

Configuration profile: `MicrOs/release_info/MicrOS_0.1.0.0_release/node_config_profiles/lamp-node_config.json`

|          Features         |    Status  |
| ------------------------- | ---------- |
| 1. Bootup hook				  |    YES      |
| 2. Network setup          |     YES    |
| 3. Timer IRQ              |     YES     |
| 4. External / evant IRQ   |     YES     |
| 5. Socket Shell Server    |     YES    |

|           Phase             |    Free memory [byte]
| --------------------------- | :---------------------: |
| MicrOS memory usage         |   ~ **2848** byte [ on nodemcu - esp8266: **38** % ] 
| Micropython baseload, free memory      |   7328 byte |
| MicrOS baseload, free memory|    **4480 byte** | 

Boot up log: `MicrOs/release_info/MicrOS_0.1.0.0_release/release_0.1.0.0_lamp_bootup.log`

## Stability lamp test - 100 % connection success

### Clinet log

File: `MicrOs/release_info/MicrOS_0.1.0.0_release/light_app_stability_client.log`

```
===========================
R: 350, G: 350 B: 250
CMD: ./socketClient.py --dev Lamp light RGB(350, 350, 250)
===========================
==> EXITCODE: 0				3/63
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
SET RGB
===========================
R: 350, G: 350 B: 350
CMD: ./socketClient.py --dev Lamp light RGB(350, 350, 350)
===========================
==> EXITCODE: 0				3/64
Load MicrOS device cache: /Users/bnm/Documents/NodeMcu/MicrOs/tools/../user_data/device_conn_cache.json
Device was found: Lamp
SET RGB
```

> NOTE: 3 error was caused by clinet msg retrievel limiatation. 

### Server log

File: `MicrOs/release_info/MicrOS_0.1.0.0_release/light_app_stability_server.log`

```
...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        [ socket server ] RAW INPUT |exit|
          [ socket server ] exit and close connection from ('10.0.1.7', 59511)
[ socket server ] wait to accept a connection - blocking call...
  [ socket server ] Connected with 10.0.1.7:59513
~~~~~ [PROFILING INFO] - [X] AFTER INTERPRETER EXECUTION ~~~~~
stack: 2480 out of 8192
GC: total: 37952, used: 35104, free: 2848
 No. of 1-blocks: 374, 2-blocks: 97, max blk sz: 264, max free sz: 45
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    [ socket server ] RAW INPUT |light RGB(350, 350, 350)|
      from LM_light import RGB
~~~~~ [PROFILING INFO] - [X] AFTER INTERPRETER EXECUTION ~~~~~
stack: 2480 out of 8192
GC: total: 37952, used: 33712, free: 4240
 No. of 1-blocks: 315, 2-blocks: 93, max blk sz: 264, max free sz: 43
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        [ socket server ] RAW INPUT |exit|
          [ socket server ] exit and close connection from ('10.0.1.7', 59513)
[ socket server ] wait to accept a connection - blocking call...
```















