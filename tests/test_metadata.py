"""Metadata of animated GIF/WebP is removed without touching the frames."""
from __future__ import annotations

import io
import unittest

from PIL import Image, ImageSequence

from gallery.metadata import strip_metadata


def _frames(data: bytes) -> list[bytes]:
    with Image.open(io.BytesIO(data)) as img:
        return [frame.convert("RGBA").tobytes() for frame in ImageSequence.Iterator(img)]


def _animation(fmt: str, **save_kwargs) -> bytes:
    frames = [Image.new("RGB", (16, 16), color) for color in ("red", "green", "blue")]
    buf = io.BytesIO()
    frames[0].save(buf, fmt, save_all=True, append_images=frames[1:], duration=100, loop=0, **save_kwargs)
    return buf.getvalue()


class StripMetadataTests(unittest.TestCase):
    def test_gif_comment_and_xmp_removed(self):
        xmp = b"XMP DataXMP" + bytes([3]) + b"<x:" + bytes([0])  # application extension
        raw = _animation("GIF", comment=b"Photographer: Jane Doe")
        # Insert an XMP application extension right after the header blocks.
        insert_at = raw.index(b"\x21\xf9")
        raw = raw[:insert_at] + b"\x21\xff\x0b" + xmp + raw[insert_at:]
        self.assertIn(b"Jane Doe", raw)

        out = strip_metadata(raw, ".gif")

        self.assertNotIn(b"Jane Doe", out)
        self.assertNotIn(b"XMP DataXMP", out)
        self.assertIn(b"NETSCAPE2.0", out)  # looping kept
        self.assertEqual(_frames(raw), _frames(out))

    def test_webp_exif_removed_and_flag_cleared(self):
        exif = Image.Exif()
        exif[0x013B] = "Jane Doe"  # Artist
        raw = _animation("WEBP", exif=exif.tobytes(), lossless=True)
        self.assertIn(b"EXIF", raw)

        out = strip_metadata(raw, ".webp")

        self.assertNotIn(b"EXIF", out)
        self.assertNotIn(b"Jane Doe", out)
        vp8x = out.index(b"VP8X")
        self.assertFalse(out[vp8x + 8] & 0x08)
        self.assertEqual(_frames(raw), _frames(out))
        with Image.open(io.BytesIO(out)) as img:
            self.assertNotIn("exif", img.info)

    def test_file_without_metadata_is_unchanged(self):
        raw = _animation("GIF")
        self.assertEqual(strip_metadata(raw, ".gif"), raw)

    def test_unparsable_file_is_rejected(self):
        with self.assertRaises(ValueError):
            strip_metadata(b"GIF89a\x01\x00\x01\x00\x00\x00\x00", ".gif")
        with self.assertRaises(ValueError):
            strip_metadata(b"not a webp", ".webp")


if __name__ == "__main__":
    unittest.main()
