
from sim_console import console
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import json


def _guess_url_is_file(url):
    # 1. URL path contains a filename-like pattern
    path = Path(urlparse(url).path)
    if "." in path.name:
        return True

    # 2. HEAD request content-type
    try:
        with urlopen(Request(url, method="HEAD")) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if not ctype.startswith("text/html"):
                return True
    except Exception as e:
        if "404" in str(e):
            return False

    # 4. GET small chunk and detect HTML
    try:
        with urlopen(url) as resp:
            chunk = resp.read(256).lower()
            if b"<html" in chunk:
                return False
    except:
        pass

    # last fallback: treat as file if unsure
    return True


def _url_file_content(url):
    data = ""
    try:
        with urlopen(url) as resp:
            data = resp.read()
    except Exception as e:
        print()
        console(f"❌ Failed to read {url}: {e}")
    return data


def _save_file(path, data):
    try:
        # Write as binary
        with open(path, "wb") as f:
            f.write(data)
        print(f"✅ Saved {path.parent.name}/{path.name}")
        return True
    except Exception as e:
        console(f"Failed to save {path}: {e}")
    return False


def _github_to_url(ref, branch="master"):
    if ref.startswith("github"):
        """
        Convert: github:peterhinch/micropython-mqtt
                https://raw.githubusercontent.com/peterhinch/micropython-mqtt/refs/heads/master/mqtt_as/clean.py
            To: https://raw.githubusercontent.com/peterhinch/micropython-mqtt/refs/heads/master/XXX
        """
        base_github_url = "https://raw.githubusercontent.com"
        branch = f"refs/heads/{branch}"
        # Remove mip prefix
        path = ref[len("github:"):]
        # Build subpath from path and branch name
        file_subpath = f"{path.split("/")[-2]}/{path.split("/")[-1]}"
        if "." in file_subpath:
            # File mode - Build raw URL
            path = path.replace(file_subpath, "")
            ref = f"{base_github_url}/{path}/{branch}/{file_subpath}"
        else:
            # Folder mode - Build raw URL
            ref = f"{base_github_url}/{path}/{branch}"
        return ref
    return None


def _mip_emu(ref, target=None):
    """
    [BETA]
    Tiny simulation of MicroPython's mip.install for normal Python.

    - ref:
        * URL (http/https): downloads file to `target`
        * local path (file or directory): copies to `target`
    - target:
        * destination directory (defaults to ./lib)
    - verbose:
        * if True, prints actions

    Returns: list of installed/downloaded Path objects.
    """
    # Default target like /lib in MicroPython
    if target is None:
        target = Path("lib")
    else:
        target = Path(target)

    installed = []

    # --- Case 1: URL ---------------------------------------------------------
    if isinstance(ref, str) and (ref.startswith("http") or ref.startswith("github")):
        if ref.startswith("github"):
            url = _github_to_url(ref)
            if url is None:
                console(f"Invalid GitHub URL: {ref}")
                return []
        else:
            url = ref
        dest = target / Path(urlparse(url).path).name

        if not _guess_url_is_file(url):
            url = f"{url.rstrip('/')}/package.json"
            dest = target / Path(urlparse(url).path).name
            console(f"Patch url (dir) to point to package.json: {url}")
        try:
            print(f"🔻 Downloading {url} to {dest}", end="")
            data = _url_file_content(url)
            print(f" ({len(data)} bytes)")
        except Exception as e:
            console(f"❌ Failed to read {url}: {e}")
            return []

        if url.endswith("package.json"):
            package_json_data = json.loads(data)
            package_urls = package_json_data.get("urls", [])
            for file_url in package_urls:
                pack_source_file = file_url[1]
                if pack_source_file.startswith("github"):
                    pack_source_file = _github_to_url(pack_source_file)
                pack_dest_file = Path(file_url[0])
                pack_dest_dir = target / pack_dest_file.parent
                pack_dest_dir.mkdir(parents=True, exist_ok=True)
                pack_dest_file = pack_dest_dir / pack_dest_file.name
                print(f"File download: {pack_source_file} -> {pack_dest_file}")
                data = _url_file_content(pack_source_file)
                if data:
                    if _save_file(pack_dest_file, data):
                        installed.append(pack_dest_dir.name)
        else:
            if data:
                if _save_file(dest, data):
                    installed.append(dest.name)
    return installed


def _dump_dir_content(target):
    # Dump content
    base_path = str(target.parent)
    for item in target.iterdir():
        print(f" 🗂️ {str(item).replace(base_path, '')}")
        if item.is_dir():
            for subitem in item.iterdir():
                print(f"   {str(subitem).replace(base_path, '')}")
            print("")


def install(ref, **kwargs):
    target = kwargs.get("target", Path.cwd() / "lib")
    console(f">>> mip install: {ref} {kwargs}")
    if isinstance(target, str):
        target = Path(target)
    # Run mip emulation
    _mip_emu(ref, target=target)
    # Dump content
    _dump_dir_content(target)