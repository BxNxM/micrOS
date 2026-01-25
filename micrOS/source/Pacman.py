"""
Module is responsible for Package management and installation
Install from
    Package URL (package.json):
        https://github.com/BxNxM/micrOSPackages/tree/main/blinky_example
        github:BxNxM/micrOSPackages/blinky_example
    File URL:
        https://github.com/BxNxM/micrOS/blob/master/toolkit/workspace/precompiled/modules/LM_rgb.mpy
        github:BxNxM/micrOS/toolkit/workspace/precompiled/modules/LM_rgb.mpy
    Default packages:
        by name (micropython doc.)

Load Modules in /lib/LM_* will be automatically moved to /modules/LM_* as post install step.

Designed by Marcell Ban aka BxNxM
"""

from json import load
from mip import install as mipstall
from uos import rename, mkdir
from Files import OSPath, path_join, is_file, ilist_fs, is_dir, remove_file, remove_dir
from Debug import syslog, console_write
from urequests import get as uget


# ---------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------

def _normalize_source(ref):
    """
    Normalize GitHub URLs or shorthand for mip compatibility.
    Converts:
      - https://github.com/user/repo/blob/branch/path/file.py → https://raw.githubusercontent.com/user/repo/branch/path/file.py
      - https://github.com/user/repo/tree/branch/path → github:user/repo/path
    Returns (normalized_ref, branch)
    """
    try:
        ref = ref.strip().rstrip("/")
        # Already in github: shorthand
        if ref.startswith("github:"):
            return ref, None

        if ref.startswith("https://"):
            ref = ref.replace("https://", "")
        if ref.startswith("github.com"):
            # Folder (tree) case → github:user/repo/path
            if "/tree/" in ref:
                console_write("[mip-normalize] detected GitHub tree folder link")
                parts = ref.split("/")
                user, repo = parts[1], parts[2]
                branch = parts[4]
                path = "/".join(parts[5:])
                github_ref = f"github:{user}/{repo}/{path}".rstrip("/")
                return github_ref, branch

            # File (blob) case → raw.githubusercontent.com
            if "/blob/" in ref:
                console_write("[mip-normalize] detected GitHub blob file link")
                url_base = "https://raw.githubusercontent.com/"
                ref = ref.replace("github.com/", url_base).replace("/blob", "")
                return ref, None

            # Direct GitHub file (no blob/tree) → github:user/repo/path
            if ref.count("/") >= 2:
                console_write("[mip-normalize] direct GitHub path (no blob/tree)")
                parts = ref.split("/")
                user, repo = parts[1], parts[2]
                path = "/".join(parts[3:])
                github_ref = f"github:{user}/{repo}/{path}".rstrip("/")
                return github_ref, None

        console_write("[mip-normalize] unchanged")
        return ref, None

    except Exception as e:
        syslog(f"[ERR][pacman] normalize failed: {ref}: {e}")
        return str(ref), None


def _protected_resource(source_name):
    return source_name.split(".")[0] in ("LM_system", "LM_pacman", "LM_cluster")


