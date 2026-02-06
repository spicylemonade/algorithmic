from typing import Iterable, List, Sequence, Tuple
import math

Point = Tuple[float, float, float]


def euclidean(a: Point, b: Point) -> float:
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def directed_hausdorff(a: Sequence[Point], b: Sequence[Point]) -> float:
    return max(min(euclidean(x, y) for y in b) for x in a)


def hausdorff_distance(a: Sequence[Point], b: Sequence[Point]) -> float:
    return max(directed_hausdorff(a, b), directed_hausdorff(b, a))


def volumetric_iou(vox_a: Iterable[Tuple[int, int, int]], vox_b: Iterable[Tuple[int, int, int]]) -> float:
    sa = set(vox_a)
    sb = set(vox_b)
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 1.0


def rms_residual(observed: Sequence[float], predicted: Sequence[float]) -> float:
    if len(observed) != len(predicted) or not observed:
        raise ValueError("observed and predicted must have equal non-zero length")
    return math.sqrt(sum((o-p)**2 for o, p in zip(observed, predicted))/len(observed))


def spin_vector_angular_error_deg(v_true: Point, v_est: Point) -> float:
    dot = sum(a*b for a,b in zip(v_true, v_est))
    nt = math.sqrt(sum(a*a for a in v_true))
    ne = math.sqrt(sum(a*a for a in v_est))
    if nt == 0 or ne == 0:
        raise ValueError("spin vectors must be non-zero")
    c = max(-1.0, min(1.0, dot/(nt*ne)))
    return math.degrees(math.acos(c))
