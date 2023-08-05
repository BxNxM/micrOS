# Release validation
### VERSION: 1.21.0-4

|  version  |       memory usage    | board type  |     config    |
| :------:  | :-------------------: | :---------: | :-----------: |
| 1.21.0-4  | **57.3%** 63 728 byte |    esp32    |   `default`   |

## Deployment

Installed with micrOS DevToolKit GUI Dashboard

# Validation & Measurements

## [1] micrOS bootup with default config (STA mode)

```

[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONF] SKIP obsolete keys check (no cleanup.pds)
[CONF] User config injection done
[CONF] Save conf struct successful
[PIN MAP] esp32
[io] Init pin: builtin:2
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
~~~~~ [PROFILING INFO] - [memUsage] MAIN LOAD ~~~~~
stack: 1520 out of 15360
GC: total: 111168, used: 71 456, free: 39 712
 No. of 1-blocks: 1030, 2-blocks: 232, max blk sz: 142, max free sz: 2482
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[BOOT] EXECUTION ...
[BOOT HOOKS] Set up CPU high Hz - boostmd: True
[IRQ] EXTIRQ SETUP - EXT IRQ1: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ2: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ3: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ4: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[NW: STA] SET WIFI STA NW elektroncsakpozitivan_2G
        | - [NW: STA] ESSID WAS FOUND: elektroncsakpozitivan_2G
        | [NW: STA] CONNECT TO NETWORK elektroncsakpozitivan_2G
        | [NW: STA] Waiting for connection... 60 sec
        | [NW: STA] Waiting for connection... 59 sec
        | [NW: STA] Waiting for connection... 58 sec
        | [NW: STA] Waiting for connection... 57 sec
        | [NW: STA] Waiting for connection... 56 sec
        | [NW: STA] Waiting for connection... 55 sec
        | [NW: STA] Waiting for connection... 54 sec
        | [NW: STA] Waiting for connection... 53 sec
        | [NW: STA] Waiting for connection... 52 sec
        | [NW: STA] Waiting for connection... 51 sec
        | [NW: STA] Waiting for connection... 50 sec
[NW: STA] Set device static IP.
[NW: STA] IP was not stored: n/a
        |       | [NW: STA] network config: ('10.0.1.193', '255.255.255.0', '10.0.1.1', '10.0.1.1')
        |       | [NW: STA] CONNECTED: True
Cron: False - SKIP sync
[IRQ] TIMIRQ SETUP: False SEQ: 1000
|- [IRQ] TIMIRQ CBF:n/a
[IRQ] CRON IRQ SETUP: False SEQ: 3000
|- [IRQ] CRON CBF:n/a
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [memUsage] SYSTEM IS UP ~~~~~
stack: 1520 out of 15360
GC: total: 111168, used: 79 728, free: 31 440
 No. of 1-blocks: 1299, 2-blocks: 271, max blk sz: 142, max free sz: 1964
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] Start socket server on 10.0.1.193:9008
|--- TCP server ready, connect: telnet 10.0.1.193 9008
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|  inital   |  **64.2%** 71 456 byte |  111 168 byte   |   `[memUsage] MAIN LOAD`    |
|  running  |  **71,7%** 79 728 byte |  111 168 byte   |   `[memUsage] SYSTEM IS UP` |

## [2] Memory usage At bootup with default config

```
node01 $ system memory_usage
 percent: 57.3
 mem_used: 63 728
node01 $ lmpacman module
['Common', 'usocket', 'neopixel', 'InterruptHandler', 'TinyPLed', 'uasyncio.stream',
'network', 'uasyncio', 'Debug', 'ConfigHandler', 'flashbdev', 'micrOS', 'micrOSloader',
'LM_lmpacman', 'Network', 'urequests', 'Hooks', 'LogicalPins', 'uasyncio.core', 'Time',
'uasyncio.event', 'SocketServer', 'InterpreterShell', 'TaskManager', 'LP_esp32']
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|  running/clean  |  **57.3%** 63 728 byte |  111 218 byte   | `over socket: system memory_usage` |

## [3] System test results:

