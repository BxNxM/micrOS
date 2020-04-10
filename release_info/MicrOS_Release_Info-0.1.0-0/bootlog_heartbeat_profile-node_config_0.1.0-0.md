# Test Result Evauation - heartbeat_profile

## Hardware and Software info


- Device: **nodemcu** - esp8266
- Profile: **heartbeat_profile**-node_config.json
- **MicrOS: 0.1.0-0**

## Bootlog memory usage - system performance

|            PHASE         |   FREE MEMORY [byte]  |
| ------------------------ | :-------------------: |
|  BASELOAD                |         9056
|  SYSTEM LOAD				|         7648
|  SYSTEM MEMORY USAGE     |         1408

**MICROS SYSTEM MEMORY USAGE: ~ 15,5 %**

## Detailed boot logs

```
[CONFIGHANDLER] inject config:
{'timirqseq': 3000, 'irqmembuf': 1000, 'extirq': False, 'extirqcbf': 'n/a', 'gmttime': 2, 'devfid': 'release', 'hwuid': '0x2c0xf40x320x440xca0x28', 'version': '0.1.0-1', 's
tapwd': '<pwd>', 'appwd': 'ADmin123', 'timirqcbf': 'system heartbeat', 'staessid': '<essid>', 'soctout': 100, 'devip': '10.0.1.95', 'boothook': 'n/a', 'timirq': True, 'pled': True, 'dbg': True, 'nwmd': 'STA', 'socport': 9008}
[CONFIGHANDLER] Inject default data struct successful
[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [0] AFTER SOCKET SERVER CREATION ~~~~~
stack: 2864 out of 8192
GC: total: 37952, used: 28896, free: 9056
 No. of 1-blocks: 314, 2-blocks: 79, max blk sz: 264, max free sz: 566
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29344, free: 8608
 No. of 1-blocks: 334, 2-blocks: 81, max blk sz: 264, max free sz: 538
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29792, free: 8160
 No. of 1-blocks: 354, 2-blocks: 83, max blk sz: 264, max free sz: 510
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
[NW: STA] Set device static IP.
[NW: STA] StaticIP was already set: 10.0.1.95
        |       | [NW: STA] network config: ('10.0.1.95', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup errer.:[Errno 110] ETIMEDOUT
NTP setup errer.:-2
NTP setup errer.:[Errno 110] ETIMEDOUT
NTP setup DONE: (2020, 4, 10, 16, 20, 9, 4, 101)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 28208, free: 9744
 No. of 1-blocks: 294, 2-blocks: 78, max blk sz: 264, max free sz: 308
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
[IRQ] TIMIRQ ENABLED: SEQ: 3000 CBF: system heartbeat
~~~~~ [PROFILING INFO] - [4] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29696, free: 8256
 No. of 1-blocks: 278, 2-blocks: 77, max blk sz: 264, max free sz: 349
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ: isenable: False callback: n/a
~~~~~ [PROFILING INFO] - [5] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 30304, free: 7648
 No. of 1-blocks: 303, 2-blocks: 78, max blk sz: 264, max free sz: 349
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  [ socket server ] SERVER ADDR: telnet 10.0.1.95 9008
    [ socket server ] Socket bind complete
      [ socket server ] Socket now listening
        [ socket server ] wait to accept a connection - blocking call...
```

