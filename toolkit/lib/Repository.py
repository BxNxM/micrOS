import requests
import zipfile
import io
import os

try:
    from .LocalMachine import CommandHandler
except:
    from LocalMachine import CommandHandler


def git_clone_archive(url):
    """
    Clone git repo as archive (without git installed)
    Note: No git history, it is just a snapshot
    :param url: https://github.com/micropython/webrepl
    """
    print(f"CLONE ARCHIVE: {url}")
    url = url.replace(".git", "") if url.endswith(".git") else url
    # URL of the repository zip archive (adjust branch name if needed)
    target_name = url.split("/")[-1].strip()
    zip_url = f"{url}/archive/refs/heads/master.zip"
    response = requests.get(zip_url)
    if response.status_code == 200:
        # Read the downloaded content as a binary stream
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for member in z.infolist():
                # Each member's filename is something like 'webrepl-master/filename'
                # Remove the first directory component
                parts = member.filename.split('/', 1)
                if len(parts) > 1:
                    relative_path = parts[1]
                else:
                    relative_path = parts[0]

                # Build the target path relative to the current directory
                target_path = os.path.join(target_name, relative_path)

                if member.is_dir():
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with z.open(member) as source, open(target_path, 'wb') as target_file:
                        target_file.write(source.read())
        print(f"\tRepository extracted successfully: {target_name}")
        return 0, zip_url, ""
    print(f"\tFailed to download repository archive: {target_name}")
    return 1, zip_url, ""


def git_clone(url):
    """
    Git clone - subshell call
    - git is needed to be preinstalled
    """
    print(f"GIT CLONE: {url}")
    target_name = url.split("/")[-1].strip().replace(".git", "")
    command = 'git clone {url} {name}'.format(name=target_name, url=url)
    exitcode, stdout, stderr = CommandHandler.run_command(command, shell=True)
    if exitcode == 0:
        print(f"\tRepository was cloned successfully: {target_name}")
    else:
        print(f"\tRepository clone failed: {target_name}")
    return exitcode, stdout, stderr