```
----------------------------------- micrOS System Test results on node01 device -----------------------------------
	TEST NAME		STATE		Description

	single_cmds:		OK		[i][ST] Run single command execution check [hello]
	lm_cmd_exec:		OK		[i][ST] Run Load Module command execution check [system heartbeat]
	config_get:		    OK		[i][ST] Run micrOS config get [conf -> socport]
	config_set:		    OK		[i][ST] Run micrOS config set [conf -> utc]
	task_oneshot:		OK		[i][ST] Run micrOS BgJob check [system clock &]
	task_loop:		    OK		[i][Stop task] [ST] Run micrOS Async Task check [system clock &&] + task kill
	version:		    OK		[i][ST] Run micrOS get version [version] v:1.21.0-4
	json_check:		    OK		[i][ST] Run micrOS raw output check aka >json [system rssi >json] out: {"Amazing": -60}
	reponse time:		OK		[i][ST] Measure response time [system heartbeat]x10 deltaT: 0.0325 s
	negative_api:		OK		[i][ST] Run micrOS Negative API check [Invalid CMDs + conf]
	dhcp_hostname:		OK		[i][ST] Check host node01.local and resolve IP: 10.0.1.193
	lm_exception:		OK		[i][ST] Check robustness - exception [robustness raise_error]: Valid error msg: exec_lm_core *->raise_error: *
	mem_usage:		    OK		[i][ST] OK: memory usage 60.4% (67136 bytes)
	disk_usage:		    OK		[i][ST] WARNING: disk usage 17.8% (372736 bytes)
	mem_alloc:		    OK		[i][ST] Check robustness - memory_leak [robustness memory_leak 12]: Mem alloc: [12] RAM Alloc.: -4 kB 432 byte
	recursion:		    OK		[i][ST] Check robustness - recursion [robustness recursion_limit 5]
	intercon:		    OK		[i][ST] Check device-device connectivity:
		Device was found: RingLamp.local:(True, {'verdict': 'Task started: task show con.RingLamp.hello', 'tag': 'con.RingLamp.hello'}): (True, 'hello:RingLamp:micr2462abfddb44OS')
		Negative test: Device was not found: "notavailable.local":(True, {'verdict': 'Task started: task show con.notavailable.hello', 'tag': 'con.notavailable.hello'}): (True, '')
	micros_alarms:		OK		[i][ST] Test alarm state - system alarms should be null [0] out: 2023.8.4-16:39:54 [intercon] send_cmd notavailable.local oserr: -2
 OK alarm: 0
	conn_metrics:		OK		[i]SINGLE CONNECTION LOAD TEST X10, AVERAGE REPLY TIME: 0.022 sec
                                                   MULTI CONNECTION LOAD TEST X10, AVERAGE REPLY TIME: 0.07s, SERVER AVAILABILITY: 100% (0.07s)
	micros_tasks:		OK		[i]---- micrOS  top ----
                                                   #queue: 3 #load: 1%
                                                   #Active   #taskID
                                                   No        system.clock
                                                   No        con.notavailable.hello
                                                   Yes       idle
                                                   Yes       server
                                                   No        con.RingLamp.hello
PASS RATE: 100.0 %
RESULT: OK
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|  running/system test result  |  **60.4%** 67136 byte |  111 218 byte   | `mem_usage:` |


## [4] Memory usage after system test

Additional module loads:

* LM_system
* LM_intercon
* LM_lmpacman
* LM_robustness
* InterConnect

```
node01 $ system memory_usage
 percent: 65.3
 mem_used: 72 608

node01 $ lmpacman module
['Common', 'usocket', 'neopixel', 'LM_robustness', 'InterruptHandler', 'TinyPLed',
'uasyncio.stream', 'network', 'uasyncio', 'Debug', 'ConfigHandler', 'flashbdev',
'micrOS', 'micrOSloader', 'LM_system', 'Network', 'urequests', 'Hooks', 'LM_intercon',
'InterConnect', 'LogicalPins', 'LM_lmpacman', 'uasyncio.core', 'Time', 'uasyncio.event',
'SocketServer', 'InterpreterShell', 'TaskManager', 'LP_esp32']
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|  running/after system test  |  **65.3%** 72 608 byte |  111 218 byte   | `over socket: system memory_usage` |

|   modules   |       memory usage   |  all memory     |           details           |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|    5      |    **8%** 8 897 byte   |  111 218 byte   |   `average/module: 1,8kb `  |



