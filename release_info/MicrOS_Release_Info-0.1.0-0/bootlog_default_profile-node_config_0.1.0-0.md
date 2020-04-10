# Test Result Evauation - default_profile

## Hardware and Software info


- Device: **nodemcu** - esp8266
- Profile: **default_profile**-node_config.json
- **MicrOS: 0.1.0-0**

## Bootlog memory usage - system performance

|            PHASE         |   FREE MEMORY [byte]  |
| ------------------------ | :-------------------: |
|  BASELOAD                |         9328
|  SYSTEM LOAD				|         8016
|  SYSTEM MEMORY USAGE     |         1312

**MICROS SYSTEM MEMORY USAGE: ~14 %**

## Detailed boot logs

```
[CONFIGHANDLER] inject config:
{'timirqseq': 3000, 'irqmembuf': 1000, 'extirq': False, 'extirqcbf': 'n/a', 'gmttime': 2, 'devfid': 'release', 'hwuid': 'n/a', 'version': '0.1.0-1', 'stapwd': '<pwd>', 'appwd': 'ADmin123', 'timirqcbf': 'n/a', 'staessid': '<wifiname>', 'soctout': 100, 'devip': 'n/a', 'boothook': 'n/a', 'timirq': False, 'pled': True, 'dbg': True, 'nwmd': 'STA', 'socport': 9008}
[CONFIGHANDLER] Inject default data struct successful
[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [0] AFTER SOCKET SERVER CREATION ~~~~~
stack: 2864 out of 8192
GC: total: 37952, used: 28624, free: 9328
 No. of 1-blocks: 306, 2-blocks: 76, max blk sz: 264, max free sz: 583
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29072, free: 8880
 No. of 1-blocks: 326, 2-blocks: 78, max blk sz: 264, max free sz: 555
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29520, free: 8432
 No. of 1-blocks: 346, 2-blocks: 80, max blk sz: 264, max free sz: 527
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: elektroncsakpozitivan
        | [NW: STA] CONNECT TO NETWORK elektroncsakpozitivan
        | - [NW: STA] ESSID WAS FOUND True
        | [NW: STA] Waiting for connection... 60/60
        | [NW: STA] Waiting for connection... 59/60
        | [NW: STA] Waiting for connection... 58/60
        | [NW: STA] Waiting for connection... 57/60
        | [NW: STA] Waiting for connection... 56/60
        | [NW: STA] Waiting for connection... 55/60
        | [NW: STA] Waiting for connection... 54/60
        | [NW: STA] Waiting for connection... 53/60
[NW: STA] Set device static IP.
[NW: STA] IP was not stored: n/a
        |       | [NW: STA] network config: ('10.0.1.95', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup DONE: (2020, 4, 10, 15, 50, 54, 4, 101)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 28160, free: 9792
 No. of 1-blocks: 305, 2-blocks: 79, max blk sz: 264, max free sz: 273
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
[IRQ] TIMIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [4] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 28288, free: 9664
 No. of 1-blocks: 266, 2-blocks: 74, max blk sz: 264, max free sz: 245
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [5] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 28896, free: 9056
 No. of 1-blocks: 291, 2-blocks: 75, max blk sz: 264, max free sz: 245
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  [ socket server ] SERVER ADDR: telnet 10.0.1.95 9008
    [ socket server ] Socket bind complete
      [ socket server ] Socket now listening
        [ socket server ] wait to accept a connection - blocking call...
          [ socket server ] Connected with 10.0.1.7:62090
            [ socket server ] RAW INPUT |help|
~~~~~ [PROFILING INFO] - [X] AFTER INTERPRETER EXECUTION ~~~~~
stack: 2480 out of 8192
GC: total: 37952, used: 29936, free: 8016
 No. of 1-blocks: 320, 2-blocks: 86, max blk sz: 264, max free sz: 102
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
              [ socket server ] RAW INPUT |system memfree|
                from LM_system import memfree
~~~~~ [PROFILING INFO] - [X] AFTER INTERPRETER EXECUTION ~~~~~
stack: 2480 out of 8192
GC: total: 37952, used: 29792, free: 8160
 No. of 1-blocks: 294, 2-blocks: 81, max blk sz: 264, max free sz: 245
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                  [ socket server ] RAW INPUT |system modules|
                    from LM_system import modules
~~~~~ [PROFILING INFO] - [X] AFTER INTERPRETER EXECUTION ~~~~~
stack: 2480 out of 8192
GC: total: 37952, used: 32032, free: 5920
 No. of 1-blocks: 371, 2-blocks: 88, max blk sz: 264, max free sz: 245
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                      [ socket server ] RAW INPUT |exit|
                        [ socket server ] exit and close connection from ('10.0.1.7', 62090)
[ socket server ] wait to accept a connection - blocking call...
```
