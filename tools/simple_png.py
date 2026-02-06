#!/usr/bin/env python3
import struct, zlib

def _chunk(tag, data):
    return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', zlib.crc32(tag + data) & 0xffffffff)

def write_png(path, width, height, rgb_rows):
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('!IIBBBBB', width, height, 8, 2, 0, 0, 0)
    raw = b''.join(b'\x00' + row for row in rgb_rows)
    data = zlib.compress(raw, 9)
    with open(path, 'wb') as f:
        f.write(sig)
        f.write(_chunk(b'IHDR', ihdr))
        f.write(_chunk(b'IDAT', data))
        f.write(_chunk(b'IEND', b''))

def bar_chart_png(path, labels, values, colors):
    w, h = 640, 360
    img = [[(245,245,245) for _ in range(w)] for _ in range(h)]
    maxv = max(values) if values else 1
    left, top, bottom = 60, 30, h-40
    plot_w = w-80
    n = len(values)
    bar_w = max(10, int(plot_w/(max(1,n)*1.5)))
    spacing = int((plot_w - n*bar_w)/max(1,n+1))
    x = left + spacing
    for i,v in enumerate(values):
        bh = int((v/maxv)*(bottom-top))
        y0 = bottom - bh
        c = colors[i % len(colors)]
        for yy in range(y0, bottom):
            row = img[yy]
            for xx in range(x, x+bar_w):
                if 0 <= xx < w:
                    row[xx] = c
        x += bar_w + spacing
    for yy in range(top, bottom):
        img[yy][left] = (50,50,50)
    for xx in range(left, w-20):
        img[bottom][xx] = (50,50,50)
    rows = [bytes([ch for px in row for ch in px]) for row in img]
    write_png(path, w, h, rows)

if __name__ == '__main__':
    bar_chart_png('figures/example.png', ['a','b'], [1,2], [(31,119,180),(255,127,14)])
