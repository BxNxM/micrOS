# Project roadmap and release history

This page preserves roadmap proposals and historical release information that
previously lived in the project README. Roadmap entries are ideas, not committed
release promises. The release table is a historical milestone index and does
not describe the complete current compatibility matrix.

For current source and package versions, consult the repository, release tags,
and [PyPI package page](https://pypi.org/project/micrOSDevToolKit/). For current
firmware targets, use the [firmware catalog](../micrOS/micropython/README.md).

## Roadmap proposals

### `micrOS-Waterbear` — proposed 3.X line

- Low-power mode with wake-on-event and hibernation commands.
- Battery-powered remote-control and sensor use cases.

### `micrOS-SecurePower` — proposed later line

- Async socket servers with SSL/TLS and authentication.
  - ShellCli over TLS and InterCon adaptation; the historical proposal suggested
    retaining port 9008 and adding secure port 9009.
  - HTTPS support for WebCli and the web UI.
- A possible wired InterCon transport over I2C, OneWire, or UART, supporting
  bidirectional messages and easier Arduino/co-processor integration.
- Application-deployment automation based on `/config/compose.json`:
  - safe `node_config.json` injection for boot hooks and interrupts;
  - requirements handling, which the original roadmap already marked complete;
  - automatic behavior when the file exists in STA mode.

## Historical release milestones

[Development metrics](../toolkit/helper_scripts/analysis/timeline_visualization.pdf)

| Version | Release information | Historical core memory | Devices recorded at release | App profiles | Load Module reference | Historical note |
| --- | --- | --- | --- | --- | --- | --- |
| **v0.1.0-0** | [Release note](../micrOS/release_info/micrOS_ReleaseInfo/release_0.1.0-0_note.md) | 78.4%, 29,776 bytes | ESP8266 | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](https://github.com/BxNxM/micrOS/blob/a4625c7c80906bce2ddb6c47a60c2efd88f6a7e1/micrOS/client/sfuncman/sfuncman_0.1.0-0.json) | Stable core with applications; first release. |
| **v0.4.0-0** | [ESP8266 release note](../micrOS/release_info/micrOS_ReleaseInfo/release_0.4.0-0_note_esp8266.md) | 81.0%, 30,768 bytes | ESP8266 | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](https://github.com/BxNxM/micrOS/blob/a4625c7c80906bce2ddb6c47a60c2efd88f6a7e1/micrOS/client/sfuncman/sfuncman_0.4.0-0.json) | Multi-device support, finalized core, and OTA updates. |
| **v0.4.0-0** | [ESP32 release note](../micrOS/release_info/micrOS_ReleaseInfo/release_0.4.0-0_note_esp32.md) | 47.1%, 52,416 bytes | ESP32 | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](https://github.com/BxNxM/micrOS/blob/a4625c7c80906bce2ddb6c47a60c2efd88f6a7e1/micrOS/client/sfuncman/sfuncman_0.4.0-0.json) | Multi-device support, advanced task scheduling, and OTA updates. |
| **v1.0.0-0** | [Release note](../micrOS/release_info/micrOS_ReleaseInfo/release_1.0.0-0_note_esp32.md) | 47.9%, 53,280 bytes | ESP32 | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](https://github.com/BxNxM/micrOS/blob/a4625c7c80906bce2ddb6c47a60c2efd88f6a7e1/micrOS/client/sfuncman/sfuncman_1.0.0-0.json) | v1 release with timer/event IRQs, cron, real-time communication, multiple-device support, and OTA. |
| **v1.2.2-0** | [Release note](../micrOS/release_info/micrOS_ReleaseInfo/release_1.2.2-0_note_esp32.md) | 48.6%, 54,032 bytes | ESP32 | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](https://github.com/BxNxM/micrOS/blob/a4625c7c80906bce2ddb6c47a60c2efd88f6a7e1/micrOS/client/sfuncman/sfuncman_1.2.2-0.json) | Public v1 release with scheduling, real-time communication, multi-device support, OTA, and beta socket-shell threading. |
| **light-1.3.0-0** | [Lightweight branch](https://github.com/BxNxM/micrOS/tree/lightweight) | — | ESP8266 | — | — | ESP8266 left the main branch because of memory limits but remained available with reduced functionality on the lightweight branch. The historical workflow was to select that branch, download it, and start the DevToolKit dashboard. |
| **v1.5.0-1** | [Release note](../micrOS/release_info/micrOS_ReleaseInfo/release_1.5.0-1_note_esp32.md) | 58.2%, 64,704 bytes | ESP32 / TinyPICO | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](https://github.com/BxNxM/micrOS/blob/9d5dc0ffd34f85d05e1cb149cc8abe280fd02bd9/micrOS/client/sfuncman/sfuncman_1.5.0-1.json) | Advanced timer scheduling, geolocation timing, four external IRQ channels, lighting controls, and device-to-device communication. |
| **v1.21.0-4** | [Release note](../micrOS/release_info/micrOS_ReleaseInfo/release_1.21.0-4_note_esp32.md) | 57.3%, 63,728 bytes | ESP32, TinyPICO, ESP32-S2, ESP32-S3 | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](https://github.com/BxNxM/micrOS/blob/c9a69814f32ab32d96c447c3e40e880df32bddd6/micrOS/client/sfuncman/sfuncman_1.21.0-4.json) | Full asynchronous core, task management, device communication, scheduling, and more than 30 applications and peripherals. |
| **v2.0.0-0** | [Release note](../micrOS/release_info/micrOS_ReleaseInfo/release_2.0.0-0_note_esp32.md) | 45.4%, 68.7 KB | ESP32, TinyPICO, ESP32-S2, ESP32-S3 | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](../micrOS/client/sfuncman/sfuncman_2.0.0-0.json) | Optimizations, WebCli frontends, and camera support on MicroPython 1.21. |
| **v2.6.0-0** | [Release note](../micrOS/release_info/micrOS_ReleaseInfo/release_2.6.0-0_note_esp32.md) | 48.3%, 72.6 KB | ESP32, TinyPICO, ESP32-S2, ESP32-S3 | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](../micrOS/client/sfuncman/sfuncman_2.6.0-0.json) | WebCli enhancements, dashboard web app, and finalized Load Module interfaces in `Common.py`, `Types.py`, and `microIO.py`. |
| **v3.0.0-0** | [Release note](../micrOS/release_info/micrOS_ReleaseInfo/release_3.0.0-0_note_esp32.md) | 66.0%, 95.5 KB | ESP32, TinyPICO, ESP32-C6, ESP32-S3 with PSRAM, and others | [Profiles](../micrOS/release_info/node_config_profiles/) | [LM manual](../micrOS/client/sfuncman/sfuncman_3.0.0-0.json) | Minimum recorded RAM requirement of 200 KB; standalone micrOS with multi-layer resource separation and package management. [More details](https://github.com/BxNxM/micrOS/discussions/55). |

## Legacy mobile clients

The original iOS and Android applications were replaced by the on-device web
UI. Their store listings returned 404 when checked on September 7, 2026. These
links are retained solely as historical references:

[![Former micrOS iOS client](../media/store/AppStoreBadge.svg)](https://apps.apple.com/hu/app/micros-client/id1562342296)
[![Former micrOS Android client](../media/store/GooglePlayBadge.png)](https://play.google.com/store/apps/details?id=com.BMT.micrOSClient)
