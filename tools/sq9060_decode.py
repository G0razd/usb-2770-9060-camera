import argparse
import struct
import sys
import zlib

TILE_WIDTH = 640
TILE_HEIGHT = 480
HEADER_SIZE = 32
CATALOG_SIZE = 16
PICTURE_CODE = 0x67

SHORT_CODES = (8, 7, 9, 6)
LONG_CODES = (10, 11, 12, 13, 14, 15, 5, 4, 3, 2, 1, 0)
DELTAS = (-144, -110, -77, -53, -35, -21, -11, -3, 2, 10, 20, 34, 52, 76, 110, 144)


class FormatError(ValueError):
    pass


def read_deltas(data, count):
    out = []
    pos = 0
    total_bits = len(data) * 8

    def bit():
        nonlocal pos
        if pos >= total_bits:
            raise FormatError(f"stream ended after {len(out)} of {count} values")
        value = (data[pos >> 3] >> (7 - (pos & 7))) & 1
        pos += 1
        return value

    while len(out) < count:
        ones = 0
        while ones < 4 and bit():
            ones += 1
        if ones < 4:
            out.append(SHORT_CODES[ones])
            continue
        index = (bit() << 3) | (bit() << 2) | (bit() << 1) | bit()
        if index >= len(LONG_CODES):
            raise FormatError(f"illegal code 0xf{index:x} at bit {pos}")
        out.append(LONG_CODES[index])
    return out


def reconstruct(deltas, width, height):
    img = bytearray(width * height)
    above = {colour: [0x80] * width for colour in ("first", "green", "last")}
    k = 0
    for pair in range(height // 2):
        for row, (left, right) in ((2 * pair, ("first", "green")), (2 * pair + 1, ("green", "last"))):
            base = row * width
            even_row = row % 2 == 0
            for i in range(width // 2):
                line = above[left]
                value = line[0] if i == 0 else (line[i] + img[base + 2 * i - 2]) // 2
                value = max(0, min(255, value + DELTAS[deltas[k]]))
                img[base + 2 * i] = value
                line[i] = value
                line = above[right]
                if i == 0:
                    value = line[1] if even_row else line[0]
                elif even_row and 2 * i != width - 2:
                    value = (line[i + 1] + img[base + 2 * i - 1]) // 2
                else:
                    value = (line[i] + img[base + 2 * i - 1]) // 2
                value = max(0, min(255, value + DELTAS[deltas[k + 1]]))
                img[base + 2 * i + 1] = value
                line[i] = value
                k += 2
    return img


def split_tiles(data):
    if len(data) < HEADER_SIZE:
        raise FormatError("picture is shorter than its 32-byte header")
    sizes = struct.unpack("<4I", data[:16])
    if HEADER_SIZE + sum(sizes) > len(data):
        raise FormatError(f"header lists {sum(sizes)} bytes of tiles, only {len(data) - HEADER_SIZE} present")
    tiles = []
    offset = HEADER_SIZE
    for size in sizes:
        tiles.append(data[offset:offset + size])
        offset += size
    return tiles


def decode_bayer(data):
    width, height = 2 * TILE_WIDTH, 2 * TILE_HEIGHT
    bayer = bytearray(width * height)
    for n, tile_data in enumerate(split_tiles(data)):
        deltas = read_deltas(tile_data, TILE_WIDTH * TILE_HEIGHT)
        tile = reconstruct(deltas, TILE_WIDTH, TILE_HEIGHT)
        x0, y0 = (n % 2) * TILE_WIDTH, (n // 2) * TILE_HEIGHT
        for y in range(TILE_HEIGHT):
            start = (y0 + y) * width + x0
            bayer[start:start + TILE_WIDTH] = tile[y * TILE_WIDTH:(y + 1) * TILE_WIDTH]
    return bayer, width, height


def bayer_to_half_rgb(bayer, width, height):
    rgb = bytearray((width // 2) * (height // 2) * 3)
    k = 0
    for y in range(0, height, 2):
        top = y * width
        bottom = top + width
        for x in range(0, width, 2):
            rgb[k] = bayer[bottom + x + 1]
            rgb[k + 1] = (bayer[top + x + 1] + bayer[bottom + x]) // 2
            rgb[k + 2] = bayer[top + x]
            k += 3
    return rgb


def write_png(path, pixels, width, height, channels):
    stride = width * channels
    rows = b"".join(b"\x00" + bytes(pixels[y * stride:(y + 1) * stride]) for y in range(height))

    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))

    colour_type = 2 if channels == 3 else 0
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, colour_type, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(rows, 6)))
        f.write(chunk(b"IEND", b""))


def strip_catalog_footer(raw):
    if len(raw) > CATALOG_SIZE and raw[-CATALOG_SIZE] == PICTURE_CODE:
        return raw[:-CATALOG_SIZE]
    return raw


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Decode a raw picture from an SQ Technology A130 (USB 2770:9060) camera, "
        "as saved by 'gphoto2 --get-all-raw-data'."
    )
    parser.add_argument("raw", help="raw picture file")
    parser.add_argument("--bayer", help="also write the full 1280x960 sensor image as a greyscale PNG")
    parser.add_argument("-o", "--output", help="colour preview PNG (640x480), default: <raw>.png")
    args = parser.parse_args(argv)

    with open(args.raw, "rb") as f:
        data = strip_catalog_footer(f.read())
    try:
        bayer, width, height = decode_bayer(data)
    except FormatError as error:
        print(f"{args.raw}: {error}", file=sys.stderr)
        return 1
    if args.bayer:
        write_png(args.bayer, bayer, width, height, 1)
    output = args.output or args.raw + ".png"
    write_png(output, bayer_to_half_rgb(bayer, width, height), width // 2, height // 2, 3)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
