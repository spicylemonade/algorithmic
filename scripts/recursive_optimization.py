#!/usr/bin/env python3
import json
import math
from pathlib import Path

from src.lci.metrics import hausdorff_distance, volumetric_iou
from src.lci.interfaces import Observation, Geometry, ConvexParams
from src.lci.convex_engine import ConvexOptimizer, ForwardModel

SEED = 42
MAX_ITER = 8

TARGETS = [
    {
        "name": "433_Eros",
        "photometry": "data/raw/ground_truth/eros/lc.json",
        "reference_mesh": "data/raw/ground_truth/eros/shape_damit.obj",
    },
    {
        "name": "216_Kleopatra",
        "photometry": "data/raw/ground_truth/kleopatra/lc.json",
        "reference_mesh": "data/raw/ground_truth/kleopatra/shape_jpl.obj",
    },
    {
        "name": "25143_Itokawa",
        "photometry": "data/raw/ground_truth/itokawa/pds_extract/gbo.ast-itokawa.torino.polarimetry_V1_1/data/itokawapolar.tab",
        "reference_mesh": "data/raw/ground_truth/itokawa/shape_jpl.mod",
    },
]


def read_mesh(path: str):
    pts = []
    for ln in Path(path).read_text(errors="ignore").splitlines():
        ls = ln.strip().split()
        if not ls:
            continue
        if ls[0] == "v" and len(ls) >= 4:
            try:
                pts.append((float(ls[1]), float(ls[2]), float(ls[3])))
            except Exception:
                pass
        elif len(ls) == 3 and all(x.replace(".", "", 1).replace("-", "", 1).isdigit() for x in ls):
            # fallback for .mod-like XYZ-only lines
            try:
                pts.append((float(ls[0]), float(ls[1]), float(ls[2])))
            except Exception:
                pass
    return pts


def normalize_points(points):
    if not points:
        return []
    xs, ys, zs = zip(*points)
    cx, cy, cz = sum(xs)/len(xs), sum(ys)/len(ys), sum(zs)/len(zs)
    centered = [(x-cx, y-cy, z-cz) for x,y,z in points]
    r = max(math.sqrt(x*x+y*y+z*z) for x,y,z in centered) or 1.0
    return [(x/r, y/r, z/r) for x,y,z in centered]


def voxelize(points, scale=30):
    vox=[]
    for x,y,z in points:
        vox.append((int(round((x+1)*scale)), int(round((y+1)*scale)), int(round((z+1)*scale))))
    return vox


def parse_obs(path):
    if path.endswith('.json'):
        data=json.loads(Path(path).read_text())
        rows=data if isinstance(data,list) else data.get('lightCurves', data.get('data', []))
        out=[]
        for i,r in enumerate(rows[:400]):
            jd=float(r.get('julianDate', r.get('jd', 2459000+i*0.01)))
            mag=float(r.get('brightness', r.get('mag', 0.0)))
            out.append(Observation(jd, mag, 0.05, Geometry((1,0,0),(0,1,0),30.0),'V'))
        return out
    out=[]
    for i,ln in enumerate(Path(path).read_text().splitlines()):
        p=ln.strip().split()
        if len(p)<2: continue
        try:
            mag=float(p[-1])
        except Exception:
            continue
        out.append(Observation(2453000+i*0.01, mag, 0.1, Geometry((1,0,0),(0,1,0),25.0),'V'))
    return out[:400]


def run_target(t):
    obs = parse_obs(t['photometry'])
    hist=[]
    lr=0.01
    period_step=0.05
    success=False
    final_mesh=None
    for it in range(1, MAX_ITER+1):
        init=ConvexParams(8.0,120.0,-20.0,0.0,[0.1]*12,[0.2,0.1])
        opt=ConvexOptimizer(learning_rate=lr,max_iter=40)
        fit=opt.run(obs,init)
        mesh=opt.to_mesh(fit)
        final_mesh=mesh
        pred=normalize_points(mesh.vertices)
        ref=normalize_points(read_mesh(t['reference_mesh']))
        if not ref:
            h=1.0; iou=0.0
        else:
            # downsample for speed
            ref_s=ref[::max(1,len(ref)//800)]
            pred_s=pred[::max(1,len(pred)//800)]
            h=hausdorff_distance(pred_s, ref_s)
            iou=volumetric_iou(voxelize(pred_s), voxelize(ref_s))
        dev=max(h, 1.0-iou)
        hist.append({"iteration":it,"lr":lr,"period_step":period_step,"hausdorff":h,"iou":iou,"deviation":dev})
        if dev <= 0.05:
            success=True
            break
        # recursive adjustment rule
        lr = max(0.001, lr*0.8)
        period_step = max(0.002, period_step*0.5)
    out_path=Path(f"data/processed/blinded_runs/{t['name']}_recursive.obj")
    if final_mesh:
        txt=[]
        for x,y,z in final_mesh.vertices: txt.append(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        for a,b,c in final_mesh.faces: txt.append(f"f {a+1} {b+1} {c+1}\n")
        out_path.write_text(''.join(txt))
    return {"target":t['name'],"success":success,"iterations":len(hist),"history":hist,"output_mesh":str(out_path)}


def main():
    results=[run_target(t) for t in TARGETS]
    Path('results/item_018_recursive_optimization.json').write_text(json.dumps({"item_id":"item_018","seed":SEED,"max_iter":MAX_ITER,"targets":results}, indent=2))


if __name__=='__main__':
    main()
