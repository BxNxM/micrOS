# ![micrOS logo](./media/logo_mini.png?raw=true) micrOS

A local-first automation platform for Wi-Fi-enabled MicroPython boards.

Build a network-controlled lamp, read a sensor over Socket/HTTP, or let one board trigger another. micrOS turns a compatible Wi-Fi microcontroller into a programmable automation node—without a required cloud service.

Write the hardware behavior in [MicroPython](http://micropython.org); micrOS
handles networking, configuration, background jobs, scheduling, interrupts and updates.

> micrOS is a network-addressable edge application platform for MicroPython MCUs, built around a dynamically loadable plug-in architecture.

[![PyPI Version](https://img.shields.io/pypi/v/micrOSDevToolKit)](https://pypi.org/project/micrOSDevToolKit/)
![GitHub stars](https://img.shields.io/github/stars/BxNxM/micrOS)
[![GitHub Discussions](https://img.shields.io/badge/GitHub-Discussions-green?logo=github&style=flat)](https://github.com/BxNxM/micrOS/discussions)
[![DockerHub](https://img.shields.io/badge/DockerHub-micrOS%20Gateway-blue)](https://hub.docker.com/r/bxnxm/micros-gateway)

## Contents

- 🎬 [See it in action](#see-it-in-action)
- 🚀 [Start using micrOS](#start-using-micros) — installation, Wi-Fi setup, and first commands
- 📦 [Applications](https://htmlpreview.github.io/?https://github.com/BxNxM/micrOS/blob/master/micrOS/client/sfuncman/sfuncman.html) · [micrOS Packages](https://github.com/BxNxM/micrOSPackages)
- 🌐 [Network modes](#networking-modes) · [Configuration reference](./docs/CONFIGURATION_REFERENCE.md)
- 💬 [Tutorials and community](#tutorials-and-community)
- ⚙️ [Advanced use](#advanced-use) — automation, hardware, configuration, and developer tools
- 🧩 [Create a Load Module](./micrOS/MODULE_GUIDE.md) · [Architecture](./micrOS/ARCHITECTURE.md)
- 📚 [Documentation map](#documentation-map)

[![micrOS web interface: REST console, configuration, dashboard, and files](./media/lms/web.png?raw=true)](./media/lms/web.png)

_The on-device web UI: REST console, configuration, application controls, and
file management. It is enabled automatically when the board has enough memory._

## Why micrOS?

- **One function, several ways to use it.** Public functions in `LM_*.py` Load
  Modules are callable from the shell, REST API, schedules, interrupts, and
  background jobs.
- **Local control.** Clients connect directly to nodes over Wi-Fi. No cloud
  account or always-on server is required; time and sunrise/sunset lookups use
  external services.
- **A runtime you can build on.** STA/AP networking, NTP/RTC, pin mapping, async
  tasks, OTA updates, and device-to-device commands are included.
- **Load only what you need.** Modules are imported on demand and stay resident.
  Available memory determines how many you can combine.

## Who is it for?

For MicroPython developers who want reusable device infrastructure, makers
building local automation, hardware experimenters adding sensors or actuators,
and developers connecting several nodes over sockets or ESP-NOW.

## See it in action

| Ring Lamp | RoboArm | RGB + CCT lighting |
| --- | --- | --- |
| [![NeoPixel Ring Lamp controlled by micrOS](./media/projects/RingLamp.gif?raw=true)](https://youtu.be/BlQzAnFtpLk) | ![micrOS-controlled robot arm](./media/projects/RoboArm.gif?raw=true) | ![micrOS RGB and tunable-white controller](./media/projects/RGB_CCT.gif?raw=true) |
| Generated controls for a 24-pixel NeoPixel lamp. | A Wi-Fi-controlled servo application and laser cat toy. | Full-color and tunable-white LED control from one node. |

Start with an existing application, then add your own behavior as a Load Module.

<a id="installing-micros-with-devtoolkit-esp32-and-more"></a>

<a id="quick-start"></a>

## Start using micrOS

You only need three ideas: a **node** is your board running micrOS;
**DevToolKit** installs and connects to it from your computer; a **Load Module**
is a Python application on the board. You don't need to understand the runtime
internals to use an existing application.

Before you begin, have a compatible Wi-Fi MicroPython board, a USB data cable,
a computer, and your Wi-Fi credentials ready. Check the
[firmware catalog](./micrOS/micropython/README.md) for your board; see
[boards and memory](#boards-and-memory) for larger applications.

Follow these four steps to get a node online and make your first request.

Use DevToolKit on macOS, Linux, or Windows to deploy your first node. Start with
the GUI; the CLI supports interactive use and automation.

[![Install micrOS DevToolKit from PyPI](./media/pipy.png)](https://pypi.org/project/micrOSDevToolKit/)

### 1. Install Python and DevToolKit

Install [Python 3.12 or newer](https://www.python.org/downloads/) and add it to
your system path. The original setup used
[Python 3.12.0](https://www.python.org/downloads/release/python-3120/).

On macOS, open Terminal with `Command+Space`, type `terminal`, and press Enter.
On Windows, press `Windows+R`, type `powershell`, and press Enter.

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install micrOSDevToolKit
```

Verify the Python installation with `python3 --version`. Update DevToolKit later
with `python3 -m pip install --upgrade micrOSDevToolKit`.

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install micrOSDevToolKit
```

Activate the environment again when opening a new terminal. If PowerShell
blocks activation, use Command Prompt with `.venv\Scripts\activate.bat`.
On Windows, update with `python -m pip install --upgrade micrOSDevToolKit`.

Run package installation as a normal user; approve administrator access only
if your platform genuinely requires a USB-driver installation. Repository
cloning and `magic.bash` are development workflows documented separately in
the [Load Module and development guide](./micrOS/MODULE_GUIDE.md#develop-from-source).

### 2. Deploy micrOS over USB

Start the graphical toolkit:

```bash
devToolKit.py
```

![micrOS DevToolKit deployment interface](./media/micrOSToolkit.png?raw=true)

> **Warning:** **Deploy (USB)** erases the board's existing firmware and files.
> Back up a board you already use before continuing.

1. Connect your board over USB.
2. Select the matching board and MicroPython firmware from the available lists.
3. Select **Deploy (USB)** and confirm the operation.
4. Wait for deployment to complete and the board to restart.

On first deployment, DevToolKit may offer to install the Serial USB driver
required by your platform. The first toolkit launch installs optional GUI,
compiler, and media dependencies; keep internet access available until it
finishes.

### 3. Configure Wi-Fi and open the web UI

On first startup, an unconfigured node creates its own Wi-Fi access point
when it cannot connect to your network:

1. Connect your computer to the `node01` Wi-Fi network using the
   factory password `ADmin123`.
2. Keep that connection active even if your computer reports that the network
   has no internet access, then open `http://192.168.4.1` in a browser.
3. Select **🚀 Load Web Apps**, then open **Configuration**.
4. In **Device**, set **Device name** to a unique, URL-friendly name such as
   `MyNode`. Under **Startup Actions**, add `web load`. This reloads the
   dashboard and configuration applications automatically after every reboot.
   Preserve any startup actions already present.
5. In **Network**, enter the **WiFi SSID** and **WiFi Password** for your local
   network. The default network mode is `STA`.
6. As a security precaution, replace the factory **Admin Password** in
   **Device**. It must be 8–9 characters long and contain uppercase and
   lowercase letters and a digit.
7. Select **💾 Save**, then **Reboot** when the confirmation dialog appears.

The HTTP server is enabled by default. At boot, micrOS checks the available heap
and disables it automatically if its 80 KiB memory budget cannot be met. The
`web load` startup action registers the dashboard and configuration applications
again at each boot.

After the node restarts, reconnect your computer or phone to the normal local
network and open `http://MyNode.local`. The dashboard and Configuration links
should now be available without selecting **🚀 Load Web Apps** again.

If `.local` does not resolve, use the node IP shown by discovery or your router:
`http://<node-ip>`. The toolkit's default AP address is `192.168.4.1`; another
MicroPython port may use a different address.

If you deploy a previously prepared configuration containing valid Wi-Fi
credentials, the node can join that network directly and the access-point
configuration step is unnecessary. Change the factory device password during
initial setup.

> **Security boundary:** micrOS currently serves HTTP and its socket shell
> without transport encryption, and shell authentication is disabled by
> default. Use nodes only on a trusted local network. Do not expose ports 80 or
> 9008 directly to the internet. Changing `appwd` protects the access point and
> protected operations; it does not add TLS to HTTP or the socket protocol.

<details>
<summary><strong>Advanced: Configuration with Shell</strong></summary>

Use this method when the board cannot host the web UI because of its memory
limit, or when browser-based configuration is unavailable. Start
`devToolKit.py -s -c`, select `__device_on_AP__` at `192.168.4.1`, and enter the
following commands **one line at a time**. Replace the angle-bracket
placeholders, including the brackets, and check that each setting succeeds.

```text
conf
devfid MyNode
staessid <your-wifi-name>
stapwd <your-wifi-password>
appwd <new-device-password>
boothook web load
noconf
reboot
```

If the board does not have enough memory for the web UI, omit
`boothook web load` and continue using ShellCli.

After the reboot, reconnect through DevToolKit and continue with the validation
in step 4.

</details>

### 4. Confirm the installation

![micrOS system intro](./media/micrOS_welcome.png?raw=true)

Open `http://MyNode.local/rest/system/info` to call the first REST endpoint, or connect through DevToolKit and try the shell `devToolKit.py -s -c`:

```text
help
system info
system heartbeat
```

`system info` reports the board, MicroPython version, memory, filesystem, and
uptime. `system ifconfig` reports network mode and addresses. `help all` lists
the installed Load Modules. You can also create a
[custom Load Module](./micrOS/MODULE_GUIDE.md).

The dashboard displays controls for modules with widget metadata, so a fresh node may have few controls until you load an application. Protected configuration operations may prompt for your device password.

### What to try next

Choose a module from the [application catalog](https://htmlpreview.github.io/?https://github.com/BxNxM/micrOS/blob/master/micrOS/client/sfuncman/sfuncman.html),
check its wiring and help, then try its commands. The shell uses
`module function`; HTTP uses `/rest/module/function`, as in the system-info
example above. Module and hardware availability depend on your deployment.

You now have the basics. Keep the
[configuration reference](./docs/CONFIGURATION_REFERENCE.md) nearby for exact
settings and scheduling syntax; continue to Advanced use for custom behavior,
different firmware, or multi-node tooling.

<a id="micros-video-tutorials"></a>

## Tutorials and community

[![YouTube](https://img.shields.io/badge/YouTube-micrOS_framework-red?logo=youtube&logoColor=white)](https://www.youtube.com/channel/UChRlJw7OYAoKroC-Mi75joA)
[![Instagram](https://img.shields.io/badge/Instagram-%40micros_framework-%23E4405F?logo=instagram&logoColor=white)](https://www.instagram.com/micros_framework/)
[![Facebook](https://img.shields.io/badge/Facebook-micrOS_framework-%231877F2?logo=facebook&logoColor=white)](https://www.facebook.com/Micros-Framework-103501302140755)
[![Thingiverse](https://img.shields.io/badge/Thingiverse-micrOS_3Dprints-%231489FF?logo=thingiverse&logoColor=white)](https://www.thingiverse.com/micros_framework/designs)

[![micrOS video tutorials](./media/YoutubeChannel.png)](https://www.youtube.com/channel/UChRlJw7OYAoKroC-Mi75joA)

Questions, ideas, and technical requests are welcome in
[GitHub Discussions](https://github.com/BxNxM/micrOS/discussions). If micrOS is
useful to you, a GitHub star helps other MicroPython and embedded-automation
developers find it.


---

<a id="networking-modes"></a>

<a id="how-it-works"></a>

## Networking modes

![micrOS station, access-point, and local-network modes](./media/micrOSNetworking.png?raw=true)

A node normally joins the local Wi-Fi network in station mode. It can fall back
to its own access point for configuration. Clients communicate directly with a
node; nodes can invoke each other over sockets or ESP-NOW. The complete behavior
and parameter definitions are in the
[configuration and automation reference](./docs/CONFIGURATION_REFERENCE.md).


<a id="micros-node-configuration-parameters-with-description"></a>

## Node configuration reference

For routine setup, open `http://<nodename>.local/config`. The settings most new
users need are:

| Setting | Purpose |
| --- | --- |
| `devfid` | Node name, AP name, DHCP hostname, and shell prompt after restart. |
| `staessid`, `stapwd` | Local Wi-Fi network credentials. Multiple networks use `;`-separated values. |
| `appwd` | Shared password for the AP, protected operations, and optional shell authentication. Replace the factory value. |
| `boothook` | Startup commands such as `web load; rgb load`. Preserve existing commands when adding one. |
| `nwmd` | Preferred station (`STA`) or access-point (`AP`) mode. |

The [complete configuration and automation reference](./docs/CONFIGURATION_REFERENCE.md)
documents every key, default, type, reboot requirement, authentication behavior,
and scheduling syntax.


---

## Advanced use

![Animated micrOS system and message-function visualization](./media/micrOS.gif?raw=true)

Use this section as a reference, not a second setup checklist. It covers
operating and extending your nodes. Runtime design belongs in
[ARCHITECTURE.md](./micrOS/ARCHITECTURE.md); application APIs and examples belong
in [MODULE_GUIDE.md](./micrOS/MODULE_GUIDE.md).

- [Interfaces and applications](#interfaces-and-applications)
- [Automation commands](#configure-automation)
- [Boards and memory](#boards-and-memory) · [Peripherals](#built-in-peripheral-support) · [Pinouts](#device-pinouts-for-wiring)
- [Gateway and monitoring](#gateway-and-monitoring)
- [Development, customization, and shell usage](./micrOS/MODULE_GUIDE.md#development-and-customization)
- [Documentation](#documentation-map)
- [Roadmap](#roadmap) · [Release history](#release-history)

<a id="micros-clients"></a>

### Interfaces and applications

| Interface | Purpose |
| --- | --- |
| **On-device web UI** | Configuration, generated dashboards, REST tools, and file management at `http://<nodename>.local`. |
| **WebCli / REST** | Exposes MicroPython module functions through HTTP endpoints. |
| **ShellCli** | Provides a generic, session-based TCP/IP operation and management (OAM) interface with a telnet-style shell. |
| **DevToolKit** | Deploys, updates, discovers, monitors, and simulates nodes. |
| **InterCon** | Executes commands between nodes over sockets or ESP-NOW. |

Load Modules are micrOS applications. Use the catalog to find one for your
hardware, or follow the development guide to write your own.

- [Browse the built-in application and peripheral catalog](https://htmlpreview.github.io/?https://github.com/BxNxM/micrOS/blob/master/micrOS/client/sfuncman/sfuncman.html)
- [Create a custom Load Module](./micrOS/MODULE_GUIDE.md)
- [Install shared micrOS packages](https://github.com/BxNxM/micrOSPackages)
- [Use the micrOS Gateway](./env/docker/README.md)
- AI integration: [![DockerHub micrOS MCP](https://img.shields.io/badge/DockerHub-micrOS%20MCP-blue)](https://hub.docker.com/r/bxnxm/micros-mcp)

#### Optional file manager

Run `web load fileserver=True` in the shell. To make it persistent, add the
command to `boothook` while preserving existing startup actions. See the
[configuration reference](./docs/CONFIGURATION_REFERENCE.md#startup-actions-and-web-applications)
for details and security behavior.

<a id="complete-guide-and-reference"></a>
<a id="micros-framework-features"></a>

<a id="detailed-runtime-capabilities"></a>

### Configure automation

<a id="boot-configuration-and-networking"></a>

#### Startup and network settings

Use the Configuration app for routine changes. `boothook` can initialize the
web applications and hardware modules in sequence, for example:

```text
web load; rgb load; neopixel load
```

Preserve existing actions when adding another one. ShellCli remains the fallback
when the web UI is unavailable.

#### Schedules and external events

| Mechanism | Configuration and example |
| --- | --- |
| Periodic timer | Enable `timirq`; set `timirqseq` in milliseconds and `timirqcbf` to a command. With `5000` and `bme280 measure`, Timer(0) measures every five seconds. Callbacks support `#` comments. |
| Cron | Enable `cron` and set `crontasks`. Timer(1) runs timestamped entries such as `*:8:0:0!rgb rgb r=10 g=60 b=100` (daily at 08:00). |
| External interrupt | Enable `irqX` (X = 1–4), choose `irqX_trig` (`up`, `down`, or `both`), and set `irqX_cbf` to a Load Module callback. Callbacks support `#` comments. |

The [complete automation reference](./docs/CONFIGURATION_REFERENCE.md#schedules-and-external-events)
covers cron fields and ranges, multi-command separators, comments,
sunrise/sunset offsets, timer dependencies, and IRQ configuration.

### Hardware and peripherals

#### Boards and memory

micrOS targets compatible MicroPython boards with Wi-Fi, not one chip family or
manufacturer. Included mappings cover multiple Espressif boards as well as
RP2/Pico W and provider-specific boards such as TinyPICO, M5Stamp, and QT Py.
Deployment method and peripheral availability vary by MicroPython port. A pin
map alone does not guarantee compatibility: check the
[firmware catalog](./micrOS/micropython/README.md) and each module's requirements.
The full web UI plus several modules generally needs more than 150–200 KB of
available RAM; PSRAM-capable boards are preferable for larger combinations,
camera, or audio workloads. See the
[hardware and memory guide](./docs/HARDWARE_GUIDE.md) for board examples,
historical measurements, and port-specific caveats.

---

#### Built-in peripheral support

Sensors, inputs, actuators, and outputs are documented in the generated Load
Module catalog. The
[hardware guide](./docs/HARDWARE_GUIDE.md#built-in-peripheral-support) links to
that catalog and records the related wiring and memory caveats.

---

#### Device pinouts for wiring

`microIO` maps logical application pins through `IO_*.py` board definitions.
Inspect the active mapping with `system pinmap`; individual pins can be
overridden through `cstmpmap`. The [hardware guide](./docs/HARDWARE_GUIDE.md#logical-pin-association)
contains the complete mapping list, override syntax, OTA caveat, and wiring
illustrations.

---

<a id="micros-gateway-in-docker"></a>

### Gateway and monitoring

![MICROSVISUALIZATION](./media/micrOS_gateway.png?raw=true)

The optional Gateway provides multi-node access and can feed Prometheus metrics
to Grafana dashboards. The [Docker setup guide](./env/docker/README.md) contains
the compose command, scraper configuration, dashboard examples, standalone
container options, and the official
[DockerHub image](https://hub.docker.com/r/bxnxm/micros-gateway).

### Roadmap

Proposed low-power, secure-transport, wired InterCon, and compose-based deployment
work is preserved in [Project roadmap and release history](./docs/PROJECT_HISTORY.md#roadmap-proposals).
These are proposals rather than committed release promises.

<a id="release-note"></a>
### Release history

The complete historical milestone table, memory figures, release-note links,
legacy-client references, and development metrics are in
[Project roadmap and release history](./docs/PROJECT_HISTORY.md#historical-release-milestones).
It is explicitly labeled historical so it is not mistaken for the current
firmware compatibility matrix.

---

### Documentation map

- [Configuration and automation reference](./docs/CONFIGURATION_REFERENCE.md)
- [Hardware, memory, and pin-map guide](./docs/HARDWARE_GUIDE.md)
- [Architecture](./micrOS/ARCHITECTURE.md)
- [Development, shell usage, and Load Modules](./micrOS/MODULE_GUIDE.md)
- [MicroPython images](./micrOS/micropython/README.md)
- [Gateway deployment](./env/docker/README.md)
- [Project roadmap and release history](./docs/PROJECT_HISTORY.md)
- [Business vision](./docs/BUSINESS_VISION.md)
- [Contributing](./CONTRIBUTING.md)
- [Maintainer operations](./docs/MAINTAINER_OPERATIONS.md)

<a id="hints"></a>
<a id="operations-and-maintainer-notes"></a>


git push -u origin master
