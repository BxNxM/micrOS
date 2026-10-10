# micrOS authentication report

This report describes authentication in the current repository source, reviewed
on 2026-10-10. It covers on-device interfaces and the optional Telegram and MQTT
packages. It does not describe authentication added by an external gateway or
broker. Findings come from source inspection, without hardware verification.

## Configuration and protection layers

The `auth` configuration flag defaults to `False`. It controls TCP shell login
and module autoload restrictions on REST and ESP-NOW. It is not a global switch
for every password check.

Three mechanisms operate separately:

- **Shell session login:** when `auth=True`, the TCP shell checks `appwd` before
  accepting commands, except for public device identification through `hello`.
- **Module loading restrictions:** some interfaces allow commands only for
  already-loaded Load Modules. This checks module residency, not caller identity.
- **Function protection with `@sudo`:** decorated functions check an explicit
  `pwd` argument against `appwd`, independently of the `auth` flag.

An already-loaded module is resident in the runtime. Modules are normally
imported on first use and remain loaded. Consequently, an autoload restriction
does not prevent access to unprotected functions once their module is loaded.

## Interface comparison

| Interface | `auth=False` | `auth=True` |
| --- | --- | --- |
| Local Python / USB REPL | No micrOS login gate; direct execution can import modules. | Same. The flag does not protect local REPL access. |
| TCP shell | Commands run without session login and can load modules. | Requires `appwd` once per session. Wrong password closes the session. `hello` remains public. After login, commands can load modules. |
| REST `GET /rest/...` | Commands can automatically load modules. | Commands execute only for already-loaded modules. Unloaded modules return `Auth:Protected`. There is no password login or HTTP authentication retry on this route. |
| Callable web endpoints | Callbacks protected by `@sudo` require `appwd`; undecorated callbacks have no automatic password gate. | Same. Protection is selected by the callback, independently of `auth`. |
| Static web pages and assets | Public. | Public, including the config page itself. Its protected API callbacks still require credentials. |
| WebREPL / OTA file transfer | WebREPL requires `appwd`. | Same. WebREPL password authentication is independent of `auth`. |
| ESP-NOW commands | Commands can automatically load modules. | Commands execute only for already-loaded modules; other modules return `NotAllowed`. `hello` remains public. There is no shell-style password login. |
| Telegram commands | Only already-loaded modules can execute. | Same. The shared executor defaults to `secure=True`; Telegram has no micrOS session login. |
| Async MQTT package | Commands can automatically load modules through `secure=False`. | Same. The command executor does not apply the `auth` module-loading gate. Broker credentials are separate. |
| SIM800 MQTT package | Commands can automatically load modules through `secure=False`. | Same. Broker credentials are separate from `appwd`. |
| Internal hooks, schedules, IRQ commands and tasks | Internal command execution has no shell session login gate. | Same. Function-level `@sudo` checks still apply when a decorated function executes. |

All rows remain subject to `@sudo` when the invoked function is decorated.
Interface availability also depends on configuration, installed packages and
runtime initialization.

## Function-level protection: `@sudo`

`@sudo` checks `pwd` against the configured `appwd` and raises `AuthRequired`
when the password is missing or incorrect. It removes the `pwd` argument before
calling the protected function.

- The check applies with both `auth=False` and `auth=True`.
- A successful TCP shell login does not automatically satisfy `@sudo`.
- Direct local Python calls also need `pwd` when invoking decorated functions.
- Conditional protection, such as `@sudo(_when_true=("force", 1))`, requires the
  password only when the specified option is truthy.
- The credential checked by the runtime is `appwd`; username validation is not
  implemented by this shared password check.

For example, the shell test function can be invoked as:

```text
robustness func_sudo pwd='<appwd>'
```

Boot hooks can use `pwd=$pwd`; the boot-hook secret resolver substitutes the
configured password before command execution.

## Web authentication flow

Callable registered endpoints use the HTTP adapter for `@sudo`:

1. The endpoint callback executes.
2. If it raises `AuthRequired`, WebEngine retries with the password from the
   `x-micros-auth` header when that header is present.
3. If authentication is still required, the client receives an HTTP `401`
   challenge.
4. Browser clients using `auth.js` can enter the password and retry the request.
   Non-interactive clients can supply `x-micros-auth: <appwd>`.

The browser helper keeps credentials in memory and sends them only to the same
origin. Static file responses and `/rest/...` do not use this HTTP retry flow.
Supplying `x-micros-auth` to REST does not override its loaded-module gate.

## Telegram and MQTT credentials

Telegram uses a bot token to communicate with the Telegram service. Its command
path calls `Notify.lm_execute()` with the default `secure=True`, which blocks
autoload of unloaded modules regardless of `auth`. This restriction does not
authenticate a command sender with `appwd`.

Both MQTT packages explicitly call `Notify.lm_execute(..., secure=False)`.
Their broker username and password configure broker access; they do not enable
the micrOS shell login or REST module-loading restrictions. Protected functions
still require their `pwd` argument.

## Configuration activation

The TCP shell captures `auth` when its shell instance is initialized. WebEngine
captures it when its class is loaded, and ESP-NOW captures it when its instance
is initialized. Do not assume editing `auth` immediately updates every active
interface; restart the device to apply the setting consistently.

## Source references

| Source | Behavior covered |
| --- | --- |
| [Config.py](../micrOS/source/Config.py) | `auth=False` default and `appwd` configuration |
| [Auth.py](../micrOS/source/Auth.py) | Password validation, `@sudo`, conditional protection and boot-hook secret resolution |
| [Shell.py](../micrOS/source/Shell.py) | Session login, public `hello` and WebREPL startup |
| [Web.py](../micrOS/source/Web.py) | REST module gate, static routing and callback authentication |
| [Tasks.py](../micrOS/source/Tasks.py) | Shared Load Module execution |
| [Hooks.py](../micrOS/source/Hooks.py) | Boot-hook password substitution |
| [mespnow.py](../micrOS/source/mespnow.py) | ESP-NOW command module gate |
| [Notify.py](../micrOS/source/Notify.py) | Shared notification command executor and `secure` option |
| [LM_telegram.py](../micrOS/source/modules/LM_telegram.py) | Telegram command dispatch |
| [LM_mqtt_client.py](../micrOS/packages/async_mqtt/package/LM_mqtt_client.py) | Async MQTT command dispatch with `secure=False` |
| [LM_sim800mqtt.py](../micrOS/packages/sim800/package/LM_sim800mqtt.py) | SIM800 MQTT command dispatch with `secure=False` |
| [Runtime architecture](../micrOS/ARCHITECTURE.md#runtime-web-authentication) | Web authentication design and route distinctions |
