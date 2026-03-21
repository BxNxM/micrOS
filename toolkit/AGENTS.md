# AGENTS.md — micrOS / DevToolKit

This file is the working guide for AI and coding agents in this repository.

Humans should still read:

- `README.md`
- `micrOS/ARCHITECTURE.md`
- `micrOS/MODULE_GUIDE.md`
- `CONTRIBUTING.md`

Use this file as the operational summary for making safe changes.

---

## 1. First principle: there are two systems in this repo

Do not mix them up.

### A. `micrOS` runtime

Code that runs on the microcontroller itself.

Main location:

- `micrOS/source/`

This is MicroPython-oriented embedded runtime code:

- boot and mode selection
- config-driven runtime assembly
- network bring-up
- async task execution
- shell / web server interfaces
- interrupts, scheduling, and optional feature activation
- `LM_*` load modules
- `IO_*` pin map modules
- built-in web assets under `micrOS/source/web/`

### B. `DevToolKit` host environment

Code that runs on the developer machine under CPython.

Main locations:

- `devToolKit.py`
- `toolkit/`
- `env/`

This is host-side tooling:

- USB deploy / erase / install
- OTA / WebREPL update
- dashboard GUI and test apps
- socket client and gateway
- simulator shims and workspace preparation
- precompile / packaging helpers

If a change is about firmware behavior on the board, start in `micrOS/source/`.
If a change is about install, deploy, dashboard, CLI, gateway, or simulation, start in `toolkit/`.

---

## 2. Repository map by responsibility

### Embedded runtime: authoritative source

- `micrOS/source/main.py`
  - minimal bootstrap, GC enable, handoff to loader
- `micrOS/source/micrOSloader.py`
  - mode selection (`micros`, `webrepl`, `off`)
- `micrOS/source/micrOS.py`
  - runtime assembly: config, hooks, network, IRQs, server, event loop
- `micrOS/source/Config.py`
  - persistent config defaults and type-safe get/put
- `micrOS/source/Tasks.py`
  - async manager, background LM execution, idle task, HA watchdog path
- `micrOS/source/Server.py`
  - socket shell server and optional HTTP serving
- `micrOS/source/Interrupts.py`
  - timer / cron / external IRQ provisioning
- `micrOS/source/Network.py`
  - STA/AP setup, identity, STA repair logic
- `micrOS/source/Hooks.py`
  - boot hooks, profiling, ESP-NOW activation, CPU tuning
- `micrOS/source/Common.py`, `Types.py`, `microIO.py`
  - LM support APIs, widget metadata, pin binding and board lookup
- `micrOS/source/modules/LM_*.py`
  - public load modules callable through ShellCli / WebCli / hooks / IRQs
- `micrOS/source/modules/IO_*.py`
  - board pin maps
- `micrOS/source/web/*`
  - embedded web UI assets served by runtime web server

### Host-side DevToolKit: authoritative source

- `devToolKit.py`
  - main CLI entrypoint and optional dependency bootstrap
- `toolkit/MicrOSDevEnv.py`
  - orchestration entry for deployment and development flows
- `toolkit/DevEnvUSB.py`
  - USB erase / deploy / install / backup flows
- `toolkit/DevEnvOTA.py`
  - OTA / WebREPL update flows
- `toolkit/DevEnvCompile.py`
  - precompile pipeline and workspace generation
- `toolkit/socketClient.py`
  - shell client / device communication
- `toolkit/micrOSdashboard.py`
  - GUI dashboard
- `toolkit/Gateway.py`
  - gateway REST API / multi-node access layer
- `toolkit/dashboard_apps/*`
  - host-run apps that talk to boards
- `toolkit/lib/*`
  - host utilities shared by the toolkit
- `toolkit/simulator_lib/*`
  - MicroPython compatibility shims for simulation

### Generated / mirrored / derived areas

- `toolkit/workspace/precompiled/*`
  - deployment-ready compiled artifacts copied to devices
- `toolkit/workspace/simulator/*`
  - simulator workspace mirror of runtime code
- `toolkit/workspace/webrepl/*`
  - bundled WebREPL assets

Treat these as derived outputs unless the task is specifically about the build pipeline or simulator generation.
Prefer editing the primary source in `micrOS/source/` or `toolkit/` first.

---

## 3. Runtime architecture constraints agents must respect

The runtime is config-first and memory-sensitive.

From `micrOS/ARCHITECTURE.md`, boot flow is effectively:

1. `main.py`
2. `micrOSloader.py`
3. `micrOS.py`
4. config init and pin map selection
5. task manager
6. boot hooks
7. network setup
8. time sync or uptime init
9. IRQ provisioning
10. socket server
11. optional web server
12. optional ESP-NOW
13. event loop forever

Important consequences:

- Do not add heavyweight imports to always-on runtime files casually.
- Many optional features are loaded only when config enables them.
- `LM_*` modules are action-driven and imported lazily on first use.
- Stateful modules remain resident after import by design.
- Config keys are part of runtime behavior, not just docs.

If you change runtime behavior, verify where in boot or lazy-load flow it activates.

---

## 4. Load Module rules

Load Modules are part of the embedded public API.

### Naming and placement

- File name must be `LM_<name>.py`
- Lives in `micrOS/source/modules/`

### Public API shape

- Prefer simple top-level functions
- Functions are callable through shell, REST, hooks, IRQs, and task manager
- Keep command compatibility in mind:
  - shell form: `module function ...`
  - REST form: `/<module>/<function>`

