# SQ Technology A130 (USB 2770:9060): protocol and picture format

Worked out on 2026-10-28 from one camera that calls itself "USB Digital Still Camera" over USB and
"NHJ, Ltd A130" in `usb.ids`. It is sold as "Dual Mode Camera 1300". Firmware ID string: `2004072818`.

## USB

- Full speed (USB 1.1), one configuration, one interface, class/subclass/protocol `ff/ff/ff`.
- Endpoints: bulk IN `0x81`, bulk OUT `0x02`, interrupt IN `0x83` (1 byte).
- The command set is the one libgphoto2's `digigr8` camlib uses for the 2770:905C family (SQ905C):
  vendor request `0x0c` with values `0x14f4`, `0x14f0`, `0x20`/`0x40`, `0x30`, `0xa0`. The 20-byte ID
  block, the 16 KiB catalog and the picture data are read from bulk endpoint `0x81` exactly as for 905C.

## Catalog entry (16 bytes per picture)

| Offset | Example | Meaning |
|---|---|---|
| 0 | `67` | Picture type. `0x67` is new: 1280x960, compressed, stored as four quadrants. `0x76` is the camera's low-resolution setting: one 640x480 SQ905C stream with no header, which `digigr8` already decodes. `0x00` ends the catalog |
| 1-2 | `02 80` | `0x0280` = 640, the width of one quadrant (big-endian) |
| 4-6 | `00 45 03` | Size of the picture data in bytes, little-endian (`0x034500` = 214272) |
| 8-9 | `02 00` | Looks like a running position in 8 KiB blocks: it grows by the data size / 8192, rounded up |
| 10 | `40` | Varies, unknown |
| 11 | `61` | Lighting value; `digigr8` already reads this byte for white balance |
| 15 | `00` | Unknown; `01` on one 640x480 picture out of fifteen |

No video clips have been seen in the catalog. "Dual mode" on these cameras means still camera plus
USB webcam; the webcam mode is not covered here.

Entries after the last picture hold whatever was in the camera's memory. The camera keeps pictures in
RAM, so they are lost when its batteries run out.

## Picture data

```
offset 0   u32 LE  size of quadrant 0 (top-left)
offset 4   u32 LE  size of quadrant 1 (top-right)
offset 8   u32 LE  size of quadrant 2 (bottom-left)
offset 12  u32 LE  size of quadrant 3 (bottom-right)
offset 16  16 bytes, constant on every picture seen: ff bb ff ff fb d9 fb ff ff db 7f 7f ff ff bf ff
offset 32  quadrant 0, then 1, 2, 3, back to back
```

32 + the four sizes is exactly the size in the catalog entry.

Each quadrant is a complete 640x480 image in the existing SQ905C compression (`digi_decompress` in
`camlibs/digigr8/digi_postprocess.c`): a prefix code of `0`, `10`, `110`, `1110` and `1111xxxx` into
16 delta steps, applied per Bayer colour against the line above. Every quadrant starts with fresh
predictors (all `0x80`). The four quadrants together are one 1280x960 BGGR Bayer image, which then goes
through the normal `digigr8` demosaic, gamma and white-balance steps.

## How it was found

- Treating the data as one 640x480 SQ905C stream decodes noise: the first 32 bytes are a header.
- Decoding a 640x480 stream from offset 32 consumes almost exactly the first header size (54325 of
  54336 bytes on one picture, 57405 of 57408 on another), so each header entry is one full image.
- Laying the four images out 2x2 gives a seamless picture; four stacked 1280x240 strips do not.
