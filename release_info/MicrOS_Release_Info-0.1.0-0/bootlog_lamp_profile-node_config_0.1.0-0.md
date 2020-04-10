# Test Result Evauation - lamp_profile

## Hardware and Software info


- Device: **nodemcu** - esp8266
- Profile: **lamp_profile**-node_config.json
- **MicrOS: 0.1.0-0**

## Bootlog memory usage - system performance

|            PHASE         |   FREE MEMORY [byte]  |
| ------------------------ | :-------------------: |
|  BASELOAD                |         8896
|  SYSTEM LOAD				|         5504
|  SYSTEM MEMORY USAGE     |         3392

**MICROS SYSTEM MEMORY USAGE: ~ 38 %**

```
[CONFIGHANDLER] inject config:
{'timirqseq': 2000, 'irqmembuf': 1000, 'extirq': True, 'extirqcbf': 'light RGB_toggle', 'gmttime': 2, 'devfid': 'lampy', 'hwuid': '0x2c0xf40x320x440xca0x28', 'version': '0.1.0-0', 'stapwd': '<pwd>', 'appwd': 'ADmin123', 'timirqcbf': 'system heartbeat', 'staessid': '<wifi name>', 'soctout': 100, 'devip': '10.0.1.95', 'boothook': '
light RGB_deinit', 'timirq': True, 'pled': True, 'dbg': True, 'nwmd': 'STA', 'socport': 9008}
[CONFIGHANDLER] Inject default data struct successful
[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [0] AFTER SOCKET SERVER CREATION ~~~~~
stack: 2864 out of 8192
GC: total: 37952, used: 29056, free: 8896
 No. of 1-blocks: 320, 2-blocks: 81, max blk sz: 264, max free sz: 556
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~ [PROFILING INFO] - [1] MAIN BASELOAD ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 29504, free: 8448
 No. of 1-blocks: 340, 2-blocks: 83, max blk sz: 264, max free sz: 528
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT HOOKS] EXECUTION...
|-[BOOT HOOKS] SHELL EXEC: light RGB_deinit
|-[BOOT HOOKS] state: True
~~~~~ [PROFILING INFO] - [2] AFTER SAFE BOOT HOOK ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 28976, free: 8976
 No. of 1-blocks: 319, 2-blocks: 86, max blk sz: 264, max free sz: 432
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[NW: STA] SET WIFI: elektroncsakpozitivan
        | [NW: STA] CONNECT TO NETWORK elektroncsakpozitivan
        | - [NW: STA] ESSID WAS FOUND True
        | [NW: STA] Waiting for connection... 60/60
[NW: STA] Set device static IP.
[NW: STA] StaticIP was already set: 10.0.1.95
        |       | [NW: STA] network config: ('10.0.1.95', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
NTP setup errer.:[Errno 110] ETIMEDOUT
NTP setup DONE: (2020, 4, 10, 16, 35, 20, 4, 101)
~~~~~ [PROFILING INFO] - [3] AFTER NETWORK CONFIGURATION ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 35232, free: 2720
 No. of 1-blocks: 546, 2-blocks: 129, max blk sz: 264, max free sz: 170
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] Interrupts was enabled, alloc_emergency_exception_buf=1000
[IRQ] TIMIRQ ENABLED: SEQ: 2000 CBF: system heartbeat
~~~~~ [PROFILING INFO] - [4] AFTER TIMER INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 31616, free: 6336
 No. of 1-blocks: 322, 2-blocks: 86, max blk sz: 264, max free sz: 303
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[IRQ] EVENTIRQ ENABLED PIN: 12 CBF: light RGB_toggle
~~~~~ [PROFILING INFO] - [5] AFTER EXTERNAL INTERRUPT SETUP ~~~~~
stack: 2256 out of 8192
GC: total: 37952, used: 32448, free: 5504
 No. of 1-blocks: 351, 2-blocks: 89, max blk sz: 264, max free sz: 261
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  [ socket server ] SERVER ADDR: telnet 10.0.1.95 9008
    [ socket server ] Socket bind complete
      [ socket server ] Socket now listening
        [ socket server ] wait to accept a connection - blocking call...
```

