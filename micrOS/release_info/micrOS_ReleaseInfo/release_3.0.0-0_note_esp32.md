# Release validation
### VERSION: 3.0.0-0

| version |     memory usage      | board type  |     config    |
|:-------:|:---------------------:| :---------: | :-----------: |
| 3.0.0-0 | **66.0%** 95 488 byte |    esp32    |   `default`   |

## Deployment

Installed with micrOS DevToolKit GUI Dashboard

# Validation & Measurements

## [1] micrOS bootup with default config (STA mode)

```
[loader][if_mode:True] .if_mode file not exists -> micros interface
[loader][main mode] Start micrOS (default)
[BOOT] rootFS validation: ['/config', '/modules', '/lib', '/logs', '/data', '/web']
[CONF] SKIP obsolete keys check (no .cleanup)
[CONF] User config injection done
[PIN MAP] esp32
[io] Init pin: builtin:2
[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.
~~~~~ [PROFILING INFO] - [memUsage] MAIN LOAD ~~~~~
stack: 1472 out of 15360
GC: total: 112000, used: 63088, free: 48912, max new split: 53248
 No. of 1-blocks: 741, 2-blocks: 207, max blk sz: 142, max free sz: 3057
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[TASK MANAGER] <<constructor>>
[BOOT] info: PowerOn
[BOOT] EXECUTION...
[BOOT HOOKS] CPU boost mode ON: 240000000 Hz
[NW: STA] Enable
	| - [NW: STA] ESSID WAS FOUND: elektroncsakpozitivan_2G
	| [NW: STA] CONNECT TO NETWORK elektroncsakpozitivan_2G
	| [NW: STA] Waiting for connection... 60 sec
	| [NW: STA] Waiting for connection... 59 sec
	| [NW: STA] Waiting for connection... 58 sec
	| [NW: STA] Waiting for connection... 57 sec
	| [NW: STA] Waiting for connection... 56 sec
[NW: STA] Set device static IP.
	| [NW: STA] micrOS dev. StaticIP request: 10.0.1.72
[NW: STA] Enable
	| - [NW: STA] ESSID WAS FOUND: elektroncsakpozitivan_2G
	| [NW: STA] CONNECT TO NETWORK elektroncsakpozitivan_2G
	| [NW: STA] Waiting for connection... 60 sec
[NW: STA] Set device static IP.
[NW: STA][SKIP] StaticIP conf.: 10.0.1.72 ? 10.0.1.72
	|	| [NW: STA] network config: ('10.0.1.72', '255.255.255.0', '10.0.1.1', '10.0.1.1')
	|	| [NW: STA] CONNECTED: True
Cron: False - SKIP sync
[IRQ] EXTIRQ SETUP - EXT IRQ1: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ2: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ3: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] EXTIRQ SETUP - EXT IRQ4: False TRIG: n/a
|- [IRQ] EXTIRQ CBF: n/a
[IRQ] TIMIRQ SETUP: False SEQ: 1000
|- [IRQ] TIMIRQ CBF:n/a
[IRQ] CRON IRQ SETUP: False SEQ: 5000
|- [IRQ] CRON CBF:n/a
|[ socket server ] <<constructor>>
~~~~~ [PROFILING INFO] - [memUsage] SYSTEM IS UP AND RUNNING ~~~~~
stack: 1472 out of 15360
GC: total: 112000, used: 91744, free: 20256, max new split: 32768
 No. of 1-blocks: 1487, 2-blocks: 338, max blk sz: 142, max free sz: 1266
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[TASK MANAGER] watchdog enabled: 30000 ms
|-[ socket server ] Start socket server on 10.0.1.72
|--- TCP server ready, connect: telnet 10.0.1.72 9008
```

|   stage   |     memory usage      |    all memory   |             details         |
| :------:  |:---------------------:| :-------------: |  :------------------------: |
| inital  | **56.3%** 63 088 byte |     112 000 byte    |   `[memUsage] MAIN LOAD`   |
| running  |    **79.5%** 89136 byte  |     112 000 byte    |   `[memUsage] SYSTEM IS UP`   |

## [2] Memory usage At bootup with default config

```
node01 $ system memory_usage
 percent: 63.8
 mem_used: 92304
 
node01 $ modules
['system', 'task']
```

|   stage   |  memory usage   |    all memory   |             details         |
| :------:  |:---------------:| :-------------: |  :------------------------: |
|  running/clean  | **63.8%** 92 304 byte |  144 678 byte   | `over socket: system memory_usage` |

## [3] System test results:

