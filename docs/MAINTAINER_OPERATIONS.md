# Maintainer operations

This page collects repository-maintenance commands that are intentionally kept
out of the user-facing project README. See [`CONTRIBUTING.md`](../CONTRIBUTING.md)
for contribution workflow and change-label conventions.

## Diagnostics and media

Save a GNU Screen console buffer:

```text
Ctrl+A :
hardcopy -h <filename>
```

Run the micrOS linter:

```bash
devToolKit.py -lint
# Equivalent long option:
devToolKit.py --linter
```

Convert PNG or JPEG frames to a GIF with ImageMagick:

```bash
convert -delay 60 ./*.png mygif.gif
```

PyCallGraph was previously used for call-graph generation but is now a legacy
tool: <https://pycallgraph.readthedocs.io/en/master/>.

## Gateway systemd service

Install DevToolKit before creating the service.

The beta helper is `toolkit/helper_scripts/linux_service/make.bash`. It probes
for a working DevToolKit command before generating the service. Prefer it over
hard-coding `python -m devToolKit`, because packaged installations expose
`devToolKit.py` as a script rather than a declared Python module.

The generated service requires installation-specific values for the user,
working directory, executable path, and `API_AUTH` credentials. Review the
generated file before copying it to `/lib/systemd/system/`.

Template:

```ini
[Unit]
Description=micrOS gateway REST API service
After=network-online.target

[Service]
Environment="API_AUTH=<usr_name>:<password>"
ExecStart=<absolute-path-to-devToolKit.py> --light -gw
WorkingDirectory=/home/<user>
StandardOutput=inherit
StandardError=inherit
Restart=always
User=<user>

[Install]
WantedBy=multi-user.target
```

If a shell wrapper is used instead, set `ExecStart` to `/bin/bash` followed by
the wrapper's absolute path. For background on creating a Raspberry Pi service,
see <https://domoticproject.com/creating-raspberry-pi-service/>.

```bash
sudo cp micros-gw.service /lib/systemd/system/
sudo systemctl start micros-gw.service
sudo systemctl enable micros-gw.service
sudo systemctl status micros-gw.service
```

## Git and release maintenance

```bash
git tag -a vX.Y.Z-K -m "tag message"
git push origin --tags
git log --pretty=oneline
```

Historical release file-list inspection command:

```bash
git diff --name-only fbb4875609a3c0ee088b6a118ebf9f8a500be0fd HEAD | grep 'mpy-MicrOS'
```

The former direct publishing command was `git push -u origin master`. Before
using it, confirm that `master` is still the intended release branch and that
the selected remote is correct.

Historical note on embedding YouTube links in GitHub Markdown:
<https://github.com/itskeshav/Add-youtube-link-in-Readme.md>.

Review and publish changes through the repository's normal branch and review
workflow. Do not use a hard-coded `git push` command from documentation as a
substitute for checking the active branch and remote.

## Git-history visualization

With Gource and FFmpeg installed:

```bash
gource \
    --highlight-users \
    --hide filenames \
    --file-idle-time 0 \
    --max-files 0 \
    --seconds-per-day 0.01 \
    --auto-skip-seconds 1 \
    --title "micrOS Evolution" \
    --output-ppm-stream - \
    | ffmpeg -y -r 30 -f image2pipe -vcodec ppm -i - \
      -vcodec libx264 -preset ultrafast -pix_fmt yuv420p -crf 1 \
      -threads 0 -bf 0 output.mp4
```
