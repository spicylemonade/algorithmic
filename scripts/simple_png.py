#!/usr/bin/env python3
import struct
import zlib
from pathlib import Path


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', zlib.crc32(tag + data) & 0xFFFFFFFF)


def save_png(path: str, pixels, width: int, height: int) -> None:
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            r, g, b = pixels[y][x]
            raw.extend([r, g, b])
    ihdr = struct.pack('!IIBBBBB', width, height, 8, 2, 0, 0, 0)
    data = zlib.compress(bytes(raw), 9)
    blob = b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr) + _chunk(b'IDAT', data) + _chunk(b'IEND', b'')
    Path(path).write_bytes(blob)


def blank(width: int, height: int, color=(255, 255, 255)):
    return [[color for _ in range(width)] for _ in range(height)]


def line(pixels, x0, y0, x1, y1, color=(0, 0, 0)):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= y0 < len(pixels) and 0 <= x0 < len(pixels[0]):
            pixels[y0][x0] = color
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def rect(pixels, x0, y0, x1, y1, color=(0, 0, 0), fill=False):
    if fill:
        for y in range(max(0, y0), min(len(pixels), y1 + 1)):
            for x in range(max(0, x0), min(len(pixels[0]), x1 + 1)):
                pixels[y][x] = color
        return
    line(pixels, x0, y0, x1, y0, color)
    line(pixels, x1, y0, x1, y1, color)
    line(pixels, x1, y1, x0, y1, color)
    line(pixels, x0, y1, x0, y0, color)