def _unpack_from_pacman_json(path:str, packages:tuple) -> tuple[bool, str]:
    """
    Unpack Load Modules and other resources based on pacman.json
    :param path: packages library path (default: /lib)
    :param packages: list of package names, but least one to unpack
    """
    verdict = ""
    # Check all input packages
    for pack in packages:
        pack_meta_path = path_join(path, pack, 'pacman.json')
        if is_file(pack_meta_path):
            verdict += f"\n    UNPACKING {pack_meta_path}"
            # Load package layout metadata
            try:
                with open(pack_meta_path, 'r') as p:
                    layout = load(p).get('layout', {})
            except Exception as e:
                syslog(f"[ERR] Package unpack {pack_meta_path}: {e}")
                layout = {}
            # Unpack files based on layout metadata
            for target, source_list in layout.items():
                # Restrict write access for /config/*
                if target.lstrip("/").startswith("config"):
                    verdict += f"\n  ✗ Protected target dir: {target}"
                    continue
                target_dir = path_join(OSPath._ROOT, target)
                for source in source_list:
                    source_path = path_join(path, source)
                    source_name = source.split('/')[-1] if '/' in source else source
                    if _protected_resource(source_name):
                        verdict += f"\n  ! Unpack skip - protected target: {source_name}"
                        continue
                    if is_file(source_path):
                        try:
                            if not is_dir(target_dir):
                                # Support single-level child dir
                                mkdir(target_dir)
                        except Exception as e:
                            verdict += f"\n  ✗ Unpack subdir error {target_dir}: {e}"
                        try:
                            rename(source_path, path_join(target_dir, source_name))
                            verdict += f"\n  ✓ Unpacked {source} -> {target_dir}"
                        except Exception as e:
                            verdict += f"\n  ✗ Unpack error {source}: {e}"
                    elif not is_file(path_join(target_dir, source)):
                        # Check already unpacked target resource
                        verdict += f"\n  ✗ Unpack error: {source} not exists"
    return "\nNothing to unpack" if verdict == "" else verdict


# ---------------------------------------------------------------------
# Core installer
# ---------------------------------------------------------------------

def _install_any(ref, target=None):
    """Internal wrapper with consistent error handling and debug output."""
    verdict = f"[mip] Installing: {ref}\n"
    try:
        ref, branch = _normalize_source(ref)
        kwargs = {}
        if branch:
            kwargs["version"] = branch
        kwargs["target"] = target or OSPath.LIB
        verdict = f"[mip] Installing: {ref} {kwargs}\n"
        # MIP Install
        mipstall(ref, **kwargs)
        verdict += f"  ✓ Installed under {kwargs['target']}"
    except Exception as e:
        err = f"  ✗ Failed to install '{ref}': {e}"
        syslog(f"[ERR][pacman] {err}")
        verdict += err
    return verdict


# ---------------------------------------------------------------------
# Public install functions
# ---------------------------------------------------------------------

def install_requirements(source="requirements.txt"):
    """Install from a requirements.txt file under /config."""
    source_path = path_join(OSPath.CONFIG, source)
    verdict = f"[mip] Installing from requirements file: {source_path}\n"
    if is_file(source_path):
        with open(source_path, "r") as f:
            for req in f:
                try:
                    verdict += _install_any(req, target=OSPath.LIB) + "\n"
                except Exception as e:
                    err = f"  ✗ Failed to process {source}: {e}"
                    syslog(f"[ERR][pacman] {err}")
                    verdict += err
            verdict += "  ✓ All listed packages processed"
    else:
        err = f"  ✗ {source_path} not exists"
        syslog(f"[ERR][pacman] {err}")
        verdict += err
    return verdict


def unpack(ref:str=None):
    """
    Unpack downloaded package from /lib
    - use pacman.json metadata layout to unpack files to multiple targets
    :param ref: install reference (extract package name from this)
    """

    if ref is None:
        # Collect all package names under /lib and unpack all
        packages = tuple(ilist_fs(OSPath.LIB, type_filter='d'))
    else:
        # Handle single explicit ref for unpacking
        ref_parts = [p for p in ref.split("/") if p]
        pack_name = ref_parts[-2] if '.' in ref_parts[-1] else ref_parts[-1]
        packages = (pack_name, )

    return _unpack_from_pacman_json(OSPath.LIB, packages)

# ---------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------

def install(ref):
    """
    Unified mip-based installer for micrOS.
    Automatically detects:
      - requirements.txt files (local)
      - Single-file load modules (LM_/IO_ names or URLs)
      - GitHub or raw URLs (tree/blob/github:)
      - Official MicroPython packages
    """

    if not ref:
        return "[mip] Nothing to install (empty input)"

    # 1. Install from requirements.txt
    if ref == "requirements.txt":
        verdict = install_requirements(ref)
        verdict += unpack()
        return verdict

    # 2. Install from URL or Shorthand file / package reference
    if ref.startswith("github") or ref.startswith("http"):
        # 2.1. Exact file ref: LM_/IO_ load modules → /modules
        if ref.endswith("py") and ("LM_" in ref or "IO_" in ref):
            return _install_any(ref, target=OSPath.MODULES)

        # 2.2. Package ref: GitHub or raw URLs → /lib
        verdict = _install_any(ref, target=OSPath.LIB)
        verdict += unpack(ref)
        return verdict

    # 3. Fallback/Official micropython package → /lib
    return _install_any(ref, target=OSPath.LIB)


