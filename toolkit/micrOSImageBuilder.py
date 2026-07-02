#!/usr/bin/env python3
"""
Build a MicroPython firmware image with the micrOS core frozen into it.

All Python files directly inside ``micrOS/source`` are frozen as core modules.
Configured web assets and allowed load modules are left to the normal
post-flash resource copier.

The direct source set includes ``main.py``. MicroPython's ESP32 startup checks
for a frozen ``main.py`` before checking the writable filesystem, so micrOS
starts directly from the firmware image.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from time import monotonic


class BuildError(RuntimeError):
    """Raised when the image cannot be built safely."""


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IMAGE_CONFIG = REPOSITORY_ROOT / "toolkit" / "micrOSImageConfig.json"
MICROS_FIRMWARE_MARKER = "[micrOS]"
WORKSPACE_BUILD_DIR = REPOSITORY_ROOT / "toolkit" / "workspace" / "build"
DEFAULT_BUILD_DIR = WORKSPACE_BUILD_DIR / "micrOSImageBuilder"
DEFAULT_MICROPYTHON_DIR = WORKSPACE_BUILD_DIR / "micropython"
DEFAULT_ESP_IDF_DIR = WORKSPACE_BUILD_DIR / "esp-idf"
DEFAULT_IDF_TOOLS_DIR = WORKSPACE_BUILD_DIR / "esp-idf-tools"


def _load_config_file(config_path):
    try:
        return json.loads(Path(config_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BuildError("Cannot load image configuration: {}".format(config_path)) from exc


def _repository_path(relative_path):
    return (REPOSITORY_ROOT / relative_path).resolve()


DEFAULT_IMAGE_SETTINGS = _load_config_file(DEFAULT_IMAGE_CONFIG)
BUILD_SETTINGS = DEFAULT_IMAGE_SETTINGS["build"]
MICROS_SOURCE = _repository_path(BUILD_SETTINGS["core_source"])
DEFAULT_OUTPUT_DIR = _repository_path(BUILD_SETTINGS["output_directory"])
MICROPYTHON_REPOSITORY = BUILD_SETTINGS["micropython"]["repository"]
ESP_IDF_REPOSITORY = BUILD_SETTINGS["esp_idf"]["repository"]
MICROPYTHON_STABLE_VERSION = BUILD_SETTINGS["micropython"]["version"]
ESP_IDF_VERSION = BUILD_SETTINGS["esp_idf"]["version"]
OUTPUT_FILENAME_TEMPLATE = BUILD_SETTINGS["output_filename"]
SUPPORTED_DEVICES = DEFAULT_IMAGE_SETTINGS["supported_devices"]


def log(level, message):
    """Emit a consistent, grep-friendly build message."""
    print("[micrOS-image][{}] {}".format(level.upper(), message), flush=True)


def log_step(number, total, message):
    log("STEP {}/{}".format(number, total), message)


def micros_version(source_dir=MICROS_SOURCE):
    """Read the micrOS release version without importing embedded modules."""
    shell_path = Path(source_dir) / "Shell.py"
    try:
        shell_source = shell_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError("Cannot read micrOS version from: {}".format(shell_path)) from exc

    match = re.search(
        r"^\s*MICROS_VERSION\s*=\s*['\"]([^'\"]+)['\"]",
        shell_source,
        flags=re.MULTILINE,
    )
    if not match:
        raise BuildError("MICROS_VERSION was not found in: {}".format(shell_path))
    return match.group(1)


def core_source_files(source_dir=MICROS_SOURCE):
    """Return only direct ``source/*.py`` files, in deterministic order."""
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        raise BuildError("micrOS source directory does not exist: {}".format(source_dir))

    files = sorted(
        path.name
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix == ".py"
    )
    if not files:
        raise BuildError("No micrOS core Python files found in: {}".format(source_dir))
    if "main.py" not in files:
        raise BuildError("micrOS/source/main.py is required for firmware startup")
    return files


def configured_module_files(profile, platform):
    """Return validated module names selected for post-flash copying."""
    modules = profile["modules"]
    if modules.get("delivery") != "copy":
        raise BuildError("Image modules must use delivery='copy'")
    module_source_dir = _configured_source(modules["source"])
    files = []
    for configured_name in modules["include"]:
        module_name = configured_name.format(platform=platform)
        module_path = Path(module_name)
        if module_path.name != module_name:
            raise BuildError("Image module entries must be filenames: {}".format(module_name))
        if module_path.suffix not in ("", ".py", ".mpy"):
            raise BuildError("Unsupported image module extension: {}".format(module_name))
        module_stem = module_path.stem if module_path.suffix else module_name
        source = module_source_dir / "{}.py".format(module_stem)
        if not source.is_file():
            raise BuildError("Configured image module is missing: {}".format(source))
        files.append(module_stem)
    return module_source_dir, files


def prepare_custom_board(micropython_dir, build_dir, device):
    """Create a generated board overlay carrying the micrOS runtime marker."""
    board = device["micropython_board"]

    source_board_dir = Path(micropython_dir) / "ports" / "esp32" / "boards" / board
    if not source_board_dir.is_dir():
        raise BuildError("MicroPython board directory is missing: {}".format(source_board_dir))

    custom_board_dir = Path(build_dir) / "boards" / device["platform"]
    if custom_board_dir.exists():
        shutil.rmtree(str(custom_board_dir))
    custom_board_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(source_board_dir), str(custom_board_dir))

    board_header = custom_board_dir / "mpconfigboard.h"
    try:
        header_text = board_header.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError("Cannot read MicroPython board header: {}".format(board_header)) from exc

    board_name_match = re.search(
        r'^\s*#define\s+MICROPY_HW_BOARD_NAME\s+"([^"]*)"',
        header_text,
        flags=re.MULTILINE,
    )
    if board_name_match is None:
        raise BuildError("MICROPY_HW_BOARD_NAME was not found in: {}".format(board_header))
    board_name = board_name_match.group(1)
    runtime_mcu_name = []

    def add_micros_marker(match):
        mcu_name = match.group(2)
        if MICROS_FIRMWARE_MARKER not in mcu_name:
            mcu_name = "{} {}".format(mcu_name, MICROS_FIRMWARE_MARKER)
        runtime_mcu_name.append(mcu_name)
        return "{}{}{}".format(match.group(1), json.dumps(mcu_name), match.group(3))

    header_text, replacements = re.subn(
        r'^(\s*#define\s+MICROPY_HW_MCU_NAME\s+)"([^"]*)"(.*)$',
        add_micros_marker,
        header_text,
        count=1,
        flags=re.MULTILINE,
    )
    if replacements != 1:
        raise BuildError("MICROPY_HW_MCU_NAME was not found in: {}".format(board_header))
    board_header.write_text(header_text, encoding="utf-8")
    log("IDENTITY", "Custom firmware key: {}".format(MICROS_FIRMWARE_MARKER))
    log(
        "IDENTITY",
        "Runtime machine: {} with {}".format(board_name, runtime_mcu_name[0]),
    )
    return custom_board_dir


def manifest_text(source_dir=MICROS_SOURCE):
    """Create the core-only MicroPython frozen-module manifest."""
    source_dir = Path(source_dir).resolve()
    files = core_source_files(source_dir)
    file_lines = "\n".join('        "{}",'.format(name) for name in files)
    return """# Generated by toolkit/micrOSImageBuilder.py; do not edit.
# Minimal ESP32 runtime support. Keep MicroPython's espnow.py and aioespnow
# because micrOS mespnow.py builds its async integration on top of them.
# Deliberately do not freeze micropython-lib's urequests.py because micrOS owns
# that module.
module("_boot.py", base_path="$(PORT_DIR)/modules")
module("apa106.py", base_path="$(PORT_DIR)/modules")
module("espnow.py", base_path="$(PORT_DIR)/modules")
module("flashbdev.py", base_path="$(PORT_DIR)/modules")
module("inisetup.py", base_path="$(PORT_DIR)/modules")
module("machine.py", base_path="$(PORT_DIR)/modules")

include("$(MPY_DIR)/extmod/asyncio")
require("aioespnow")
require("mip")
require("ntptime")
require("requests")
require("ssl")
require("webrepl")

# Freeze only direct micrOS/source/*.py core files.
freeze(
    {source_dir!r},
    (
{file_lines}
    ),
    opt=3,
)
""".format(
        source_dir=str(source_dir),
        file_lines=file_lines,
    )


def write_manifest(output_dir, source_dir=MICROS_SOURCE):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "micrOS-manifest.py"
    manifest_path.write_text(
        manifest_text(source_dir),
        encoding="utf-8",
    )
    return manifest_path


def load_image_profile(config_path=DEFAULT_IMAGE_CONFIG, profile_name=None):
    """Load and validate a declarative image resource profile."""
    config_path = Path(config_path).expanduser().resolve()
    config = _load_config_file(config_path)

    profile_name = profile_name or config.get("default_profile")
    profile = config.get("profiles", {}).get(profile_name)
    if not profile:
        raise BuildError("Image profile {!r} was not found in {}".format(profile_name, config_path))
    try:
        profile["directories"]
        profile["modules"]["include"]
    except (KeyError, TypeError) as exc:
        raise BuildError("Invalid image profile {!r}".format(profile_name)) from exc
    for directory in profile["directories"]:
        if directory.get("delivery") != "copy":
            raise BuildError("Resource directories must use delivery='copy'")
        source = _configured_source(directory["source"])
        if not source.is_dir():
            raise BuildError("Configured resource directory is missing: {}".format(source))
    return profile_name, profile


def _configured_source(relative_path):
    source = (REPOSITORY_ROOT / relative_path).resolve()
    try:
        source.relative_to(REPOSITORY_ROOT)
    except ValueError as exc:
        raise BuildError("Configured source escapes the repository: {}".format(relative_path)) from exc
    return source


def run(command, cwd, env=None):
    printable = " ".join(str(part) for part in command)
    log("RUN", "{} (cwd: {})".format(printable, cwd))
    started = monotonic()
    try:
        subprocess.run(
            [str(part) for part in command],
            cwd=str(cwd),
            env=env,
            check=True,
        )
    except FileNotFoundError as exc:
        raise BuildError("Required command is unavailable: {}".format(command[0])) from exc
    except subprocess.CalledProcessError as exc:
        raise BuildError("Command failed with exit code {}: {}".format(exc.returncode, printable)) from exc
    log("OK", "Command completed in {:.1f}s".format(monotonic() - started))


def ensure_micropython_checkout(micropython_dir):
    """Clone the pinned MicroPython release when the managed checkout is absent."""
    micropython_dir = Path(micropython_dir).expanduser().resolve()
    if micropython_dir.exists():
        log("INFO", "Using MicroPython checkout: {}".format(micropython_dir))
        return micropython_dir

    micropython_dir.parent.mkdir(parents=True, exist_ok=True)
    log("INFO", "MicroPython checkout missing; cloning {}".format(MICROPYTHON_STABLE_VERSION))
    run(
        [
            "git",
            "clone",
            "--branch",
            MICROPYTHON_STABLE_VERSION,
            "--depth",
            "1",
            MICROPYTHON_REPOSITORY,
            str(micropython_dir),
        ],
        cwd=micropython_dir.parent,
    )
    return micropython_dir


def ensure_esp_idf_checkout(esp_idf_dir):
    """Clone the ESP-IDF release required by the pinned MicroPython version."""
    esp_idf_dir = Path(esp_idf_dir).expanduser().resolve()
    if esp_idf_dir.exists():
        if not (esp_idf_dir / "export.sh").is_file():
            raise BuildError("Not an ESP-IDF source checkout: {}".format(esp_idf_dir))
        log("INFO", "Using ESP-IDF checkout: {}".format(esp_idf_dir))
        return esp_idf_dir

    esp_idf_dir.parent.mkdir(parents=True, exist_ok=True)
    log("INFO", "ESP-IDF checkout missing; cloning {}".format(ESP_IDF_VERSION))
    run(
        [
            "git",
            "clone",
            "--branch",
            ESP_IDF_VERSION,
            "--depth",
            "1",
            "--recursive",
            "--shallow-submodules",
            ESP_IDF_REPOSITORY,
            str(esp_idf_dir),
        ],
        cwd=esp_idf_dir.parent,
    )
    return esp_idf_dir


def idf_environment(esp_idf_dir, idf_target, tools_dir=DEFAULT_IDF_TOOLS_DIR):
    """Install ESP-IDF tools when needed and return its exported environment."""
    esp_idf_dir = Path(esp_idf_dir).expanduser().resolve()
    tools_dir = Path(tools_dir).expanduser().resolve()
    tools_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["IDF_TOOLS_PATH"] = str(tools_dir)
    install_marker = tools_dir / ".micros-{}-{}-installed".format(
        ESP_IDF_VERSION, idf_target
    )
    if not install_marker.is_file():
        log("INFO", "Installing ESP-IDF tools for target {}".format(idf_target))
        run(["./install.sh", idf_target], cwd=esp_idf_dir, env=env)
        install_marker.touch()
    else:
        log("INFO", "ESP-IDF tools already installed for target {}".format(idf_target))

    log("INFO", "Loading ESP-IDF environment")
    try:
        result = subprocess.run(
            [
                "bash",
                "-c",
                'source "$1/export.sh" >/dev/null && env -0',
                "bash",
                str(esp_idf_dir),
            ],
            env=env,
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise BuildError("bash is required to load the ESP-IDF environment") from exc
    except subprocess.CalledProcessError as exc:
        raise BuildError("Failed to load ESP-IDF environment") from exc

    exported_env = {}
    for item in result.stdout.split(b"\0"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            exported_env[os.fsdecode(key)] = os.fsdecode(value)

    missing_build_tools = [
        tool
        for tool in ("cmake", "ninja")
        if shutil.which(tool, path=exported_env.get("PATH")) is None
    ]
    if missing_build_tools:
        python_env = exported_env.get("IDF_PYTHON_ENV_PATH")
        if not python_env:
            raise BuildError("ESP-IDF did not export IDF_PYTHON_ENV_PATH")
        python_executable = Path(python_env) / "bin" / "python"
        log(
            "INFO",
            "Installing missing build utilities: {}".format(
                ", ".join(missing_build_tools)
            ),
        )
        run(
            [python_executable, "-m", "pip", "install"] + missing_build_tools,
            cwd=esp_idf_dir,
            env=exported_env,
        )

    for tool in ("cmake", "ninja"):
        tool_path = shutil.which(tool, path=exported_env.get("PATH"))
        if tool_path is None:
            raise BuildError("{} is unavailable after ESP-IDF setup".format(tool))
        log("OK", "{}: {}".format(tool, tool_path))
    return exported_env


def validate_git_version(checkout_dir, expected_version, component, allow_version_mismatch=False):
    """Require a reproducible, exact release checkout."""
    if not allow_version_mismatch:
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--exact-match"],
                cwd=str(checkout_dir),
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise BuildError(
                "{} must be checked out exactly at {}. "
                "Use --allow-version-mismatch only for intentional testing."
                .format(component, expected_version)
            ) from exc
        actual_version = result.stdout.strip()
        if actual_version != expected_version:
            raise BuildError(
                "Expected {} {}, found {}. "
                "Checkout the stable tag or use --allow-version-mismatch."
                .format(component, expected_version, actual_version or "unknown")
            )
        log("OK", "{} version: {}".format(component, actual_version))


def validate_micropython_checkout(micropython_dir, allow_version_mismatch=False):
    micropython_dir = Path(micropython_dir).expanduser().resolve()
    esp32_port = micropython_dir / "ports" / "esp32"
    if not (micropython_dir / "mpy-cross").is_dir() or not esp32_port.is_dir():
        raise BuildError(
            "Not a MicroPython source checkout: {}".format(micropython_dir)
        )
    validate_git_version(
        micropython_dir,
        MICROPYTHON_STABLE_VERSION,
        "MicroPython",
        allow_version_mismatch,
    )
    return micropython_dir


def build_image(
    device_name,
    micropython_dir,
    esp_idf_dir,
    output_dir,
    build_dir=DEFAULT_BUILD_DIR,
    config_path=DEFAULT_IMAGE_CONFIG,
    profile_name=None,
    allow_version_mismatch=False,
):
    device = SUPPORTED_DEVICES[device_name]
    started = monotonic()
    log("BUILD", "micrOS firmware image build started")
    log("INFO", "Target: {} ({})".format(device_name, device["micropython_board"]))
    log("INFO", "Output directory: {}".format(Path(output_dir).expanduser().resolve()))

    profile_name, profile = load_image_profile(config_path, profile_name)
    log("INFO", "Resource profile: {}".format(profile_name))

    log_step(1, 7, "Validate source selection and generate frozen manifest")
    source_files = core_source_files()
    log("INFO", "Freezing {} direct source/*.py files:".format(len(source_files)))
    for source_file in source_files:
        log("SOURCE", source_file)
    _, module_files = configured_module_files(profile, device["platform"])
    log("INFO", "Copying {} allowed modules after flash:".format(len(module_files)))
    for module_file in module_files:
        log("COPY", "modules/{} (.mpy preferred, .py fallback)".format(module_file))
    for resource in profile["directories"]:
        log(
            "COPY",
            "{} -> /{} (post-flash resource copier)".format(
                resource["source"], resource["target"].strip("/")
            ),
        )

    micropython_dir = ensure_micropython_checkout(micropython_dir)
    micropython_dir = validate_micropython_checkout(
        micropython_dir,
        allow_version_mismatch=allow_version_mismatch,
    )
    output_dir = Path(output_dir).expanduser().resolve()
    build_dir = Path(build_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = write_manifest(build_dir)
    log("OK", "Frozen manifest: {}".format(manifest_path))

    log_step(2, 7, "Prepare pinned ESP-IDF and toolchain")
    esp_idf_dir = ensure_esp_idf_checkout(esp_idf_dir)
    validate_git_version(
        esp_idf_dir,
        ESP_IDF_VERSION,
        "ESP-IDF",
        allow_version_mismatch,
    )
    env = idf_environment(esp_idf_dir, device["idf_target"])
    board = device["micropython_board"]
    esp32_port = micropython_dir / "ports" / "esp32"
    target_build_dir = esp32_port / "build-{}".format(board)
    custom_board_dir = prepare_custom_board(micropython_dir, build_dir, device)
    make_target_args = [
        "BOARD={}".format(board),
        "BOARD_DIR={}".format(custom_board_dir),
    ]

    log_step(3, 7, "Build MicroPython cross-compiler")
    run(["make", "-C", "mpy-cross"], cwd=micropython_dir, env=env)

    log_step(4, 7, "Reset target build to prevent stale frozen modules")
    if target_build_dir.exists():
        shutil.rmtree(str(target_build_dir))
        log("OK", "Removed previous target build: {}".format(target_build_dir))
    else:
        log("OK", "Target build is already clean")
    log_step(5, 7, "Prepare MicroPython ESP32 submodules")
    run(["make", "submodules"] + make_target_args, cwd=esp32_port, env=env)
    log_step(6, 7, "Build firmware with frozen micrOS core")
    run(
        [
            "make",
            "FROZEN_MANIFEST={}".format(manifest_path),
        ] + make_target_args,
        cwd=esp32_port,
        env=env,
    )

    firmware_source = target_build_dir / "firmware.bin"
    if not firmware_source.is_file():
        raise BuildError("Build completed without producing: {}".format(firmware_source))

    log_step(7, 7, "Publish versioned firmware image")
    micropython_version = MICROPYTHON_STABLE_VERSION.lstrip("v")
    firmware_output = output_dir / OUTPUT_FILENAME_TEMPLATE.format(
        device=device_name,
        micropython_version=micropython_version,
        micros_version=micros_version(),
    )
    shutil.copy2(str(firmware_source), str(firmware_output))

    log("SUCCESS", "Firmware: {}".format(firmware_output))
    log(
        "SUCCESS",
        "Runtime identification key: {}".format(MICROS_FIRMWARE_MARKER),
    )
    log("SUCCESS", "Only direct source/*.py core files are frozen")
    log("SUCCESS", "Allowed web and module resources will be copied post-flash")
    log("SUCCESS", "Completed in {:.1f}s".format(monotonic() - started))
    log("BOOT", "Frozen main.py will be executed automatically by MicroPython")
    return firmware_output


def print_supported_devices():
    log("INFO", "Supported devices:")
    for name, device in sorted(SUPPORTED_DEVICES.items()):
        print(
            "  {name:<12} {board:<24} {status:<10} {description}".format(
                name=name,
                board=device["micropython_board"],
                status=device["status"],
                description=device["description"],
            )
        )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Build stable MicroPython with direct micrOS/source/*.py core files "
            "frozen into the firmware."
        )
    )
    parser.add_argument(
        "--device",
        choices=sorted(SUPPORTED_DEVICES),
        help="build only one target device (default: build every supported device)",
    )
    parser.add_argument(
        "--micropython-dir",
        default=str(DEFAULT_MICROPYTHON_DIR),
        help=(
            "MicroPython checkout; cloned automatically when absent "
            "(default: toolkit/workspace/build/micropython)"
        ),
    )
    parser.add_argument(
        "--esp-idf-dir",
        default=str(DEFAULT_ESP_IDF_DIR),
        help=(
            "ESP-IDF checkout; cloned and configured automatically when absent "
            "(default: toolkit/workspace/build/esp-idf)"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="firmware destination (default: micrOS/micropython)",
    )
    parser.add_argument(
        "--build-dir",
        default=str(DEFAULT_BUILD_DIR),
        help="temporary manifest and bootstrap destination",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_IMAGE_CONFIG),
        help="image resource configuration (default: toolkit/micrOSImageConfig.json)",
    )
    parser.add_argument(
        "--profile",
        help="resource profile name (default: config default_profile)",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="generate the manifest without invoking the compiler",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="show supported device identifiers and exit",
    )
    parser.add_argument(
        "--allow-version-mismatch",
        action="store_true",
        help="allow an intentional build from a tag other than the pinned stable release",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.list_devices:
        print_supported_devices()
        return 0

    if args.manifest_only:
        profile_name, _ = load_image_profile(args.config, args.profile)
        manifest_path = write_manifest(args.build_dir)
        source_files = core_source_files()
        log("OK", "Manifest: {}".format(manifest_path))
        log("INFO", "Resource profile: {}".format(profile_name))
        log("INFO", "Frozen core files: {}".format(len(source_files)))
        for source_file in source_files:
            log("SOURCE", source_file)
        return 0

    devices = [args.device] if args.device else sorted(SUPPORTED_DEVICES)
    log("INFO", "Build targets: {}".format(", ".join(devices)))
    outputs = []
    for device_name in devices:
        outputs.append(
            build_image(
                device_name,
                args.micropython_dir,
                args.esp_idf_dir,
                args.output_dir,
                build_dir=args.build_dir,
                config_path=args.config,
                profile_name=args.profile,
                allow_version_mismatch=args.allow_version_mismatch,
            )
        )
    log("SUCCESS", "Built {} firmware image(s)".format(len(outputs)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as error:
        print("[micrOS-image][ERROR] {}".format(error), file=sys.stderr, flush=True)
        sys.exit(1)
