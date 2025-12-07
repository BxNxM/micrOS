# micrOS Source Architecture

This diagram traces the boot and runtime orchestration flow using only the Python modules located directly under `micrOS/source`.

```mermaid
graph TD
    main[main.py\nBoot entrypoint] --> loader[micrOSloader.main()\nMode switch]
    loader -->|micrOS mode| core[micrOS.micrOS()\nSystem orchestrator]
    loader -->|webrepl mode| recovery[Recovery webrepl server]

    core --> fs[Files.init_micros_dirs\nFilesystem prep]
    core --> tasks[Tasks.Manager\nAsync task runtime]
    core --> hooks[Hooks.bootup\nBoot tasks]
    core --> net[Network.auto_nw_config\nAP/STA selection]
    net --> timeSync[Time.suntime + Time.ntp_time\nClock sync]
    core --> interrupts[Interrupts.initEventIRQs + enableInterrupt/enableCron\nIRQ setup]
    core --> server[Server.run_server\nTCP + optional HTTP]
    server --> shell[Shell + WebEngine\nConsole / Web UI]
    core --> espnow[Hooks.enableESPNow\nESP-NOW endpoint]
    tasks --> queue[TaskBase / NativeTask / MagicTask\nTask creation + queueing]
    tasks --> idle[Idle task\nLoad monitor + STA self-heal]
    server -. uses .-> tasks
    net -. feeds .-> tasks
```

## Flow overview
- **Boot entry**: `main.py` enables garbage collection and delegates startup to `micrOSloader.main()`, which decides between normal micrOS boot and recovery/webrepl mode based on the `.if_mode` flag. 【F:micrOS/source/main.py†L1-L24】【F:micrOS/source/micrOSloader.py†L18-L127】
- **Core orchestration**: In micrOS mode, `micrOS.micrOS()` initializes filesystem directories, sets up the async task manager, runs boot hooks, configures networking, schedules interrupts, launches the TCP/HTTP server, enables ESP-NOW, and finally enters the event loop. 【F:micrOS/source/micrOS.py†L11-L93】
- **Task runtime**: `Tasks.Manager` is a singleton that queues `NativeTask`/`MagicTask` instances, spawns an idle task to monitor system load, and periodically triggers STA network self-repair when needed. 【F:micrOS/source/Tasks.py†L33-L334】
- **Networking and time**: `Network.auto_nw_config()` selects STA when available and falls back to AP mode; STA boot flows into sun-time and NTP synchronization. `sta_high_avail()` provides self-healing during runtime. 【F:micrOS/source/Network.py†L221-L267】【F:micrOS/source/micrOS.py†L65-L90】
- **Server interfaces**: `Server.run_server()` registers a TCP shell and optional HTTP listener, each backed by `Shell`/`WebEngine` clients; active connections are tracked and surfaced through `Tasks.Manager`. 【F:micrOS/source/Server.py†L380-L427】【F:micrOS/source/Server.py†L9-L35】
