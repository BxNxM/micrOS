# AGENTS.md — micrOS

This file is for AI / coding agents working on **micrOS – mini asynchronous automation OS for DIY projects**.

Humans: see `README.md`, `APPLICATION_GUIDE.md`, `BUSINESS_VISION.md`, and `CONTRIBUTING.md` first. Agents should read those too, but use THIS file as the primary operational guide.

---

## 1. Project map (for agents)

High level layout:

- `micrOS/source/`
  - **Core framework**: all files **without** `LM_` prefix → `[micrOS][Core]`
  - **Load Modules**: files **with** `LM_` prefix → `[micrOS][LoadModule]`
- `toolkit/`
  - DevToolKit GUI + CLI, deployment logic, OTA support, Gateway, dashboard apps, etc.
- `env/`, `media/`, top-level files
  - Packaging, assets, docs, scripts (`devToolKit.py`, `magic.bash`, `setup.py`, etc.)
- `source ./magic.bash env`, create/load test virtualenv
- `./devToolKit.py -h`, micrOS development environment command line tools

**Golden rule:**  
If the code runs **on the microcontroller**, it's almost always inside `micrOS/source/`.  
If it runs on the **developer's computer**, it's in `toolkit/`.

---

## 2. Environment & setup commands

Agents should propose or use these commands when guiding developers:

### Install DevToolKit pip package (not for development, but for verification):

```bash
pip3 install --upgrade pip
pip3 install micrOSDevToolKit
```

### Launch DevToolKit GUI:

```bash
devToolKit.py
```

### Local editable install for contributors:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install micrOSDevToolKit
```

**Do NOT** assume MicroPython code can be run under CPython. Anything inside `micrOS/source/` targets real boards.

---

## 3. Tests & checks

### micrOS linter (primary automated check):

```bash
devToolKit.py -lint
# or
devToolKit.py --linter
```

### Manual / hardware-in-the-loop testing:

- Use `toolkit/dashboard_apps` with a real board when possible
- Avoid assuming full hardware emulation exists
- If hardware is unavailable:
  1. Run linter  
  2. Keep logic isolated  
  3. Only unit-test pure-Python helpers  

---

## 4. Coding conventions & constraints

### 4.1 MicroPython-friendly coding

For all files under `micrOS/source/`:

- Avoid heavy stdlib modules and dynamic imports
- Avoid large memory allocations
- Keep recursion shallow
- Keep code minimal and predictable — micrOS targets low-RAM boards

### 4.2 Load Modules (`LM_*.py`)

- Naming: `LM_<Name>.py`
- Public API: simple top-level functions callable from ShellCli and WebCli
- Maintain backward compatibility for:
  - CLI commands (`system info`, `rgb rgb ...`, etc.)
  - REST-like WebCli paths (`/<module>/<function>`)

If breaking a public API is unavoidable:

1. Prefer adding a new function instead
2. Update docs and dashboard metadata accordingly

### 4.3 Toolkit (`toolkit/`)

- Preserve CLI flags of `devToolKit.py`
- Keep dashboard apps small and composable
- Avoid adding large GUI dependencies

---

## 5. Commit messages & structure

Follow the tagging format defined in `CONTRIBUTING.md`:

Examples:

```text
[micrOS][Core] Fix scheduler edge case
[micrOS][LoadModule] Add LM_envSensor module
[devToolKit][ToolKit] Improve OTA uploader retry
[devToolKit][dashboard_apps] Add LED matrix controller
[devToolKit][Gateway] Fix device reconnect logic
```

Guidelines:

- Group related changes together
- Avoid monolithic commits touching both microcontroller code and toolkit unless necessary

---

## 6. Things agents should NOT do

Agents must avoid:

1. Global reformatting or replacing code style project-wide
2. Editing `LICENSE`, `CODE_OF_CONDUCT.md`, or legal text
3. Recreating binary files or assets unless explicitly asked
4. Increasing board hardware requirements casually
5. Removing low-level optimizations (async loops, IRQs, networking internals) without explicit design intent
6. Introducing large new dependencies

For big refactors:

- Propose the plan first (in natural language)
- Execute changes in small, clearly scoped steps

---

## 7. How agents should operate in this repository

When modifying or generating code:

1. Identify the target area:
   - `micrOS/source/` → MicroPython core or Load Modules
   - `toolkit/` → host-side tools
2. Apply correct coding constraints (MicroPython vs CPython)
3. Maintain backward compatibility
4. Run or recommend running the linter
5. Comment code when altering behavior

Agents should always prefer:

- Minimal, safe, reversible edits  
- Clear commit messages  
- High stability for embedded runtime code  

---

## 8. Final notes for agents

This file defines how automated coding agents should behave inside micrOS.

If in doubt:

- Make small changes  
- Respect existing architecture  
- Ask for clarification or propose design options instead of guessing