def uninstall(package_name):
    """
    Uninstalls package from /lib with its dependencies
    :param package_name: package name under /lib
    """
    pack_path = path_join(OSPath.LIB, package_name)
    pack_meta = path_join(pack_path, "pacman.json")

    if not is_dir(pack_path):
        return f"✗ No packaged found: {pack_path}"

    verdict = f"Uninstall {package_name}\n"
    if is_file(pack_meta):
        # Load package layout metadata
        try:
            with open(pack_meta, 'r') as p:
                layout = load(p).get('layout', {})
        except Exception as e:
            syslog(f"[ERR] Package uninstall {pack_meta}: {e}")
            layout = {}

        for target, source_list in layout.items():
            # Restrict write access for /config/*
            if target.lstrip("/").startswith("config"):
                verdict += f"  ✗ Protected target dir: {target}\n"
                continue
            target_dir = path_join(OSPath._ROOT, target)
            for source in source_list:
                source_name = source.split('/')[-1] if '/' in source else source
                if _protected_resource(source_name):
                    verdict += f"  ✗ Remove skip - protected target: {source_name}\n"
                    continue
                unpacked_path = path_join(target_dir, source_name)
                if is_file(unpacked_path):
                    remove_file(unpacked_path)
                    verdict += f"  ✓ Removed: {unpacked_path}\n"

    # Delete package
    verdict += "  " + remove_dir(pack_path)
    return verdict

def upgrade(package_name, force=False):
    """
    Update package based on package name and paccman.json[versions][package]
    - embeds unified mip-based installer for micrOS.: install paccman.json[url]
    :param package_name: package name under /lib
    :param force: skip version check
    """
    pack_path = path_join(OSPath.LIB, package_name)
    pack_meta = path_join(pack_path, "pacman.json")

    if not is_dir(pack_path) or not is_file(pack_meta):
        return f"✗ No packaged (metadata) found: {pack_path}"

    verdict = f"Upgrade: collecting package info {package_name}\n"
    # 1. Get local package info
    with open(pack_meta, 'r') as f:
        pm_json = load(f)
    current_version = pm_json.get("versions", {"package": "0.0.0"}).get("package")
    package_url = pm_json.get("url", "")
    # 2. Get latest package version
    latest_version = current_version
    if package_url:
        _part1 = '/'.join(package_url.split(':', 1)[1].split('/', 2)[:2])
        _part2 = package_url.split(':', 1)[1].split('/', 2)[2]
        package_json_url = f"https://raw.githubusercontent.com/{_part1}/refs/heads/main/{_part2}/package.json"
        try:
            code, body = uget(url=package_json_url, sock_size=256, jsonify=True)
            if code == 200:
                # Set remote/latest version for real
                latest_version = body.get("version", current_version)
            else:
                verdict += f"  ✗ Failed to retrieve remote version, code: {code}"
            del body    # Cleanup
        except Exception as e:
            verdict += f"  ✗ Failed to retrieve remote version: {e}"

    # Evaluate package upgrade request
    if force or current_version != latest_version:
        if package_url:
            verdict += f"  ✓ Upgrade package ({current_version}->{latest_version}): {package_url}\n"
            verdict += install(package_url)
        else:
            verdict += f"  ✗ Skip upgrade, package URL unavailable: {package_url}\n"
    else:
        verdict += f"  ✓ Skip upgrade, up-to-date: {current_version} == {latest_version}\n"
    return verdict
