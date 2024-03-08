# Release validation
### VERSION: 2.0.0-0

|  version  |       memory usage    | board type  |     config    |
| :------:  | :-------------------: | :---------: | :-----------: |
| 2.0.0-0  | **45.4%** 68 768 byte |    esp32    |   `default`   |

## Deployment

Installed with micrOS DevToolKit GUI Dashboard

# Validation & Measurements

## [1] micrOS bootup with default config (STA mode)

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[CONF] SKIP obsolete keys check (no cleanup.pds)
[CONF] User config injection done
[CONF] Save conf successful
[PIN MAP] esp32
[io] Init pin: builtin:2
[io] ReInit pin: builtin:2
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
~~~~~ [PROFILING INFO] - [memUsage] MAIN LOAD ~~~~~
stack: 1536 out of 15360
GC: total: 64000, used: 60080, free: 3920, max new split: 110592
 No. of 1-blocks: 713, 2-blocks: 188, max blk sz: 142, max free sz: 26
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[TASK MANAGER] <<constructor>>
[BOOT] EXECUTION ...
[BOOT HOOKS] Set up CPU high Hz - boostmd: True
[NW: STA] SET WIFI STA NW elektroncsakpozitivan_2G
	| - [NW: STA] ESSID WAS FOUND: elektroncsakpozitivan_2G
	| [NW: STA] CONNECT TO NETWORK elektroncsakpozitivan_2G
	| [NW: STA] Waiting for connection... 60 sec
	| [NW: STA] Waiting for connection... 59 sec
	| [NW: STA] Waiting for connection... 58 sec
	| [NW: STA] Waiting for connection... 57 sec
	| [NW: STA] Waiting for connection... 56 sec
[NW: STA] Set device static IP.
[NW: STA] IP was not stored: n/a
	|	| [NW: STA] network config: ('10.0.1.193', '255.255.255.0', '10.0.1.1', '10.0.1.1')
	|	| [NW: STA] CONNECTED: True
Cron: False - SKIP sync
[IRQ] EXTIRQ SETUP - EXT IRQ1: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: bytearray(b'n/a')
[IRQ] EXTIRQ SETUP - EXT IRQ2: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: bytearray(b'n/a')
[IRQ] EXTIRQ SETUP - EXT IRQ3: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: bytearray(b'n/a')
[IRQ] EXTIRQ SETUP - EXT IRQ4: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: bytearray(b'n/a')
[IRQ] TIMIRQ SETUP: False SEQ: 1000
|- [IRQ] TIMIRQ CBF:n/a
[IRQ] CRON IRQ SETUP: False SEQ: 5000
|- [IRQ] CRON CBF:n/a
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [memUsage] SYSTEM IS UP ~~~~~
stack: 1536 out of 15360
GC: total: 64000, used: 62992, free: 1008, max new split: 90112
 No. of 1-blocks: 809, 2-blocks: 208, max blk sz: 142, max free sz: 32
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-[ socket server ] Start socket server on 10.0.1.193
|--- TCP server ready, connect: telnet 10.0.1.193 9008
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
| inital  | **39.6%** 60 080 byte |     151 471 byte    |   `[memUsage] MAIN LOAD`   |
| running  | **41.5%** 62 992 byte |     151 471 byte    |   `[memUsage] SYSTEM IS UP`   |

## [2] Memory usage At bootup with default config

