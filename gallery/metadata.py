"""Lossless metadata removal for animated GIF/WebP files.

Still images lose EXIF/XMP when Pillow re-encodes them. Animated files are published as
they are (re-encoding would change the palette or quality), so their metadata blocks are
dropped here instead and everything else is copied byte for byte:

- GIF: comment extensions and application extensions other than looping (NETSCAPE2.0,
  ANIMEXTS1.0) and the colour profile (ICCRGBG1) — this removes XMP.
- WebP: EXIF and XMP chunks (and their flags in VP8X); the ICC profile is kept.

A file that cannot be parsed raises ValueError, so it is skipped instead of being
published with its metadata.
"""
from __future__ import annotations

import struct

_GIF_KEEP_APPLICATIONS = (b"NETSCAPE2.0", b"ANIMEXTS1.0", b"ICCRGBG1012")
_WEBP_DROP_CHUNKS = {b"EXIF", b"XMP "}
_VP8X_EXIF_FLAG = 0x08
_VP8X_XMP_FLAG = 0x04


def strip_metadata(data: bytes, suffix: str) -> bytes:
    """Return ``data`` without metadata blocks; ``suffix`` is ``.gif`` or ``.webp``."""
    if suffix == ".gif":
        return strip_gif_metadata(data)
    if suffix == ".webp":
        return strip_webp_metadata(data)
    raise ValueError(f"No metadata stripping for {suffix}")


def _skip_sub_blocks(data: bytes, pos: int) -> int:
    """Return the position after a GIF data sub-block sequence (ends with a 0 byte)."""
    while True:
        if pos >= len(data):
            raise ValueError("Truncated GIF sub-blocks")
        size = data[pos]
        pos += 1
        if size == 0:
            return pos
        pos += size


def strip_gif_metadata(data: bytes) -> bytes:
    if data[:6] not in (b"GIF87a", b"GIF89a") or len(data) < 13:
        raise ValueError("Not a GIF file")
    flags = data[10]
    pos = 13
    if flags & 0x80:  # global colour table
        pos += 3 * (2 ** ((flags & 0x07) + 1))
    out = bytearray(data[:pos])

    while True:
        if pos >= len(data):
            raise ValueError("GIF without trailer")
        block = data[pos]
        if block == 0x3B:  # trailer; anything after it is dropped as well
            out.append(0x3B)
            return bytes(out)
        if block == 0x2C:  # image descriptor (+ local colour table) + image data
            if pos + 10 > len(data):
                raise ValueError("Truncated GIF image descriptor")
            local = data[pos + 9]
            end = pos + 10
            if local & 0x80:
                end += 3 * (2 ** ((local & 0x07) + 1))
            end = _skip_sub_blocks(data, end + 1)  # +1: LZW minimum code size
            out += data[pos:end]
            pos = end
        elif block == 0x21:  # extension
            if pos + 2 > len(data):
                raise ValueError("Truncated GIF extension")
            label = data[pos + 1]
            end = _skip_sub_blocks(data, pos + 2)
            keep = label in (0xF9, 0x01)  # graphic control, plain text
            if label == 0xFF:
                keep = data[pos + 3:pos + 14] in _GIF_KEEP_APPLICATIONS
            if keep:
                out += data[pos:end]
            pos = end
        else:
            raise ValueError(f"Unknown GIF block 0x{block:02x}")


def strip_webp_metadata(data: bytes) -> bytes:
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("Not a WebP file")
    riff_end = min(len(data), 8 + struct.unpack("<I", data[4:8])[0])
    chunks = bytearray()
    pos = 12
    while pos + 8 <= riff_end:
        fourcc = data[pos:pos + 4]
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        end = pos + 8 + size + (size & 1)  # chunks are padded to an even length
        if end > riff_end + (size & 1):
            raise ValueError("Truncated WebP chunk")
        chunk = bytearray(data[pos:end])
        if fourcc == b"VP8X" and size >= 1:
            chunk[8] &= ~(_VP8X_EXIF_FLAG | _VP8X_XMP_FLAG) & 0xFF
        if fourcc not in _WEBP_DROP_CHUNKS:
            chunks += chunk
        pos = end
    return b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WEBP" + bytes(chunks)