### Design expectations from `MODULE_GUIDE.md`

- `load()` is the preferred initializer when a module needs setup
- Cache hardware objects instead of recreating them repeatedly
- `pinmap()` and `status()` are useful optional helpers
- `help(widgets=False)` should remain accurate
- Use `microIO` for pin reservation / lookup when appropriate
- Use `Common.py` and `Types.py` helpers instead of inventing parallel patterns

### Compatibility rule

Avoid breaking existing LM command names or argument patterns unless explicitly requested.
Prefer additive changes over renames.

---

## 5. DevToolKit rules

Host-side code is normal CPython code, but it serves the runtime and deployment pipeline.

### Keep responsibilities separated

- deploy / install logic belongs in `DevEnvUSB.py`, `DevEnvOTA.py`, `DevEnvCompile.py`
- UI/dashboard logic belongs in `micrOSdashboard.py` or `toolkit/dashboard_apps/`
- device communication belongs in `socketClient.py` and `toolkit/lib/micrOSClient.py`
- gateway behavior belongs in `Gateway.py`

### Avoid these mistakes

- Do not patch generated workspace files when the real fix belongs in source
- Do not treat simulator files as the firmware source of truth
- Do not change CLI flags in `devToolKit.py` without strong reason
- Do not add large optional GUI/audio/image dependencies casually

---

## 6. Simulator and precompiled workspace policy

This repo contains mirrored runtime trees for simulation and deployment.

### Simulator

- `toolkit/simulator_lib/` provides compatibility shims
- `toolkit/workspace/simulator/` mirrors runtime files for local simulation

Use these when the task is specifically about:

- simulation behavior
- simulator-only bugs
- compatibility shims
- generated workspace correctness

Do not fix a firmware bug only in simulator copies.

### Precompiled workspace

- `toolkit/workspace/precompiled/` contains deployable `.mpy` and copied resources

Do not hand-edit precompiled artifacts to implement product behavior.
If behavior changes, update the source and only touch build/precompile code if the artifact generation itself is wrong.

---

## 7. Setup and common commands

### Contributor environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### Install packaged toolkit

```bash
pip3 install --upgrade pip
pip3 install micrOSDevToolKit
```

### Launch GUI

```bash
devToolKit.py
```

### Useful checks

```bash
devToolKit.py -h
devToolKit.py -lint
devToolKit.py --linter
devToolKit.py -sim
```

Do not assume `micrOS/source/` can be executed directly with plain CPython on a host machine.

---

## 8. Testing guidance

### For `micrOS/source/` changes

Minimum:

- run linter: `devToolKit.py -lint`

If applicable:

- run targeted unit tests under `micrOS/utests/`
- test with simulator only if the changed area is simulator-covered
- prefer real hardware verification for IRQ, network, timing, pin, audio, camera, or memory-sensitive behavior

### For `toolkit/` changes

Use the most local check that proves the change:

- `devToolKit.py -h` for CLI changes
- targeted dashboard / gateway / client execution for host-side features
- avoid claiming hardware behavior is verified if only host-side code was tested

Be explicit about what was and was not validated.

---

## 9. Coding constraints

### For embedded runtime files

- optimize for small RAM footprint and predictable behavior
- prefer simple imports and lazy activation
- avoid large temporary allocations
- avoid heavy stdlib assumptions
- preserve async / IRQ / network behavior carefully
- do not casually change config defaults, boot order, or task semantics

### For host-side toolkit files

- keep CLI behavior stable
- keep GUI/dashboard apps focused and composable
- isolate platform-specific code
- prefer readable orchestration over clever abstractions

### For both

- make minimal, local changes
- keep public behavior backward compatible where possible
- update docs when changing architecture, config, or public APIs

---

## 10. Commit and change labeling

Follow `CONTRIBUTING.md` labels:

- `[micrOS][Core]`
- `[micrOS][LoadModule]`
- `[devToolKit][ToolKit]`
- `[devToolKit][dashboard_apps]`
- `[devToolKit][Gateway]`

Examples:

```text
[micrOS][Core] Tighten STA reconnect guard in HA mode
[micrOS][LoadModule] Add status helper to LM_rgbcct
[devToolKit][ToolKit] Fix OTA workspace copy path
[devToolKit][dashboard_apps] Improve RGB test reconnect flow
[devToolKit][Gateway] Harden node discovery error handling
```

Avoid mixing runtime and toolkit changes in one commit unless the feature truly spans both.

---

## 11. Things agents should not do

Do not:

1. Globally reformat the repo
2. Rewrite generated artifacts instead of fixing source
3. Change runtime boot order casually
4. Increase runtime memory requirements without necessity
5. Break LM shell / REST compatibility without calling it out
6. Introduce large new dependencies without strong justification
7. Modify legal / license / policy files unless explicitly asked

For large refactors:

- explain the scope first
- keep runtime and host-side edits clearly separated
- land changes in small, auditable steps

---

## 12. Practical decision checklist

Before editing, answer:

1. Is this running on-device or on the developer machine?
2. Is the source of truth `micrOS/source/`, `toolkit/`, or a derived workspace copy?
3. Does the change affect boot flow, config activation, or LM public API?
4. What is the smallest valid test for this area?
5. Do docs need to change too?

If unsure, prefer the primary source tree, preserve compatibility, and keep the edit narrow.