```
----------------------------------- micrOS System Test results on node01:3.0.0-0 device -----------------------------------
	TEST NAME		STATE		Description

	single_cmds:		OK		[i][ST] Run single command execution check [hello]
	shell_cmds:		OK		[i][ST] Run built-in shell commands [modules|version|help]
	lm_cmd_exec:		OK		[i][ST] Run Load Module command execution check [system heartbeat]
	config_get:		OK		[i][ST] Run micrOS config get [conf -> socport]
	config_set:		OK		[i][ST] Run micrOS config set [conf -> utc]
	task_oneshot:		OK		[i][ST] Run async microTask check [system clock &]
	task_loop:		OK		[i][Stop task] [ST] Run async microTask check [system clock &&] + task kill
	task_list:		OK		[i][ST] Run micrOS Task list feature check [task list][task list >json]
	version:		OK		[i][ST] Run micrOS get version [version] v:3.0.0-0
	json_check:		OK		[i][ST] Run micrOS raw output check aka >json [system rssi >json] out: {"Amazing": -64}
	response_time:		OK		[i][ST] Measure response time [system heartbeat]x10 deltaT: 0.0366 s
	negative_api:		OK		[i][ST] Run micrOS Negative API check [Invalid CMDs + conf]
	dhcp_hostname:		OK		[i][ST] Check host node01.local and resolve IP: 10.0.1.179
	lm_exception:		OK		[i][ST] Check robustness - exception [robustness raise_error]: Valid error msg: exec_lm_core *->raise_error: *
	mem_usage:		OK		[i][ST] OK: memory usage 66.0% (95488 bytes)
	disk_usage:		OK		[i][ST] OK: disk usage 30.9% (647168 bytes)
	webui_conn:		OK		[i][ST] WEBUI IS DISABLED (False)
	mem_alloc:		OK		[i][ST] Check robustness - memory_leak [robustness memory_leak 12]: Mem alloc: [12] RAM Alloc.: 0 kB 208 byte
	recursion:		OK		[i][ST] Check robustness - recursion [robustness recursion_limit 8]-> Recursion limit: 8
	intercon:		OK		[i][ST] Check device-device connectivity:
		Device was found: RingLamp.local:(True, {'tag': 'con.RingLamp.hello', 'verdict': 'Starting: task show con.RingLamp.hello'}): (True, 'hello:RingLamp:micr2462abfddb44OS')
		Negative test: Device was not found: notavailable.local":(True, {'tag': 'con.notavailable.hello', 'verdict': 'Starting: task show con.notavailable.hello'}): (True, '')
	micros_alarms:		OK		[i][ST] Test alarm state - system alarms should be null -1 !!!WARN!!! [2] out: ~~~ /logs/boot.sys.log
~~~ 	2000.1.1-0:0:2 [BOOT] info: PowerOn
~~~ 	2000.1.1-0:0:2 [BOOT] info: PowerOn
~~~ 	2026.3.22-18:40:29 [BOOT] info: HardReset
~~~ 	2026.3.22-18:46:20 [BOOT] info: HardReset
~~~ /logs/err.sys.log
~~~ 	2026.3.22-18:32:12 [ERR] ntptime: -202
~~~ /logs/user.sys.log
~~~ 	2026.3.22-18:46:16 [aio] loop stopped: [Errno 5] EIO
~~~ 	2026.3.22-18:47:24 Robustness TeSt ErRoR
~~~ 	2026.3.22-18:47:38 [intercon] send_cmd notavailable.local oserr: -202
~~~ /logs/warn.sys.log
~~~ 	2026.3.22-18:46:50 [WARN] Client.a_send (auto-drop) S1.72:59038: [Errno 128] ENOTCONN
 NOK alarm: 2
	conn_metrics:		OK		[i]SINGLE CONNECTION LOAD TEST X10, AVERAGE REPLY TIME: 0.027 sec
                                                   MULTI CONNECTION LOAD TEST X10, AVERAGE REPLY TIME: 0.073s, SERVER AVAILABILITY: 100% (72 ms)
	micros_tasks:		OK		[i]---- micrOS  top ----
                                                   #queue: 5 #load: 2%
                                                   #Active   #taskID
                                                   Yes       server
                                                   Yes       idle
                                                   No        con.notavailable.hello
                                                   No        con.RingLamp.hello
	clean-reboot:		OK		[i][reboot-h][OK] successfully rebooted: hello:node01:micr7c9ebd6147c4OS (boot time: ~4sec)

PASS RATE: 100.0 %
RESULT: OK
--------------------------------------------------------------------------------------
```

|   stage   |     memory usage      |    all memory   |             details         |
| :------:  |:---------------------:| :-------------: |  :------------------------: |
|  running/system test result  | **66.0%** 95 488 byte |  144 678 byte   | `mem_usage` |