```
node01 $ system memory_usage
 percent: 45.4
 mem_used: 68768
node01 $ lmpacman module
['asyncio.event', 'Config', 'asyncio.stream', 'Common', 'LM_lmpacman', 'Time', 'LM_system', 'microIO', 'flashbdev', 'Interrupts', 'Server', 'uasyncio', 'Shell', 'asyncio', 'Network', 'micrOS', 'urequests', 'Tasks', 'Hooks', 'micrOSloader', 'Debug', 'asyncio.core', 'IO_esp32']
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|  running/clean  |  **45.4%** 68 768 byte |  151 471 byte   | `over socket: system memory_usage` |

## [3] System test results:

```
----------------------------------- micrOS System Test results on node01 device -----------------------------------
	TEST NAME		STATE		Description

	single_cmds:		OK		[i][ST] Run single command execution check [hello]
	lm_cmd_exec:		OK		[i][ST] Run Load Module command execution check [system heartbeat]
	config_get:		OK		[i][ST] Run micrOS config get [conf -> socport]
	config_set:		OK		[i][ST] Run micrOS config set [conf -> utc]
	task_oneshot:		OK		[i][ST] Run micrOS BgJob check [system clock &]
	task_loop:		OK		[i][Stop task] [ST] Run micrOS Async Task check [system clock &&] + task kill
	version:		OK		[i][ST] Run micrOS get version [version] v:1.60.1-3
	json_check:		OK		[i][ST] Run micrOS raw output check aka >json [system rssi >json] out: {"Amazing": -65}
	response_time:		OK		[i][ST] Measure response time [system heartbeat]x10 deltaT: 0.0413 s
	negative_api:		OK		[i][ST] Run micrOS Negative API check [Invalid CMDs + conf]
	dhcp_hostname:		OK		[i][ST] Check host node01.local and resolve IP: 10.0.1.193
	lm_exception:		OK		[i][ST] Check robustness - exception [robustness raise_error]: Valid error msg: exec_lm_core *->raise_error: *
	mem_usage:		OK		[i][ST] OK: memory usage 49.2% (74080 bytes)
	disk_usage:		OK		[i][ST] OK: disk usage 17.6% (368640 bytes)
	webui_conn:		OK		[i][ST] WEBUI IS DISABLED (False)
	mem_alloc:		OK		[i][ST] Check robustness - memory_leak [robustness memory_leak 12]: Mem alloc: [12] RAM Alloc.: 0 kB 96 byte
	recursion:		OK		[i][ST] Check robustness - recursion [robustness recursion_limit 8]-> Recursion limit: 8
	intercon:		OK		[i][ST] Check device-device connectivity:
		Device was found: RingLamp.local:(True, {'verdict': 'Task started: task show con.RingLamp.hello', 'tag': 'con.RingLamp.hello'}): (True, 'hello:RingLamp:micr2462abfddb44OS')
		Negative test: Device was not found: "notavailable.local":(True, {'verdict': 'Task started: task show con.notavailable.hello', 'tag': 'con.notavailable.hello'}): (True, '')
	micros_alarms:		OK		[i][ST] Test alarm state - system alarms should be null [0] out: 2024.3.8-22:0:20 [WARN] ShellCli.send (auto-drop) S1.61:50261: [Errno 104] ECONNRESET
2024.3.8-22:0:21 [WARN] ShellCli.send (auto-drop) S1.61:50267: [Errno 104] ECONNRESET
2024.3.8-22:0:21 [WARN] ShellCli.send (auto-drop) S1.61:50268: [Errno 104] ECONNRESET
2024.3.8-22:0:28 [intercon] send_cmd notavailable.local oserr: -2
2024.3.8-22:0:28 [WARN] ShellCli.send (auto-drop) S1.61:50272: [Errno 128] ENOTCONN
 OK alarm: 0
	conn_metrics:		OK		[i]SINGLE CONNECTION LOAD TEST X10, AVERAGE REPLY TIME: 0.031 sec
                                                   MULTI CONNECTION LOAD TEST X10, AVERAGE REPLY TIME: 0.084s, SERVER AVAILABILITY: 100% (0.084s)
	micros_tasks:		OK		[i]---- micrOS  top ----
                                                   #queue: 4 #load: 2%
                                                   #Active   #taskID
                                                   Yes       server
                                                   Yes       idle
                                                   No        con.notavailable.hello
                                                   No        con.RingLamp.hello
	clean-reboot:		OK		[i][reboot-h][OK] successfully rebooted: hello:node01:micr08b61f3b3e0cOS (boot time: ~6sec)

PASS RATE: 100.0 %
RESULT: OK
```

|   stage   |       memory usage     |    all memory   |             details         |
| :------:  | :--------------------: | :-------------: |  :------------------------: |
|  running/system test result  |  **49.2%** 74 080 byte |  151 471 byte   | `mem_usage` |




