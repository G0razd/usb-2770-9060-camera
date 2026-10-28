# SQ Technology "Dual Mode Camera 1300" / A130 (USB 2770:9060)

Get the photos off a cheap mid-2000s USB camera with the SQ Technology chip that Windows 10/11 cannot
drive any more, on **Windows 11 (through WSL)** or **Linux**.

## Is this your camera?

- Windows Device Manager shows **"USB Digital Still Camera"** with a yellow mark and **code 28**
  ("The drivers for this device are not installed").
- Its hardware ID is **`USB\VID_2770&PID_9060`** (Device Manager → Properties → Details → Hardware Ids).
- On Linux, `lsusb` shows **`ID 2770:9060 NHJ, Ltd A130`**.

Brand names on the case vary. The USB ID is what matters.

## Why there is no Windows driver

The only drivers ever published for 2770:9060 are 32-bit Windows XP drivers from 2003-2004 (Microsoft
Update Catalog: "Service and Quality Technology Co., LTD - Video - A130" and "Dual Mode Camera 1300").
64-bit Windows cannot load them. Packages that list 9060 for x64 (for example "SQ900", 2.110.61.28) ship
only the INF, without `Capt9060.sys`.

This repo uses libgphoto2 instead. Its `digigr8` driver already speaks this camera's USB protocol; the
patch here adds the camera's picture format (1280x960 stored as four compressed 640x480 quadrants). See
[docs/FORMAT.md](docs/FORMAT.md).

## Windows 11

Needs WSL with an Ubuntu distribution (`wsl --install` if you have none).

1. Download this repo (Code → Download ZIP, or `git clone`) and open PowerShell in its folder.
2. Install usbipd-win and build the patched gphoto2 inside WSL (one admin prompt, about 5 minutes):

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\windows\Install.ps1
   ```

3. Plug the camera in, switch it on, and download its photos:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\windows\Pull-CameraPhotos.ps1
   ```

   The first time, it asks for admin rights once to share the camera with WSL. Photos are saved as JPG
   to `Pictures\OldCamera\<date_time>\`. Use `-OutputDir D:\Somewhere` to change that and `-Distro Name`
   if your Ubuntu is not the default WSL distribution.

## Linux (Debian / Ubuntu)

```bash
git clone https://github.com/G0razd/usb-2770-9060-camera.git
cd usb-2770-9060-camera
sudo linux/build.sh
sq9060-pull ~/Pictures/OldCamera
```

`build.sh` installs the build dependencies with apt, builds a patched libgphoto2 and the `gphoto2` tool
into `/opt/gphoto2-sq9060` (your system gphoto2 is not touched), installs a udev rule so the camera
works without root, and links `sq9060-pull` into `/usr/local/bin`. Replug the camera after the first
build so the udev rule applies.

You can also use the patched gphoto2 directly:

```bash
/opt/gphoto2-sq9060/bin/gphoto2 --auto-detect
/opt/gphoto2-sq9060/bin/gphoto2 --camera "SQ Technology A130" --get-all-files
```

## Good to know

- **The camera keeps photos in RAM.** When the batteries are removed or run flat, the photos are gone.
  "No photos on the camera" on an old camera usually means exactly that.
- **Indoor photos blur easily.** The sensor needs long exposures; hold it still.
- **Both resolution settings work:** 1280x960 and 640x480 photos.
- **Webcam mode is not supported** here, only downloading photos. The camera does not seem to store
  video clips in its memory.
- **Flash and resolution are set on the camera itself** (its buttons and status display), not over USB.
- **Raw data:** `gphoto2 --camera "SQ Technology A130" --get-all-raw-data` saves the undecoded pictures.
  `python tools/sq9060_decode.py raw_pict001.raw` turns one into a PNG without the patched library,
  which is handy for checking a camera that behaves differently.

If your 2770:9060 camera gives wrong pictures, open an issue with one raw file from
`--get-all-raw-data` and the output of `gphoto2 --debug --debug-logfile=log.txt --camera "SQ Technology A130" --list-files`.

## Repository layout

| Path | What it is |
|---|---|
| `patches/libgphoto2-sq9060.patch` | The libgphoto2 change (camlibs/digigr8) |
| `linux/build.sh` | Builds libgphoto2 + gphoto2 at pinned commits with the patch applied |
| `linux/sq9060-pull` | Downloads every photo and converts it to JPG |
| `windows/Install.ps1` | Installs usbipd-win and runs the build inside WSL |
| `windows/Pull-CameraPhotos.ps1` | Shares the camera with WSL and runs `sq9060-pull` |
| `tools/sq9060_decode.py` | Standalone reference decoder for raw pictures, with tests |
| `docs/FORMAT.md` | What the camera sends and how the picture format was worked out |

## Credits and license

The USB protocol and the SQ905C compression come from libgphoto2's `digigr8` camlib by Theodore
Kilgore. This repo is licensed under the GNU LGPL 2.1 or later, the same as libgphoto2 (see `LICENSE`).
