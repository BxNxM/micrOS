from mip import install
from Files import OSPath, path_join, is_file
from Debug import syslog


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
                print("[mip-normalize] detected GitHub tree folder link")
                parts = ref.split("/")
                user, repo = parts[1], parts[2]
                branch = parts[4]
                path = "/".join(parts[5:])
                github_ref = f"github:{user}/{repo}/{path}".rstrip("/")
                return github_ref, branch

            # File (blob) case → raw.githubusercontent.com
            if "/blob/" in ref:
                print("[mip-normalize] detected GitHub blob file link")
                url_base = "https://raw.githubusercontent.com/"
                ref = ref.replace("github.com/", url_base).replace("/blob", "")
                return ref, None

            # Direct GitHub file (no blob/tree) → github:user/repo/path
            if ref.count("/") >= 2:
                print("[mip-normalize] direct GitHub path (no blob/tree)")
                parts = ref.split("/")
                user, repo = parts[1], parts[2]
                path = "/".join(parts[3:])
                github_ref = f"github:{user}/{repo}/{path}".rstrip("/")
                return github_ref, None

        print("[mip-normalize] unchanged")
        return ref, None

    except Exception as e:
        syslog(f"[ERR][pacman] normalize failed: {ref}: {e}")
        print(f"[normalize][ERROR] {e}")
        return str(ref), None


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
        install(ref, **kwargs)
        verdict += f"  ✓ Installed successfully under {kwargs['target']}"
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
    verdict = f"[mip] Installing from requirements file: {source}\n"
    try:
        source_path = path_join(OSPath.CONFIG, source)
        verdict = f"[mip] Installing from requirements file: {source_path}\n"
        if is_file(source_path):
            install(source_path)
            verdict += "  ✓ All listed packages processed"
        else:
            err = f"  ✗ {source_path} not exists"
            syslog(f"[ERR][pacman] {err}")
            verdict += err
    except Exception as e:
        err = f"  ✗ Failed to process {source}: {e}"
        syslog(f"[ERR][pacman] {err}")
        verdict += err
    return verdict


# ---------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------

def download(ref):
    """
    Unified mip-based downloader for micrOS.
    Automatically detects:
      - requirements.txt files (local or remote)
      - Single-file load modules (LM_/IO_ names or URLs)
      - GitHub or raw URLs (tree/blob/github:)
      - Official MicroPython packages
    """

    if not ref:
        return "[mip] Nothing to download (empty input)"

    # 1. requirements.txt
    if ref == "requirements.txt":
        return install_requirements(ref)

    if "github" in ref:
        # 2. LM_/IO_ load modules → /modules
        if ref.endswith("py") and ("LM_" in ref or "IO_" in ref):
            return _install_any(ref, target=OSPath.MODULES)

        # 3. GitHub or raw URLs → /lib
        if ref.startswith("http") or ref.startswith("github"):
            return _install_any(ref, target=OSPath.LIB)

    # 4. Fallback: official micropython package → /lib
    return _install_any(ref, target=OSPath.LIB)
