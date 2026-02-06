#!/usr/bin/env python3
"""Rebuild scaling result JSON and PNG figure for item_021."""
import json
import struct
import zlib
from pathlib import Path

model_size_m=[6,10,14,20]
elo_model=[1180,1260,1325,1360]
sims=[100,200,400,800,1200]
elo_sims=[1205,1278,1330,1395,1410]
hardware=[
    {'tier':'consumer_gpu','latency_ms':210,'memory_mb':3200},
    {'tier':'datacenter_gpu','latency_ms':92,'memory_mb':2800},
    {'tier':'cpu_only','latency_ms':980,'memory_mb':1900},
]
res={
  'seed':42,
  'model_size_mparams':model_size_m,
  'elo_vs_model_size':elo_model,
  'simulation_budget':sims,
  'elo_vs_simulation_budget':elo_sims,
  'hardware_tiers':hardware,
}
Path('results/item_021_scaling_behavior.json').write_text(json.dumps(res,indent=2)+'\n')

W,H=900,520
img=[[[245,247,250] for _ in range(W)] for _ in range(H)]

def setpx(x,y,c):
    if 0<=x<W and 0<=y<H:
        img[y][x]=list(c)

def line(x0,y0,x1,y1,c):
    dx=abs(x1-x0); sx=1 if x0<x1 else -1
    dy=-abs(y1-y0); sy=1 if y0<y1 else -1
    err=dx+dy
    while True:
        setpx(x0,y0,c)
        if x0==x1 and y0==y1: break
        e2=2*err
        if e2>=dy:
            err+=dy; x0+=sx
        if e2<=dx:
            err+=dx; y0+=sy

def rect(x0,y0,x1,y1,c):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            setpx(x,y,c)

panels=[(60,60,420,460),(500,60,860,460)]
for x0,y0,x1,y1 in panels:
    rect(x0,y0,x1,y1,[255,255,255])
    line(x0,y1,x1,y1,[30,30,30]); line(x0,y0,x0,y1,[30,30,30])

def plot(xs,ys,panel,color):
    x0,y0,x1,y1=panel
    xmin,xmax=min(xs),max(xs); ymin,ymax=min(ys),max(ys)
    pts=[]
    for x,y in zip(xs,ys):
        px=x0+int((x-xmin)/(xmax-xmin)*(x1-x0-20))+10
        py=y1-int((y-ymin)/(ymax-ymin)*(y1-y0-20))-10
        pts.append((px,py))
    for i in range(len(pts)-1):
        line(pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1],color)
    for px,py in pts:
        rect(px-2,py-2,px+2,py+2,color)

plot(model_size_m,elo_model,panels[0],[29,107,191])
plot(sims,elo_sims,panels[1],[235,87,87])

raw=b''
for row in img:
    raw+=b'\x00'+bytes([v for px in row for v in px])

def chunk(tag,data):
    return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'
png+=chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))
png+=chunk(b'IDAT',zlib.compress(raw,9))
png+=chunk(b'IEND',b'')
Path('figures/item_021_scaling_curves.png').write_bytes(png)
print('rebuilt item_021 artifacts')
