import struct
import unittest

import sq9060_decode as d


def bits_to_bytes(bits):
    bits = bits + "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def repeated_tile(code_bits):
    count = d.TILE_WIDTH * d.TILE_HEIGHT
    return bits_to_bytes(code_bits * count)


class ReadDeltasTest(unittest.TestCase):
    def test_short_and_long_codes(self):
        data = bits_to_bytes("0" + "10" + "110" + "1110" + "11110000" + "11111011")
        self.assertEqual(d.read_deltas(data, 6), [8, 7, 9, 6, 10, 0])

    def test_illegal_long_code(self):
        with self.assertRaises(d.FormatError):
            d.read_deltas(bits_to_bytes("11111100"), 1)

    def test_truncated_stream(self):
        with self.assertRaises(d.FormatError):
            d.read_deltas(b"\xaa", 5)


class ReconstructTest(unittest.TestCase):
    def test_six_by_four_with_constant_plus_two(self):
        self.assertEqual(
            list(d.reconstruct([8] * 24, 6, 4)),
            [
                130, 130, 131, 131, 131, 131,
                132, 130, 133, 131, 134, 131,
                132, 135, 133, 136, 134, 137,
                137, 132, 138, 133, 139, 134,
            ],
        )


class SplitTilesTest(unittest.TestCase):
    def test_header_longer_than_data(self):
        data = struct.pack("<4I", 10, 10, 10, 10) + b"\xff" * 16 + b"\x00" * 39
        with self.assertRaises(d.FormatError):
            d.split_tiles(data)

    def test_tiles_follow_header(self):
        data = struct.pack("<4I", 1, 2, 3, 4) + b"\xff" * 16 + b"ABBCCCDDDD"
        self.assertEqual(d.split_tiles(data), [b"A", b"BB", b"CCC", b"DDDD"])


class DecodeBayerTest(unittest.TestCase):
    def test_quadrants_are_top_left_top_right_bottom_left_bottom_right(self):
        tiles = [repeated_tile(code) for code in ("0", "10", "110", "1110")]
        data = struct.pack("<4I", *(len(t) for t in tiles)) + b"\xff" * 16 + b"".join(tiles)
        bayer, width, height = d.decode_bayer(data)
        self.assertEqual((width, height), (1280, 960))
        self.assertEqual(bayer[0], 130)
        self.assertEqual(bayer[640], 125)
        self.assertEqual(bayer[480 * 1280], 138)
        self.assertEqual(bayer[480 * 1280 + 640], 117)


class CatalogFooterTest(unittest.TestCase):
    def test_footer_removed_only_when_it_is_a_catalog_entry(self):
        body = b"\x01" * 40
        self.assertEqual(d.strip_catalog_footer(body + b"\x67" + b"\x00" * 15), body)
        self.assertEqual(d.strip_catalog_footer(body), body)


if __name__ == "__main__":
    unittest.main()
