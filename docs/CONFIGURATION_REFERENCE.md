# Configuration and automation reference

This is the complete user-facing reference for micrOS node configuration,
networking, startup actions, schedules, timers, and external interrupts. For a
first installation, follow the concise workflow in the [project README](../README.md).

For normal setup and maintenance, open
`http://<nodename>.local/config` and use the on-device Configuration app.
ShellCli is the low-level fallback when the web interface is unavailable.

## Networking modes

A node normally joins the local Wi-Fi network in station (`STA`) mode. When it
cannot connect, an unconfigured node can fall back to its own access point for
configuration. `nwmd`, `staessid`, `stapwd`, and `devip` control this behavior.
Clients communicate directly with a node; nodes can invoke each other over
sockets or ESP-NOW.

## Basic parameters

| Config key | Default and type | Reboot required | Description |
| --- | --- | :---: | --- |
| `devfid` | `node01` (`str`) | Yes | Friendly device ID. It becomes the AP network name, STA DHCP hostname, and ShellCli prompt after restart. `.local` resolution depends on the router and client operating system. |
| `staessid` | `your_wifi_name` (`str`) | Yes | Wi-Fi network name for STA mode. Separate multiple network names with `;`. |
| `stapwd` | `your_wifi_passwd` (`str`) | Yes | Wi-Fi password for STA mode. For multiple networks, provide passwords separated with `;` in the same order as `staessid`. |
| `appwd` | `ADmin123` (`str`) | Yes | Shared device password used for the AP, WebREPL, ShellCli authentication when enabled, and protected web operations. |
| `boothook` | `n/a` (`str`) | Yes | Commands executed during boot. Separate commands with `;`, for example `web load; rgb load; cct load`. Prefix a command with `#` to disable it temporarily. |
| `webui` | `True` (`bool`) | Yes | Enables the HTTP server on port 80 alongside the shell on `socport`. micrOS disables it at boot when the 80 KiB heap budget cannot be met. `/rest/module/function` invokes Load Module functions; HTTP clients such as Apple Shortcuts can call these endpoints. |
| `espnow` | `False` (`bool`) | Yes | Enables ESP-NOW and starts the `espnow.server` task. It extends InterCon; for example, `system heartbeat >>target.local`. |
| `cron` | `False` (`bool`) | Yes | Enables timestamp-based Load Module execution through Timer(1). |
| `crontasks` | `n/a` (`str`) | No | Scheduler input in `WD:H:M:S!module function` form. Separate entries with `;`; use `;;` when an entry contains multiple `;`-separated commands. Fields accept `*`, and weekdays are 0–6. Sunrise/sunset forms and offsets are also supported. |
| `irq1` … `irq4` | `False` (`bool`) | Yes | Enables the corresponding external event interrupt. |
| `irq1_cbf` … `irq4_cbf` | `n/a` (`str`) | Yes | Command executed for the corresponding external interrupt, in `module function optional_parameters` form. |
| `irq1_trig` … `irq4_trig` | `n/a` (`str`) | Yes | Trigger phase: `up`, `down`, or `both`. |
| `irq_prell_ms` | `300` (`int`) | Yes | Contact-bounce filtering window in milliseconds during which repeated external IRQ events are ignored. |
| `timirq` | `False` (`bool`) | Yes | Enables periodic Load Module execution through Timer(0). |
| `timirqcbf` | `n/a` (`str`) | Yes | Commands executed by Timer(0). Separate multiple commands with `;`. |
| `timirqseq` | `1000` (`int`) | Yes | Timer(0) period in milliseconds. |

## Advanced parameters

