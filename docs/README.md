# Docs map

| Area | Doc | Entry files | Tests |
|---|---|---|---|
| Camera protocol and picture format | [FORMAT.md](FORMAT.md) | `patches/libgphoto2-sq9060.patch` | Manual: download from a real camera |
| Linux / WSL build and download | [../README.md](../README.md) | `linux/build.sh`, `linux/sq9060-pull` | Manual: `sudo linux/build.sh`, then `sq9060-pull` |
| Windows wrapper (WSL + usbipd-win) | [../README.md](../README.md) | `windows/Install.ps1`, `windows/Pull-CameraPhotos.ps1` | Manual on Windows 11 |
| Standalone raw decoder | [FORMAT.md](FORMAT.md) | `tools/sq9060_decode.py` | `python -m unittest discover -s tools` |
