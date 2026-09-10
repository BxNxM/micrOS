# Contributing to micrOS

Contributions are welcome across the micrOS runtime and the host-side
DevToolKit. Keep changes focused, use the component labels below in commit
messages, and validate the smallest area that proves the change.

Before editing, identify which source system owns the behavior:

- On-device firmware and Load Modules live under `micrOS/source/`.
- Host-side deployment, dashboard, client, simulator, and gateway code lives
  under `devToolKit.py` and `toolkit/`.
- `toolkit/workspace/` contains generated deployment and simulator artifacts.
  Do not edit those files directly; update the authoritative source or
  generator instead.

For design and public API context, read the
[runtime architecture](./micrOS/ARCHITECTURE.md) and
[Load Module guide](./micrOS/MODULE_GUIDE.md). The project
[README](./README.md#start-using-micros) contains environment setup instructions.

## Change labels and ownership

Start the commit subject with the label for the affected area.

### `[micrOS][Core]`

Applies to the core runtime files in:

```text
micrOS/source/*.py
```

This is the most memory-sensitive and behavior-critical part of the project.
Avoid unnecessary imports, allocations, boot-order changes, or public behavior
breaks.

### `[micrOS][LoadModule]`

Applies to on-device applications and peripheral integrations in:

```text
micrOS/source/modules/LM_*.py
```

Preserve existing shell and REST command names where possible. Keep each
module's `help()` output aligned with its callable functions.

### `[devToolKit][ToolKit]`

Applies to host-side tooling in:

```text
devToolKit.py
toolkit/
toolkit/lib/
```

This includes USB deployment, OTA updates, socket communication, build tools,
and related orchestration.

### `[devToolKit][dashboard_apps]`

Applies to host-run dashboard applications in:

```text
toolkit/dashboard_apps/
```

These applications connect to micrOS nodes for device control, system checks,
and peripheral tests.

### `[devToolKit][Gateway]`

Applies to the multi-node REST gateway and its web resources in:

```text
toolkit/Gateway.py
toolkit/gateway/*.html
```

## Validation

After changing the micrOS core or a Load Module, run the micrOS linter:

```bash
devToolKit.py -lint
# Equivalent long option:
devToolKit.py --linter
```

Run relevant unit tests under `micrOS/utests/` when the changed area is
covered. Hardware-dependent behavior—such as GPIO, IRQs, networking, timing,
audio, and camera handling—should be verified on suitable hardware when
possible. State clearly when validation was limited to linting or simulation.

For DevToolKit changes, start with the most local applicable check:

```bash
devToolKit.py -h
```

Then test the affected deployment, dashboard, client, simulator, or gateway
flow manually as appropriate. Avoid claiming device behavior was verified when
only host-side checks were run.

## Submitting a change

- Keep runtime and host-tool changes separate unless the feature genuinely
  spans both systems.
- Avoid unrelated formatting or generated-file changes.
- Update documentation when changing configuration, architecture, commands, or
  public Load Module APIs.
- Summarize the behavior change and the validation performed in the commit or
  pull-request description.