| Config key | Default and type | Reboot required | Description |
| --- | --- | :---: | --- |
| `utc` | `60` (`int`) | Yes | UTC offset in minutes used when setting the RTC from NTP. When cron is enabled in STA mode, sunrise/sunset synchronization also updates this value from IP geolocation. |
| `ha` | `True` (`bool`) | Yes | High Availability mode, not Home Assistant integration. Enables the 30-second watchdog. The idle task checks STA connectivity about every three minutes and can reboot to repair a lost connection when a configured SSID becomes visible again. AP mode retains watchdog behavior without STA repair. |
| `cstmpmap` | `n/a` (`str`) | Yes | Select an `IO_<platform>` map or provide `pin_map_name; pin_name:pin_number`. For example, `esp32; dht:22` selects the ESP32 map and overrides logical pin `dht`. In ShellCli, inspect pins with `<module> pinmap`, for example `neopixel pinmap`. |
| `boostmd` | `True` (`bool`) | Yes | Selects low/high CPU frequency. The current ESP32-C3/C6 values are 80/160 MHz, with a 160/240 MHz fallback. Other ports require compatible clock settings. |
| `aioqueue` | `5` (`int`) | Yes | Resource limit for background Load Module tasks and the shared ShellCli/WebCli connection pool. Boot-time memory tuning may reduce an oversized value. |
| `webui_max_con` | `3` (`int`) | Yes | Maximum concurrent HTTP requests. The effective limit is reduced when its memory requirement exceeds 10% of available heap or when it exceeds `aioqueue`. Lower values can mitigate allocation failures caused by fragmentation. |
| `devip` | `n/a` (`str`) | Yes / N/A | Stored/static device IP. The first stored address in STA mode becomes the device static address; it can also be set explicitly. |
| `nwmd` | `STA` (`str`) | Yes | Preferred network mode: `STA` or `AP`. |
| `soctout` | `30` (`int`) | Yes | Socket connection timeout in seconds. When a passive connection reaches the timeout and a new connection arrives, the passive connection is closed. |
| `socport` | `9008` (`int`) | Yes | Socket server port. Changing it can make existing clients and integrations incompatible. |
| `auth` | `False` (`bool`) | Yes | Enables the ShellCli password gate using `appwd`; only `hello` and connection-closing `exit` bypass it. For REST, enabling auth prevents loading new modules but permits calls to modules already resident. Protected registered web callbacks require `appwd` independently. |
| `dbg` | `True` (`bool`) | Yes | Enables runtime diagnostic output, server information, and the progress LED. |
| `version` | `n/a` (`str`) | N/A | System-managed micrOS version metadata populated by the deployment pipeline. Do not edit it manually. |
| `hwuid` | `n/a` (`str`) | N/A | System-managed hardware address/device UID state. |
| `guimeta` | `...` (`str`) | No | Widget metadata and offloaded parameter-type state used by micrOS clients. |

Most unset string parameters use `n/a`. Timer availability depends on the
MicroPython port; the original cron implementation targets ESP32.

## Startup actions and web applications

`boothook` runs initialization before network setup. A typical value begins
with `web load` and continues with application initializers:

```text
web load; rgb load; neopixel load
```

Preserve existing actions when adding another one. Prefix an action with `#` to
disable it while experimenting.

Enable the file manager for the current session with:

```text
web load fileserver=True
```

Add the same command to `boothook` if the file manager should return after every
reboot. Protected file operations may prompt for `appwd`.

DevToolKit's OTA workflow monitors the update and restarts the node when the
operation completes.

In STA mode, NTP sets the clock using `utc`. When cron is enabled,
sunrise/sunset synchronization uses [ip-api.com](http://ip-api.com/json/?fields=lat,lon,timezone,offset)
to update the offset from IP geolocation. The runtime also tracks uptime.

## Schedules and external events

| Mechanism | Configuration and example |
| --- | --- |
| Periodic timer | Enable `timirq`; set `timirqseq` in milliseconds and `timirqcbf` to a command. With `5000` and `bme280 measure`, Timer(0) measures every five seconds. |
| Cron | Enable `cron` and set `crontasks`. `*:8:0:0!rgb rgb r=10 g=60 b=100` runs daily at 08:00. |
| External interrupt | Enable `irqX` (X = 1–4), choose `irqX_trig`, and set `irqX_cbf` to a Load Module callback. |

Cron timestamps use `WD:H:M:S!module function`, with ranges
`0–6:0–23:0–59:0–59` and `*` for any value. Monday is 0 and Sunday is 6;
`0-2` selects Monday through Wednesday. Separate ordinary entries with `;`.
Use `;;` between entries when an entry contains multiple commands:

```text
*:8:0:0!rgb rgb r=10 g=60 b=100; dimmer set_value 40;;*:22:0:0!rgb toggle
```

For boot, timer, cron, and external-IRQ command pipelines, a command beginning
with `#` is skipped. This provides a reversible way to disable an entry.

Instead of a timestamp, use `sunrise` or `sunset` with an optional minute
offset, such as `sunrise+30` or
`sunset!rgb rgb r=10 g=60 b=100`. Times come from
[api.sunrise-sunset.org](https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date=today&formatted=0).
