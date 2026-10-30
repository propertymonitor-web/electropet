"""Skeleton-built bodies for the quadruped pets (see organic.py).  Design units, facing right, ground at GROUND."""
import math
from organic import ellipse, seg, chain, curve_chain, leg


def _shift(x, dy, dx=0.0):
    """move design geometry (a point, a polygon, or any nesting of them) by dy (and dx)"""
    if isinstance(x, tuple) and len(x) == 2 and isinstance(x[0], (int, float)):
        return (x[0] + dx, x[1] + dy)
    if isinstance(x, tuple) and x and isinstance(x[0], str):
        return (x[0], _shift(x[1], dy, dx)) + tuple(x[2:])
    return [_shift(i, dy, dx) for i in x]


def _xshift(g, dx):
    """move everything that is not a leg to the right (room for a long tail); legs follow through g["_XO"]"""
    for k in ("BODY", "HEAD_SIDE", "EAR_SIDE", "HEAD_FRONT", "EAR_FRONT"):
        g[k] = _shift(g[k], 0.0, dx)
    g["TAILS"] = {k: _shift(v, 0.0, dx) for k, v in g["TAILS"].items()}
    g["NECK"] = (g["NECK"][0] + dx, g["NECK"][1])
    g["FCX"] += dx
    e, n = g["HEAD_SIDE_KEY"]["eye"], g["HEAD_SIDE_KEY"]["nose"]
    g["HEAD_SIDE_KEY"] = dict(eye=(e[0] + dx, e[1]), nose=(n[0] + dx, n[1]))


def _to_body_frame(g):
    """The generator adds PAD to everything that is not a leg, so geometry written against the ground line is moved up by PAD."""
    d = -g["PAD"]
    for k in ("BODY", "HEAD_SIDE", "EAR_SIDE", "HEAD_FRONT", "EAR_FRONT", "TAILS_LIST"):
        if k in g:
            g[k] = _shift(g[k], d)
    g["TAILS"] = {k: _shift(v, d) for k, v in g["TAILS"].items()}
    g["NECK"] = (g["NECK"][0], g["NECK"][1] + d)
    g["FCY"] += d
    e, n = g["HEAD_SIDE_KEY"]["eye"], g["HEAD_SIDE_KEY"]["nose"]
    g["HEAD_SIDE_KEY"] = dict(eye=(e[0], e[1] + d), nose=(n[0], n[1] + d))


def _walk_legs(g, spec):
    """spec: hips (hind_near, hind_far, fore_near, fore_far) x positions, and the bone sizes; returns a builder"""
    G = lambda: g["GROUND"]
    def build(offs, lk):
        hip_y = g["GROUND"] - (g["GROUND"] - spec["hip_y"]) * lk
        polys = []
        order = [1, 3, 0, 2]                                  # far legs first, then the near ones
        for i in order:
            hind = i < 2
            hx = spec["hip_x"][i]
            dx, lift = offs[i]
            foot = (spec["foot_x"][i] + dx, g["GROUND"] - lift)
            s = spec["hind"] if hind else spec["fore"]
            near = i in (0, 2)
            k = 1.0 if near else 0.88
            polys += leg((hx, hip_y), foot, s["l1"] * lk, s["l2"] * lk, s["ank"] * (0.7 + 0.3 * lk), s["bend"],
                         s["w"][0] * k, s["w"][1] * k, s["w"][2] * k, s["w"][3] * k, s["paw"][0], s["paw"][1], hind)
        return polys
    return build


def apply_wolf(g):
    g["STAGES"] = [("pup", 0.70, 1.40, 0.82), ("juvenile", 0.88, 1.15, 0.94), ("adult", 1.04, 1.0, 1.0)]
    g["HIP"] = g["GROUND"] - 22.0
    # torso: deep chest, tucked waist, strong rump, a rise at the withers
    g["BODY"] = [ellipse(14.5, 26.5, 8.2, 7.8), ellipse(24.5, 26.0, 9.8, 6.3), ellipse(35.5, 26.8, 10.2, 8.2),
                 ellipse(37.5, 21.5, 8.4, 5.4), ellipse(12.5, 23.0, 5.6, 5.0),
                 ("cutline", [(17.5, 22.0), (19.8, 26.5), (19.0, 31.0)], 0.7),                 # the haunch
                 ("cutline", [(33.0, 22.5), (31.8, 27.0), (33.0, 31.5)], 0.7)]                  # the shoulder
    # head: neck, skull, long muzzle, jaw
    neck = chain([(36.0, 21.5), (41.0, 18.5), (45.5, 16.5)], [6.0, 5.2, 4.6], 5)
    skull = [ellipse(49.5, 15.5, 6.6, 5.6, -0.1)]
    muzzle = [[(52.5, 12.2), (58.5, 13.2), (63.4, 14.6), (64.2, 16.2), (63.2, 17.8), (58.0, 18.8), (52.5, 20.0)]]
    jaw = [[(50.0, 18.5), (57.0, 18.9), (61.5, 18.3), (60.5, 19.8), (54.0, 21.3), (49.0, 23.0)]]
    ruff = [[(36.0, 28.0), (41.0, 30.5), (45.0, 28.5), (48.0, 23.5), (44.0, 22.5), (38.0, 23.5)]]
    g["HEAD_SIDE"] = neck + skull + muzzle + jaw + ruff
    g["HEAD_SIDE_KEY"] = dict(eye=(51.2, 13.9), nose=(63.4, 15.6))
    g["EAR_SIDE"] = [
        [(46.0, 11.5), (47.2, 2.0), (52.8, 10.5)],                                   # tall erect
        [(45.8, 11.5), (46.2, 4.5), (49.6, 3.3), (52.8, 10.5)],                       # rounded
        [(45.8, 11.5), (46.0, 4.5), (49.0, 3.0), (51.0, 6.0), (52.8, 10.5)],          # folded tip
    ]
    g["NECK"] = (38.0, 21.0)
    g["FCX"], g["FCY"] = 47.0, 17.0
    face = [ellipse(47.0, 15.5, 9.6, 8.2), ellipse(47.0, 22.0, 4.6, 5.4), ellipse(47.0, 20.0, 10.8, 4.6)]
    g["HEAD_FRONT"] = face
    fx, fy = 47.0, 17.0
    g["EAR_FRONT"] = [
        [[(fx - 9.5, fy - 5), (fx - 9.0, fy - 17), (fx - 3.0, fy - 8)], [(fx + 9.5, fy - 5), (fx + 9.0, fy - 17), (fx + 3.0, fy - 8)]],
        [[(fx - 9.5, fy - 5), (fx - 10.0, fy - 13), (fx - 3.0, fy - 8)], [(fx + 9.5, fy - 5), (fx + 10.0, fy - 13), (fx + 3.0, fy - 8)]],
        [[(fx - 9.5, fy - 5), (fx - 8.0, fy - 13), (fx - 3.0, fy - 8), (fx - 12.5, fy - 8)], [(fx + 9.5, fy - 5), (fx + 8.0, fy - 13), (fx + 3.0, fy - 8), (fx + 12.5, fy - 8)]],
    ]
    g["FRONT_EYE"] = ((-5.5, -2), (3.5, -2))
    g["FRONT_NOSE"] = (-1.0, 9)
    g["FRONT_MOUTH"] = ((-3, 11), (2, 15))
    spec = dict(
        hip_y=g["GROUND"] - 22.0,
        hip_x=(14.5, 20.0, 36.0, 32.5),
        foot_x=(14.0, 19.5, 37.5, 33.5),
        hind=dict(l1=9.6, l2=8.4, ank=6.5, bend=1, w=(3.9, 2.4, 1.5, 1.3), paw=(6.0, 3.0)),
        fore=dict(l1=8.4, l2=8.0, ank=6.0, bend=-1, w=(3.4, 2.1, 1.5, 1.3), paw=(6.0, 3.0)),
    )
    g["LEG_BUILDER"] = _walk_legs(g, spec)
    g["TAILS"] = {
        0: [curve_chain([(9, 23), (3, 26), (1, 34), (5.5, 43)], [2.6, 4.4, 4.6, 0.8], 12),
            curve_chain([(9, 23), (2.5, 25), (1, 32), (3, 42)], [2.6, 4.4, 4.6, 0.8], 12)],
        1: [curve_chain([(9, 23), (3, 21), (0.5, 13), (5, 6)], [2.4, 3.6, 3.4, 0.8], 12),
            curve_chain([(9, 23), (3, 20), (1.5, 11), (7, 5)], [2.4, 3.6, 3.4, 0.8], 12)],
        2: [curve_chain([(9, 23), (4, 25), (0, 28), (-1, 34)], [2.4, 3.8, 3.8, 0.8], 12),
            curve_chain([(9, 23), (4, 24), (0, 25.5), (-1, 31)], [2.4, 3.8, 3.8, 0.8], 12)],
    }
    _to_body_frame(g)

def _face(g, cx, cy, parts, eye=((-5.5, -2), (3.5, -2)), nose=(-1.0, 9), mouth=((-3, 11), (2, 15))):
    g["FCX"], g["FCY"] = cx, cy
    g["HEAD_FRONT"] = parts
    g["FRONT_EYE"], g["FRONT_NOSE"], g["FRONT_MOUTH"] = eye, nose, mouth


def _ears_front(g, fx, fy, spread, tall, kinds):
    """three front-facing ear styles from (spread = distance of the ear base from the middle, tall = height, kinds = per style tall values)"""
    out = []
    for (h, tipx, drop) in kinds:
        left = [(fx - spread, fy - 5), (fx - tipx, fy - 5 - h), (fx - 3.0, fy - 8)]
        right = [(fx + spread, fy - 5), (fx + tipx, fy - 5 - h), (fx + 3.0, fy - 8)]
        if drop:
            left.append((fx - spread - 3, fy - 8)); right.append((fx + spread + 3, fy - 8))
        out.append([left, right])
    g["EAR_FRONT"] = out


def _legs(g, hip_y, hip_x, foot_x, hind, fore):
    xo = g.get("_XO", 0.0)
    spec = dict(hip_y=g["GROUND"] - hip_y, hip_x=tuple(x + xo for x in hip_x), foot_x=tuple(x + xo for x in foot_x), hind=hind, fore=fore)
    g["HIP"] = g["GROUND"] - hip_y
    g["LEG_BUILDER"] = _walk_legs(g, spec)


def apply_fox(g):
    g["STAGES"] = [("pup", 0.70, 1.45, 0.84), ("juvenile", 0.88, 1.18, 0.95), ("adult", 1.04, 1.0, 1.0)]
    g["BODY"] = [ellipse(15.0, 29.0, 7.4, 6.8), ellipse(24.0, 28.5, 8.8, 5.4), ellipse(33.5, 28.8, 8.4, 6.8),
                 ellipse(35.0, 24.8, 6.8, 4.4), ellipse(13.5, 26.5, 5.0, 4.2)]
    neck = chain([(33.5, 25.0), (38.5, 22.8), (43.0, 21.8)], [4.6, 4.1, 3.8], 5)
    skull = [ellipse(46.0, 20.8, 5.5, 4.8, -0.1)]
    muzzle = [[(49.0, 18.6), (54.5, 19.4), (60.5, 20.8), (61.6, 22.0), (60.6, 23.1), (54.5, 23.6), (49.0, 24.6)]]
    jaw = [[(46.5, 23.5), (53.0, 23.8), (58.5, 23.4), (57.5, 24.6), (51.0, 26.6), (45.5, 28.0)]]
    cheek = [[(41.0, 26.0), (45.0, 29.5), (49.0, 26.5), (47.5, 22.5), (43.0, 22.0)]]
    g["HEAD_SIDE"] = neck + skull + muzzle + jaw + cheek
    g["HEAD_SIDE_KEY"] = dict(eye=(47.6, 19.2), nose=(61.0, 21.2))
    g["EAR_SIDE"] = [
        [(41.8, 19.0), (42.0, 5.5), (48.6, 17.8)],                                   # tall pointed
        [(41.8, 19.0), (41.6, 8.5), (45.8, 7.0), (48.6, 17.8)],                       # broad
        [(41.8, 19.0), (41.8, 8.0), (45.0, 6.0), (47.0, 9.0), (48.6, 17.8)],          # tip folded
    ]
    g["NECK"] = (36.0, 24.0)
    _face(g, 47.0, 19.0, [ellipse(47.0, 17.5, 8.0, 6.8), ellipse(47.0, 23.0, 3.4, 4.6), ellipse(47.0, 21.5, 9.6, 3.8)],
          eye=((-5.0, -2), (3.0, -2)), nose=(-1.0, 8), mouth=((-3, 9), (2, 12)))
    _ears_front(g, 47.0, 19.0, 7.5, 0, [(14, 9.0, False), (10, 9.4, False), (9, 7.6, True)])
    _legs(g, 21.0, (15.0, 20.0, 33.5, 30.0), (14.5, 19.5, 35.0, 31.0),
          dict(l1=8.4, l2=7.8, ank=6.4, bend=1, w=(3.2, 2.0, 1.3, 1.1), paw=(5.0, 2.6)),
          dict(l1=7.8, l2=7.6, ank=6.2, bend=-1, w=(2.8, 1.8, 1.3, 1.1), paw=(5.0, 2.6)))
    g["TAILS"] = {
        0: [curve_chain([(9.5, 28), (3, 30), (0.5, 37), (4.5, 45.5)], [2.0, 4.8, 5.4, 0.9], 12),
            curve_chain([(9.5, 28), (2.5, 29), (0.5, 35), (3, 44)], [2.0, 4.8, 5.4, 0.9], 12)],
        1: [curve_chain([(9.5, 28), (4, 27), (0.5, 28.5), (0.5, 35)], [2.0, 4.4, 4.8, 0.9], 12),
            curve_chain([(9.5, 28), (4, 26), (0.5, 26.5), (0.5, 33)], [2.0, 4.4, 4.8, 0.9], 12)],
        2: [curve_chain([(9.5, 28), (3.5, 26), (0.8, 18), (5, 10.5)], [2.0, 4.0, 4.4, 0.9], 12),
            curve_chain([(9.5, 28), (3.5, 25), (1.5, 16.5), (7, 9.5)], [2.0, 4.0, 4.4, 0.9], 12)],
    }
    if not g.get("_KEEP_FRAME"):
        _to_body_frame(g)


def apply_cat(g):
    g["STAGES"] = [("pup", 0.72, 1.35, 0.86), ("juvenile", 0.90, 1.15, 0.95), ("adult", 1.04, 1.05, 1.0)]
    g["BODY"] = [ellipse(15.5, 29.5, 7.8, 7.4), ellipse(25.0, 29.0, 8.8, 6.0), ellipse(34.0, 29.0, 7.6, 7.0),
                 ellipse(35.0, 25.0, 6.2, 4.6)]
    neck = chain([(34.0, 25.5), (38.0, 23.5), (41.5, 22.5)], [4.8, 4.5, 4.4], 5)
    skull = [ellipse(45.0, 21.6, 6.2, 5.4)]
    muzzle = [[(48.5, 20.4), (52.5, 20.6), (54.6, 22.4), (54.2, 24.4), (51.0, 25.4), (47.5, 25.6)]]
    jaw = [[(44.0, 25.0), (50.0, 26.0), (51.5, 27.0), (46.0, 29.0), (41.0, 28.5)]]
    whisk = [[(53.5, 21.8), (60.0, 19.8), (60.0, 20.8), (53.5, 22.8)], [(53.5, 23.4), (60.0, 24.4), (60.0, 25.4), (53.0, 24.4)]]
    g["HEAD_SIDE"] = neck + skull + muzzle + jaw + whisk
    g["HEAD_SIDE_KEY"] = dict(eye=(48.2, 20.2), nose=(53.8, 22.4))
    g["EAR_SIDE"] = [
        [(41.0, 19.0), (42.4, 10.0), (48.4, 17.6)],
        [(41.0, 19.0), (42.0, 11.0), (46.5, 10.2), (48.4, 17.6)],
        [(41.0, 19.0), (41.8, 10.5), (45.0, 9.5), (46.8, 12.5), (48.4, 17.6)],
    ]
    g["NECK"] = (36.0, 24.5)
    _face(g, 47.0, 19.5, [ellipse(47.0, 18.0, 9.4, 7.8), ellipse(47.0, 23.5, 3.6, 3.6), ellipse(47.0, 21.5, 10.4, 4.2)],
          eye=((-5.5, -2), (3.5, -2)), nose=(-1.0, 7), mouth=((-3, 9), (2, 12)))
    _ears_front(g, 47.0, 19.5, 7.8, 0, [(10, 8.4, False), (8, 9.0, False), (8, 7.4, True)])
    _legs(g, 21.0, (15.0, 20.0, 33.0, 29.5), (14.5, 19.5, 34.5, 30.5),
          dict(l1=8.6, l2=7.8, ank=6.0, bend=1, w=(3.4, 2.1, 1.4, 1.3), paw=(4.6, 2.6)),
          dict(l1=7.8, l2=7.6, ank=6.0, bend=-1, w=(3.0, 1.9, 1.4, 1.3), paw=(4.6, 2.6)))
    g["TAILS"] = {
        0: [curve_chain([(9, 27), (3, 28), (1, 36), (6, 44)], [2.0, 2.4, 2.5, 1.4], 12),
            curve_chain([(9, 27), (2.5, 27), (0.5, 34), (3.5, 43)], [2.0, 2.4, 2.5, 1.4], 12)],
        1: [curve_chain([(9, 27), (4, 24), (1.5, 15), (4.5, 9)], [2.0, 2.4, 2.5, 1.5], 12),
            curve_chain([(9, 27), (4, 23), (2.5, 13), (6.5, 8)], [2.0, 2.4, 2.5, 1.5], 12)],
        2: [curve_chain([(9, 27), (4, 28), (0.5, 31), (-0.5, 38)], [2.0, 2.4, 2.4, 1.4], 12),
            curve_chain([(9, 27), (4, 27), (0.5, 28), (0, 35)], [2.0, 2.4, 2.4, 1.4], 12)],
    }
    _to_body_frame(g)


def apply_bear(g):
    g["STAGES"] = [("pup", 0.70, 1.30, 0.82), ("juvenile", 0.88, 1.12, 0.94), ("adult", 1.02, 1.0, 1.0)]
    g["BODY"] = [ellipse(15.0, 26.0, 8.6, 8.0), ellipse(25.0, 26.0, 9.6, 7.4), ellipse(35.0, 26.5, 9.8, 8.0),
                 ellipse(33.5, 18.0, 9.4, 6.8)]                                         # the shoulder hump
    neck = chain([(37.0, 22.0), (42.0, 26.5), (46.5, 30.0)], [7.0, 6.2, 5.4], 5)
    skull = [ellipse(50.0, 30.2, 6.6, 6.0)]
    muzzle = [[(53.5, 28.6), (58.5, 29.6), (62.5, 31.4), (63.3, 33.0), (61.9, 34.4), (56.5, 35.0), (52.5, 35.6)]]
    jaw = [[(49.0, 34.0), (55.5, 35.0), (59.0, 35.0), (53.5, 37.4), (48.0, 37.6)]]
    ear = ellipse(46.0, 19.0, 3.3, 3.3)
    g["HEAD_SIDE"] = neck + skull + muzzle + jaw
    g["HEAD_SIDE_KEY"] = dict(eye=(53.5, 28.6), nose=(62.5, 31.6))
    g["EAR_SIDE"] = [ellipse(46.5, 25.0, 3.6, 3.6), ellipse(46.5, 25.0, 4.0, 3.4), ellipse(46.5, 25.5, 3.3, 3.8)]
    g["NECK"] = (38.0, 23.0)
    _face(g, 47.0, 19.0, [ellipse(47.0, 18.0, 10.4, 9.0), ellipse(47.0, 24.0, 5.4, 5.0)],
          eye=((-6.0, -2), (4.0, -2)), nose=(-1.0, 8), mouth=((-3, 10), (2, 14)))
    g["EAR_FRONT"] = [[ellipse(47.0 - 9.0, 19.0 - 9.5, 3.2, 3.2), ellipse(47.0 + 9.0, 19.0 - 9.5, 3.2, 3.2)]] * 3
    _legs(g, 23.0, (14.5, 20.5, 35.5, 31.0), (14.0, 19.5, 36.5, 32.0),
          dict(l1=9.0, l2=8.2, ank=6.0, bend=1, w=(4.2, 3.0, 2.4, 2.2), paw=(7.0, 3.6)),
          dict(l1=8.8, l2=8.0, ank=6.0, bend=-1, w=(3.9, 2.8, 2.4, 2.2), paw=(7.0, 3.6)))
    g["TAILS"] = {i: [chain([(8, 21), (5.0, 21.5)], [2.0, 2.2], 4), chain([(8, 21), (5.0, 22.5)], [2.0, 2.2], 4)] for i in range(3)}
    _to_body_frame(g)


def apply_pig(g):
    g["STAGES"] = [("pup", 0.72, 1.30, 0.80), ("juvenile", 0.90, 1.12, 0.93), ("adult", 1.04, 1.0, 1.0)]
    g["BODY"] = [ellipse(16.0, 27.0, 9.0, 7.6), ellipse(26.0, 27.5, 9.6, 7.8), ellipse(35.0, 27.5, 9.2, 7.8),
                 ellipse(28.0, 22.0, 12.0, 3.6)]
    neck = chain([(37.0, 25.0), (41.0, 25.0), (44.0, 25.0)], [6.2, 5.8, 5.4], 5)
    skull = [ellipse(46.5, 24.5, 6.6, 6.0)]
    snout = [[(50.0, 22.0), (55.5, 22.6), (59.5, 23.4), (60.5, 25.0), (60.0, 28.0), (55.5, 28.6), (50.0, 29.0)]]
    jaw = [[(46.0, 28.5), (52.0, 29.5), (50.0, 31.0), (44.0, 31.0)]]
    g["HEAD_SIDE"] = neck + skull + snout + jaw
    g["HEAD_SIDE_KEY"] = dict(eye=(51.0, 22.4), nose=(59.6, 25.2))
    g["EAR_SIDE"] = [
        [(44.0, 20.0), (44.4, 12.0), (50.4, 18.5)],
        [(44.0, 20.0), (44.0, 14.0), (49.5, 14.5), (50.4, 19.0)],
        [(44.0, 20.0), (45.0, 13.0), (49.0, 14.5), (47.0, 17.0), (50.4, 19.0)],
    ]
    g["NECK"] = (38.0, 24.5)
    _face(g, 47.0, 20.5, [ellipse(47.0, 19.0, 9.4, 8.0), ellipse(47.0, 26.0, 5.8, 4.2)],
          eye=((-5.5, -2), (3.5, -2)), nose=(-1.0, 8), mouth=((-3, 10), (2, 13)))
    _ears_front(g, 47.0, 20.5, 8.0, 0, [(9, 10.0, True), (8, 10.0, True), (8, 9.0, True)])
    _legs(g, 18.0, (15.5, 21.0, 35.0, 31.0), (15.0, 20.5, 36.0, 32.0),
          dict(l1=7.2, l2=6.2, ank=5.0, bend=1, w=(4.0, 2.8, 2.0, 1.9), paw=(4.8, 2.6)),
          dict(l1=7.0, l2=6.0, ank=5.0, bend=-1, w=(3.8, 2.6, 2.0, 1.9), paw=(4.8, 2.6)))
    g["TAILS"] = {
        0: [curve_chain([(8, 24), (4, 22), (3, 18), (6, 16)], [1.4, 1.2, 1.2, 1.0], 10),
            curve_chain([(8, 24), (4, 23), (2, 19), (4, 16)], [1.4, 1.2, 1.2, 1.0], 10)],
        1: [curve_chain([(8, 24), (4, 24), (2, 28), (4, 32)], [1.4, 1.2, 1.2, 1.0], 10),
            curve_chain([(8, 24), (4, 23), (1.5, 27), (3, 31)], [1.4, 1.2, 1.2, 1.0], 10)],
        2: [curve_chain([(8, 24), (4, 21), (2, 17), (5, 14)], [1.4, 1.2, 1.2, 1.0], 10),
            curve_chain([(8, 24), (4, 22), (3, 18), (6, 15)], [1.4, 1.2, 1.2, 1.0], 10)],
    }
    _to_body_frame(g)


def _equine_o(g, kind):
    """horse / donkey / unicorn.  Coordinates are written as heights above the ground line (H) and turned into design y."""
    pad = 14
    g["PAD"] = pad; g["DESIGN_H"] = 44 + pad; g["GROUND"] = 43.0 + pad; g["DESIGN_W"] = 74
    G = g["GROUND"]
    Y = lambda h: G - h
    donkey, uni = kind == "donkey", kind == "unicorn"
    sc = 0.92 if not donkey else 0.9
    g["STAGES"] = [("pup", 0.62, 1.30, 0.82), ("juvenile", 0.78, 1.12, 0.93), ("adult", 0.94 if not donkey else 0.92, 1.0, 1.0)]
    low = 3.0 if donkey else 0.0              # a donkey stands a little lower
    g["BODY"] = [ellipse(13.0, Y(30.0 - low), 8.2, 8.4), ellipse(25.0, Y(28.5 - low), 11.0, 7.4), ellipse(37.0, Y(29.0 - low), 8.6, 8.4),
                 ellipse(36.5, Y(34.0 - low), 6.6, 4.6)]
    if donkey:
        neck_pts = [(38.0, Y(32.0 - low)), (43.5, Y(36.0 - low)), (48.5, Y(40.0 - low))]
        hx, hy = 52.0, 40.0 - low
    else:
        neck_pts = [(38.0, Y(33.0)), (43.0, Y(39.0)), (48.5, Y(45.5))]
        hx, hy = 52.5, 45.0
    neck = chain(neck_pts, [6.2, 4.8, 3.8], 5)
    # head: a long wedge pointing forward and down
    ax, ay = hx, hy
    head = chain([(ax, Y(ay)), (ax + 6.0, Y(ay - 4.4)), (ax + 11.2, Y(ay - 8.0))], [4.2, 3.4, 3.0], 5)
    head += [ellipse(ax + 2.2, Y(ay - 3.0), 4.4, 3.4, 0.5)]                                    # the jaw
    nose = (ax + 11.8, ay - 8.4)
    crest = [(38.0, Y(36.0 - low)), (41.5, Y(41.5 - low if donkey else 43.0)), (46.0, Y(48.0 - low if donkey else 50.5)), (49.0, Y(hy + 4.0)),
             (46.0, Y(44.0 - low if donkey else 46.0)), (42.0, Y(38.0 - low))]
    if not donkey:
        head.append(crest)                                                                      # the mane along the crest
    horn = []
    if uni:
        horn = [[(ax + 3.0, Y(ay + 3.2)), (ax + 12.5, Y(ay + 15.5)), (ax + 5.2, Y(ay + 2.4))]]   # the horn from the forehead
    g["HEAD_SIDE"] = neck + head + horn
    g["HEAD_SIDE_KEY"] = dict(eye=(ax + 2.0, Y(ay + 1.2)), nose=(nose[0], Y(nose[1])))
    if donkey:
        g["EAR_SIDE"] = [[(ax - 3.4, Y(ay + 2.0)), (ax - 6.0, Y(ay + 13.5)), (ax - 0.8, Y(ay + 12.5)), (ax + 0.6, Y(ay + 2.0))],
                         [(ax - 3.4, Y(ay + 2.0)), (ax - 8.0, Y(ay + 9.5)), (ax - 3.4, Y(ay + 11.0)), (ax + 0.6, Y(ay + 2.0))],
                         [(ax - 3.4, Y(ay + 2.0)), (ax - 9.0, Y(ay + 6.5)), (ax - 4.5, Y(ay + 9.0)), (ax + 0.6, Y(ay + 2.0))]]
    else:
        g["EAR_SIDE"] = [[(ax - 2.6, Y(ay + 2.4)), (ax - 2.2, Y(ay + 8.4)), (ax + 1.0, Y(ay + 2.4))],
                         [(ax - 2.6, Y(ay + 2.4)), (ax - 3.4, Y(ay + 6.4)), (ax + 1.0, Y(ay + 2.4))],
                         [(ax - 2.6, Y(ay + 2.4)), (ax - 3.8, Y(ay + 5.4)), (ax + 1.0, Y(ay + 2.4))]]
    g["NECK"] = (40.0, Y(34.0 - low))
    fy = Y(hy - 2.0)
    _face(g, 47.0, fy, [ellipse(47.0, fy - 2.0, 5.6, 8.0), ellipse(47.0, fy + 6.0, 4.0, 5.6)] + ([[(45.8, fy - 8.0), (47.0, fy - 22.0), (48.2, fy - 8.0)]] if uni else []),
          eye=((-4.6, -4), (2.6, -4)), nose=(-1.0, 11), mouth=((-3, 12), (2, 15)))
    if donkey:
        _ears_front(g, 47.0, fy - 3.0, 5.0, 0, [(17, 9.0, False), (14, 11.0, False), (11, 11.0, True)])
    else:
        _ears_front(g, 47.0, fy - 3.0, 4.6, 0, [(8, 6.5, False), (6, 6.8, False), (6, 6.0, True)])
    hs = 24.0 - low
    _legs(g, hs, (12.5, 17.5, 38.0, 34.0), (12.0, 17.0, 39.5, 35.5),
          dict(l1=9.6, l2=8.6, ank=8.0, bend=1, w=(4.0, 2.4, 1.5, 1.4), paw=(4.4, 2.6)),
          dict(l1=8.8, l2=7.8, ank=8.0, bend=-1, w=(3.4, 2.0, 1.5, 1.4), paw=(4.4, 2.6)))
    g["HIP"] = G - hs
    if donkey:
        g["TAILS"] = {i: [curve_chain([(7.5, Y(30)), (5, Y(24)), (4.5, Y(14)), (5.5, Y(8))], [1.4, 1.2, 1.3, 2.2], 10),
                          curve_chain([(7.5, Y(30)), (4.5, Y(24)), (3.5, Y(14)), (4.5, Y(8))], [1.4, 1.2, 1.3, 2.2], 10)] for i in range(3)}
    else:
        g["TAILS"] = {
            0: [curve_chain([(7.5, Y(32)), (2.0, Y(26)), (1.0, Y(14)), (3.5, Y(5))], [2.0, 3.8, 3.4, 0.8], 12),
                curve_chain([(7.5, Y(32)), (1.5, Y(25)), (0.5, Y(13)), (2.5, Y(6))], [2.0, 3.8, 3.4, 0.8], 12)],
            1: [curve_chain([(7.5, Y(32)), (2.5, Y(33)), (0.5, Y(24)), (3.0, Y(17))], [2.0, 3.4, 3.2, 0.8], 12),
                curve_chain([(7.5, Y(32)), (2.0, Y(34)), (0.5, Y(26)), (2.5, Y(20))], [2.0, 3.4, 3.2, 0.8], 12)],
            2: [curve_chain([(7.5, Y(32)), (3.0, Y(31)), (0.5, Y(26)), (0.5, Y(18))], [2.0, 3.4, 3.2, 0.8], 12),
                curve_chain([(7.5, Y(32)), (3.0, Y(32)), (0.8, Y(28)), (1.0, Y(21))], [2.0, 3.4, 3.2, 0.8], 12)],
        }
    _to_body_frame(g)


def apply_horse(g): _equine_o(g, "horse")
def apply_donkey(g): _equine_o(g, "donkey")
def apply_unicorn(g): _equine_o(g, "unicorn")


def apply_kitsune(g):
    """a fox with a fan of three great plume tails and bigger ears"""
    g["_KEEP_FRAME"] = True
    g["_XO"] = 12.0
    g["PAD"] = 12; g["DESIGN_H"] = 44 + 12; g["GROUND"] = 43.0 + 12; g["DESIGN_W"] = 78
    apply_fox(g)
    g["STAGES"] = [("pup", 0.58, 1.45, 0.86), ("juvenile", 0.72, 1.18, 0.95), ("adult", 0.86, 1.0, 1.0)]
    G = g["GROUND"]
    # re-base the fox (written for a ground at 51) onto this ground line
    dy = G - 51.0
    for k in ("BODY", "HEAD_SIDE", "EAR_SIDE", "HEAD_FRONT", "EAR_FRONT"):
        g[k] = _shift(g[k], dy)
    g["FCY"] += dy
    e, n = g["HEAD_SIDE_KEY"]["eye"], g["HEAD_SIDE_KEY"]["nose"]
    g["HEAD_SIDE_KEY"] = dict(eye=(e[0], e[1] + dy), nose=(n[0], n[1] + dy))
    g["NECK"] = (g["NECK"][0], g["NECK"][1] + dy)
    _xshift(g, g["_XO"])
    g["HIP"] = G - 21.0
    # the plumes: three tapering tails fanned from the rump
    rx, ry = 9.5 + g["_XO"], G - 23.0
    def plume(ang, ln, wid, wag):
        a = math.radians(ang + wag)
        mx, my = rx + math.cos(a) * ln * 0.5, ry + math.sin(a) * ln * 0.5 + 2.0
        ex, ey = rx + math.cos(a + 0.35) * ln, ry + math.sin(a + 0.35) * ln
        return curve_chain([(rx, ry), (rx + math.cos(a) * ln * 0.3, ry + math.sin(a) * ln * 0.3), (mx, my), (ex, ey)], [1.8, wid, wid * 0.9, 0.8], 12)
    def fan(angs, ln, wid, wag):
        return [sum([plume(a, ln, wid, w) for a in angs], []) for w in (0, wag)]
    g["TAILS"] = {0: fan((200, 222, 244), 25, 6.2, 5), 1: fan((168, 186, 204), 26, 6.0, 5), 2: fan((212, 234, 256), 25, 6.0, 6)}
    _to_body_frame(g)


def _reptile_o(g, croc):
    """alligator (broad, heavy, round snout) and crocodile (leaner, long pointed snout, teeth showing)"""
    pad = 8
    g["PAD"] = pad; g["DESIGN_H"] = 44 + pad; g["GROUND"] = 43.0 + pad; g["DESIGN_W"] = 80
    G = g["GROUND"]
    Y = lambda h: G - h
    g["STAGES"] = [("pup", 0.62, 1.30, 0.84), ("juvenile", 0.78, 1.12, 0.93), ("adult", 0.88, 1.0, 1.0)]
    r = 0.78 if croc else 1.15                    # the croc is leaner
    body = [ellipse(24.0, Y(11.5), 8.4, 6.8 * r), ellipse(33.0, Y(11.0), 9.0, 6.4 * r), ellipse(43.0, Y(11.8), 8.2, 6.6 * r)]
    # a row of raised scutes along the back
    for x in range(18, 50, 3):
        top = 17.6 * (1.0 if x < 40 else 0.97)
        body.append([(x - 0.2, Y(top - 1.0)), (x + 1.4, Y(top + 1.6)), (x + 3.0, Y(top - 1.0))])
    g["BODY"] = body
    # head: broad flat skull and a long snout
    sk = ellipse(55.0, Y(12.0), 6.4, 5.0)
    if croc:
        snout = chain([(58.0, Y(11.6)), (69.0, Y(10.4)), (79.0, Y(9.6))], [3.2, 2.2, 1.5], 5)
        lower = chain([(56.0, Y(7.6)), (66.0, Y(7.0)), (76.0, Y(7.0))], [2.6, 1.9, 1.4], 4)
        teeth = [("cut", [(74.0, Y(7.2)), (74.6, Y(5.0)), (75.4, Y(7.2))]), ("cut", [(69.0, Y(7.6)), (69.6, Y(5.4)), (70.4, Y(7.6))]),
                 ("cut", [(64.0, Y(7.8)), (64.6, Y(5.6)), (65.4, Y(7.8))]), ("cut", [(59.0, Y(8.0)), (59.6, Y(5.8)), (60.4, Y(8.0))])]
        nose = (78.5, 10.2); eye = (55.5, 16.4)
    else:
        snout = chain([(58.0, Y(11.6)), (64.0, Y(10.9)), (68.0, Y(10.2))], [5.6, 5.2, 4.6], 5)
        lower = chain([(56.0, Y(7.2)), (62.0, Y(6.6)), (67.0, Y(6.2))], [3.4, 3.2, 2.8], 4)
        teeth = []
        nose = (68.0, 10.6); eye = (55.5, 16.6)
    brow = [(53.0, Y(15.5)), (55.0, Y(18.4)), (58.0, Y(15.5))]
    neck = chain([(46.0, Y(11.5)), (50.0, Y(11.8))], [6.0, 5.2], 4)
    g["HEAD_SIDE"] = neck + [sk] + snout + lower + [brow] + teeth
    g["HEAD_SIDE_KEY"] = dict(eye=(eye[0], Y(eye[1])), nose=(nose[0], Y(nose[1])))
    g["EAR_SIDE"] = [[(52.0, Y(15.0)), (54.0, Y(19.0)), (57.0, Y(15.5))], [(52.0, Y(15.0)), (54.0, Y(18.0)), (57.5, Y(16.5))], [(52.0, Y(15.0)), (55.0, Y(18.6)), (57.0, Y(15.5))]]
    g["NECK"] = (48.0, Y(12.0))
    fw = 7.5 if croc else 9.5
    fy = Y(12.0)
    _face(g, 52.0, fy, [ellipse(52.0, fy - 1.0, fw, 6.0), ellipse(52.0, fy + 4.0, fw * 0.55, 5.0)],
          eye=((-fw + 3, -4), (fw - 5, -4)), nose=(-0.5, 7), mouth=((-5, 9), (4, 10)))
    g["EAR_FRONT"] = [[[(52.0 - fw + 2, fy - 4), (52.0 - fw + 2, fy - 8), (52.0 - 3, fy - 6)], [(52.0 + fw - 2, fy - 4), (52.0 + fw - 2, fy - 8), (52.0 + 3, fy - 6)]]] * 3
    _legs(g, 11.0, (22.0, 26.0, 44.0, 40.0), (21.0, 26.0, 45.5, 41.0),
          dict(l1=5.0, l2=4.4, ank=2.4, bend=1, w=(3.4, 2.6, 2.0, 1.8), paw=(6.0, 2.6)),
          dict(l1=4.8, l2=4.2, ank=2.4, bend=-1, w=(3.2, 2.5, 2.0, 1.8), paw=(6.0, 2.6)))
    g["HIP"] = G - 11.0
    t0 = 1.0 if croc else 1.2
    g["TAILS"] = {
        0: [curve_chain([(24.0, Y(11.5)), (14.0, Y(10.0)), (6.0, Y(5.5)), (0.5, Y(3.5))], [5.0 * t0, 4.0 * t0, 2.4, 0.8], 14),
            curve_chain([(24.0, Y(11.5)), (14.0, Y(11.0)), (6.0, Y(8.0)), (0.5, Y(6.5))], [5.0 * t0, 4.0 * t0, 2.4, 0.8], 14)],
        1: [curve_chain([(24.0, Y(11.5)), (14.0, Y(12.5)), (6.0, Y(11.0)), (0.5, Y(7.0))], [5.0 * t0, 4.0 * t0, 2.4, 0.8], 14),
            curve_chain([(24.0, Y(11.5)), (14.0, Y(10.0)), (6.0, Y(12.0)), (0.5, Y(11.5))], [5.0 * t0, 4.0 * t0, 2.4, 0.8], 14)],
        2: [curve_chain([(24.0, Y(11.5)), (14.0, Y(9.5)), (7.0, Y(9.5)), (0.5, Y(13.0))], [5.0 * t0, 4.0 * t0, 2.4, 0.8], 14),
            curve_chain([(24.0, Y(11.5)), (14.0, Y(10.5)), (7.0, Y(11.5)), (0.5, Y(15.5))], [5.0 * t0, 4.0 * t0, 2.4, 0.8], 14)],
    }
    _to_body_frame(g)


def apply_gator(g): _reptile_o(g, croc=False)
def apply_croc(g): _reptile_o(g, croc=True)


def _zig(pts, depth):
    """give an edge a feathered, ragged look: every second point is pushed out by `depth` along the edge's left normal"""
    out = []
    for i, p in enumerate(pts):
        q = pts[min(i + 1, len(pts) - 1)]
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        out.append(p if i % 2 == 0 else (p[0] + nx * depth, p[1] + ny * depth))
    return out


def apply_griffin(g):
    """lion's body and tufted tail, eagle's head with a hooked beak and feather crest, folded feathered wing"""
    g["PAD"] = 14; g["DESIGN_H"] = 58; g["GROUND"] = 57.0; g["DESIGN_W"] = 74
    G = g["GROUND"]; Y = lambda h: G - h
    g["STAGES"] = [("pup", 0.58, 1.35, 0.85), ("juvenile", 0.74, 1.15, 0.94), ("adult", 0.90, 1.0, 1.0)]
    root = (36.0, Y(36.0))
    arm = chain([root, (33.0, Y(47.0)), (27.0, Y(54.0))], [3.4, 2.4, 1.6], 4)
    feathers = []
    for i, (ex, eh) in enumerate([(24.0, 60.0), (14.0, 57.0), (6.0, 52.0), (2.5, 45.0), (2.5, 38.5)]):
        feathers += curve_chain([(31.0, Y(45.0 + i * 0.5)), (27.0 - i * 1.5, Y(50.0 - i * 0.6)), ((30.0 + ex) / 2, Y((50.0 + eh) / 2)), (ex, Y(eh))], [1.9, 1.9, 1.5, 0.5], 8)
    wing = arm + feathers + [ellipse(30.0, Y(43.0), 5.5, 4.5)]
    seam = ("cutline", [(38.5, Y(37.5)), (32.0, Y(34.8)), (25.0, Y(34.2)), (18.0, Y(36.4)), (9.0, Y(36.8))], 1.0)
    g["BODY"] = [ellipse(15.0, Y(27.5), 8.4, 7.8), ellipse(25.0, Y(27.0), 9.8, 6.8), ellipse(35.0, Y(27.8), 9.4, 8.2),
                 ellipse(37.0, Y(33.5), 7.0, 4.8)] + wing + [seam]
    neck = chain([(38.5, Y(33.0)), (43.5, Y(38.5)), (47.5, Y(43.5))], [6.2, 5.0, 4.2], 5)
    ruff = [_zig([(38.0, Y(26.0)), (42.0, Y(29.0)), (46.0, Y(33.0)), (48.5, Y(37.0)), (50.0, Y(41.0)), (44.0, Y(40.0)), (40.0, Y(36.0))], 1.6)]
    skull = [ellipse(51.5, Y(44.5), 5.2, 4.6)]
    beak = [[(54.5, Y(47.0)), (60.0, Y(46.2)), (64.5, Y(43.0)), (63.8, Y(39.6)), (61.6, Y(41.4)), (59.0, Y(42.2)), (55.0, Y(41.0))]]
    g["HEAD_SIDE"] = neck + ruff + skull + beak
    g["HEAD_SIDE_KEY"] = dict(eye=(54.0, Y(46.0)), nose=(63.0, Y(42.6)))
    g["EAR_SIDE"] = [
        [(48.5, Y(48.0)), (42.5, Y(52.5)), (47.0, Y(46.0))],
        [(48.5, Y(48.0)), (41.5, Y(50.0)), (44.5, Y(54.0)), (48.0, Y(49.5)), (51.5, Y(47.5))],
        [(48.5, Y(48.0)), (41.0, Y(49.0)), (46.5, Y(50.0)), (42.0, Y(54.5)), (49.5, Y(51.0)), (47.5, Y(57.0)), (52.0, Y(48.0))],
    ]
    g["NECK"] = (40.0, Y(35.0))
    fy = Y(44.0)
    _face(g, 54.0, fy, [ellipse(54.0, fy - 1.0, 7.4, 8.0), [(52.0, fy + 3.0), (56.0, fy + 3.0), (54.0, fy + 11.0)]],
          eye=((-5.5, -3), (3.5, -3)), nose=(-0.5, 7), mouth=((-2, 9), (2, 12)))
    _ears_front(g, 54.0, fy - 3.0, 7.0, 0, [(8, 9.5, False), (10, 7.5, False), (6, 11.0, True)])
    _legs(g, 22.0, (14.5, 20.0, 37.0, 33.0), (14.0, 19.5, 39.0, 35.0),
          dict(l1=9.8, l2=8.6, ank=7.0, bend=1, w=(4.4, 2.8, 1.8, 1.6), paw=(6.0, 3.0)),
          dict(l1=8.8, l2=8.2, ank=6.8, bend=-1, w=(4.2, 2.8, 2.2, 2.0), paw=(7.5, 3.6)))
    g["TAILS"] = {
        0: [curve_chain([(9.0, Y(28)), (3.0, Y(25)), (2.0, Y(15)), (5.5, Y(8))], [2.0, 1.8, 1.6, 1.4], 12) + [ellipse(5.8, Y(6.0), 3.2, 5.0)],
            curve_chain([(9.0, Y(28)), (2.5, Y(26)), (1.0, Y(16)), (3.5, Y(9))], [2.0, 1.8, 1.6, 1.4], 12) + [ellipse(3.8, Y(7.0), 3.2, 5.0)]],
        1: [curve_chain([(9.0, Y(28)), (3.0, Y(31)), (1.0, Y(40)), (5.0, Y(45))], [2.0, 1.8, 1.6, 1.4], 12) + [ellipse(5.4, Y(46.0), 3.2, 4.4)],
            curve_chain([(9.0, Y(28)), (2.5, Y(32)), (1.0, Y(42)), (6.0, Y(46))], [2.0, 1.8, 1.6, 1.4], 12) + [ellipse(6.6, Y(47.0), 3.2, 4.4)]],
        2: [curve_chain([(9.0, Y(28)), (3.0, Y(27)), (-0.5, Y(23)), (0.5, Y(15))], [2.0, 1.8, 1.6, 1.4], 12) + [ellipse(1.2, Y(13.0), 3.0, 4.4)],
            curve_chain([(9.0, Y(28)), (3.0, Y(28)), (0.0, Y(25)), (1.0, Y(18))], [2.0, 1.8, 1.6, 1.4], 12) + [ellipse(1.6, Y(16.0), 3.0, 4.4)]],
    }
    _to_body_frame(g)


def apply_dragon(g):
    """a western dragon: horned head on a long neck, bat wings, spiked ridge, heavy legs and a barbed tail"""
    g["PAD"] = 16; g["DESIGN_H"] = 60; g["GROUND"] = 59.0; g["DESIGN_W"] = 78
    G = g["GROUND"]; Y = lambda h: G - h
    g["STAGES"] = [("pup", 0.56, 1.30, 0.86), ("juvenile", 0.70, 1.12, 0.94), ("adult", 0.84, 1.0, 1.0)]
    # wing: an arm, three finger spars and a membrane that sags between the tips (a bat's wing), raised behind the shoulders
    S, W = (37.0, Y(37.0)), (34.0, Y(52.0))
    T = [(23.0, Y(61.0)), (11.0, Y(54.0)), (5.5, Y(41.0))]
    B = (14.0, Y(36.5))
    def sag(p, q, k):
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        return (mx + (W[0] - mx) * k, my + (W[1] - my) * k)
    membrane = [W, T[0], sag(T[0], T[1], 0.42), T[1], sag(T[1], T[2], 0.42), T[2], sag(T[2], B, 0.34), B, (24.0, Y(34.5)), S]
    spars = chain([S, W], [1.6, 1.3], 4) + chain([W, T[0]], [1.3, 0.8], 4) + chain([W, T[1]], [1.2, 0.8], 4) + chain([W, T[2]], [1.2, 0.8], 4)
    def panel(a, b, c, k=0.66):
        cx, cy = (a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3
        return ("cut", [(cx + (q[0] - cx) * k, cy + (q[1] - cy) * k) for q in (a, b, c)])
    wing = [membrane] + spars + [panel(W, T[0], sag(T[0], T[1], 0.42)), panel(W, sag(T[0], T[1], 0.42), T[1]),
                                 panel(W, T[1], sag(T[1], T[2], 0.42)), panel(W, sag(T[1], T[2], 0.42), T[2]),
                                 panel(W, T[2], B), panel(W, B, S, 0.55)]
    ridge = [[(x - 1.4, Y(36.0)), (x, Y(40.0)), (x + 1.4, Y(36.0))] for x in (14.0, 18.0, 22.0)]
    g["BODY"] = [ellipse(17.0, Y(27.5), 9.0, 8.4), ellipse(28.0, Y(27.0), 10.4, 7.4), ellipse(39.5, Y(28.0), 9.0, 8.4),
                 ellipse(38.5, Y(33.5), 7.0, 5.0)] + wing + [
                 ("cutline", [(40.0, Y(38.6)), (33.0, Y(35.2)), (26.0, Y(34.6)), (19.0, Y(36.2)), (10.0, Y(36.0))], 1.0)] + ridge
    neck = chain([(40.5, Y(33.0)), (45.0, Y(41.0)), (48.5, Y(48.0))], [6.0, 4.8, 4.0], 5)
    skull = [ellipse(52.0, Y(50.5), 5.4, 4.4)]
    snout = chain([(55.0, Y(49.6)), (61.0, Y(48.4)), (67.0, Y(46.8))], [3.9, 3.3, 2.7], 5) + [[(52.0, Y(52.5)), (56.0, Y(54.4)), (59.0, Y(51.0))]]
    jaw = chain([(53.0, Y(46.6)), (59.0, Y(45.0)), (64.0, Y(44.0))], [2.4, 2.0, 1.6], 4)
    horns = [[(49.5, Y(53.5)), (43.0, Y(57.0)), (41.0, Y(62.0)), (46.5, Y(57.5)), (51.0, Y(54.5))],
             [(51.5, Y(54.0)), (47.0, Y(60.5)), (48.0, Y(63.5)), (53.5, Y(56.5))]]
    teeth = [("cut", [(62.5, Y(45.0)), (63.2, Y(43.0)), (63.9, Y(45.0))]), ("cut", [(58.5, Y(45.6)), (59.2, Y(43.6)), (59.9, Y(45.6))])]
    g["HEAD_SIDE"] = neck + skull + snout + jaw + horns + teeth
    g["HEAD_SIDE_KEY"] = dict(eye=(54.0, Y(51.6)), nose=(65.5, Y(47.2)))
    g["EAR_SIDE"] = [
        [(47.0, Y(51.0)), (41.0, Y(55.0)), (45.0, Y(49.5))],
        [(47.0, Y(51.0)), (40.0, Y(53.0)), (43.0, Y(57.0)), (46.0, Y(50.0))],
        [(47.0, Y(51.0)), (39.5, Y(51.0)), (44.5, Y(53.0)), (41.0, Y(57.5)), (48.0, Y(52.5))],
    ]
    g["NECK"] = (42.0, Y(36.0))
    fy = Y(48.0)
    _face(g, 54.0, fy, [ellipse(54.0, fy - 1.0, 7.8, 8.0), ellipse(54.0, fy + 5.5, 4.4, 5.0)],
          eye=((-5.5, -3), (3.5, -3)), nose=(-0.5, 8), mouth=((-3, 10), (2, 14)))
    g["EAR_FRONT"] = [[[(54.0 - 6.5, fy - 6), (54.0 - 14.0, fy - 14), (54.0 - 3.0, fy - 9)], [(54.0 + 6.5, fy - 6), (54.0 + 14.0, fy - 14), (54.0 + 3.0, fy - 9)]]] * 3
    _legs(g, 23.0, (16.0, 22.0, 40.0, 35.0), (15.5, 21.5, 42.0, 37.0),
          dict(l1=10.0, l2=8.8, ank=6.8, bend=1, w=(5.2, 3.2, 2.2, 2.0), paw=(7.0, 3.2)),
          dict(l1=9.2, l2=8.2, ank=6.6, bend=-1, w=(4.8, 3.0, 2.2, 2.0), paw=(7.0, 3.2)))
    barb = [(1.0, Y(8.5)), (-0.5, Y(13.0)), (5.0, Y(11.5))]
    g["TAILS"] = {
        0: [curve_chain([(9.0, Y(28)), (3.0, Y(24)), (2.5, Y(14)), (6.5, Y(6))], [4.4, 3.6, 2.4, 0.8], 14) + [[(3.5, Y(4.5)), (8.5, Y(2.5)), (9.5, Y(8.0))]],
            curve_chain([(9.0, Y(28)), (2.0, Y(25)), (1.5, Y(16)), (4.5, Y(7))], [4.4, 3.6, 2.4, 0.8], 14) + [[(1.5, Y(5.5)), (6.5, Y(3.0)), (7.5, Y(8.5))]]],
        1: [curve_chain([(9.0, Y(28)), (2.5, Y(30)), (1.0, Y(38)), (6.0, Y(43))], [4.4, 3.6, 2.4, 0.8], 14) + [[(4.5, Y(46.0)), (9.5, Y(45.5)), (8.5, Y(40.5))]],
            curve_chain([(9.0, Y(28)), (2.0, Y(31)), (0.5, Y(40)), (5.0, Y(45))], [4.4, 3.6, 2.4, 0.8], 14) + [[(3.5, Y(48.0)), (8.5, Y(47.5)), (7.5, Y(42.5))]]],
        2: [curve_chain([(9.0, Y(28)), (3.0, Y(26)), (0.5, Y(20)), (1.0, Y(12))], [4.4, 3.6, 2.4, 0.8], 14) + [[(-0.5, Y(9.0)), (4.0, Y(8.5)), (3.0, Y(14.0))]],
            curve_chain([(9.0, Y(28)), (3.0, Y(27)), (1.0, Y(22)), (2.0, Y(14))], [4.4, 3.6, 2.4, 0.8], 14) + [[(0.5, Y(11.0)), (5.0, Y(10.5)), (4.0, Y(16.0))]]],
    }
    _to_body_frame(g)


def apply_phoenix(g):
    """a great firebird: slender body, S-curved neck, a crest of flame feathers and long trailing plumes"""
    g["PAD"] = 18; g["DESIGN_H"] = 62; g["GROUND"] = 61.0; g["DESIGN_W"] = 80
    G = g["GROUND"]; Y = lambda h: G - h
    g["STAGES"] = [("pup", 0.54, 1.35, 0.85), ("juvenile", 0.68, 1.15, 0.94), ("adult", 0.82, 1.0, 1.0)]
    wing = [(40.0, Y(38.0)), (34.0, Y(43.0)), (24.0, Y(45.0)), (14.0, Y(41.0)), (6.0, Y(35.0)), (14.0, Y(36.0)), (8.0, Y(31.0)),
            (17.0, Y(32.0)), (12.0, Y(27.0)), (22.0, Y(28.5)), (30.0, Y(28.0)), (38.0, Y(30.0))]
    g["BODY"] = [ellipse(34.0, Y(34.0), 11.0, 8.0, -0.15), ellipse(42.0, Y(34.0), 6.0, 6.5), wing,
                 ("cutline", [(36.0, Y(38.0)), (14.0, Y(36.0))], 0.6), ("cutline", [(36.0, Y(34.0)), (16.0, Y(30.5))], 0.6)]
    neck = chain([(42.0, Y(38.0)), (46.5, Y(44.0)), (49.5, Y(49.0))], [4.2, 3.4, 2.8], 5)
    head = [ellipse(51.5, Y(51.0), 3.8, 3.3)]
    beak = [[(54.0, Y(52.0)), (60.5, Y(50.0)), (54.5, Y(48.8))]]
    g["HEAD_SIDE"] = neck + head + beak
    g["HEAD_SIDE_KEY"] = dict(eye=(52.2, Y(51.8)), nose=(59.8, Y(50.0)))
    g["EAR_SIDE"] = [
        [(49.5, Y(53.0)), (44.0, Y(60.0)), (48.5, Y(55.5)), (47.0, Y(63.0)), (51.5, Y(55.5)), (52.5, Y(53.0))],
        [(49.5, Y(53.0)), (43.0, Y(57.0)), (47.5, Y(56.0)), (46.0, Y(61.5)), (50.5, Y(56.0)), (52.5, Y(53.0))],
        [(49.5, Y(53.0)), (44.0, Y(55.0)), (47.0, Y(58.0)), (48.5, Y(55.0)), (51.0, Y(61.0)), (52.5, Y(53.0))],
    ]
    g["NECK"] = (44.0, Y(40.0))
    fy = Y(50.0)
    _face(g, 52.0, fy, [ellipse(52.0, fy - 1.0, 4.6, 5.4), [(50.0, fy + 3.0), (54.0, fy + 3.0), (52.0, fy + 9.0)]],
          eye=((-3.4, -3), (1.9, -3)), nose=(-0.5, 7), mouth=((-1.5, 8), (1.5, 10)))
    _ears_front(g, 52.0, fy - 3.0, 3.6, 0, [(14, 5.0, False), (10, 6.5, False), (13, 4.0, True)])
    # two thin bird legs: the near and far legs of each pair stand together
    _legs(g, 26.0, (28.0, 33.0, 33.0, 28.0), (25.5, 35.0, 37.0, 27.0),
          dict(l1=10.6, l2=10.4, ank=4.0, bend=1, w=(1.7, 1.0, 0.8, 0.8), paw=(6.0, 1.6)),
          dict(l1=10.6, l2=10.4, ank=4.0, bend=1, w=(1.7, 1.0, 0.8, 0.8), paw=(6.0, 1.6)))
    def plumes(spec, wag):
        out = []
        for (ex, eh, mx, mh) in spec:
            out.append(curve_chain([(24.0, Y(34.0)), (mx, Y(mh)), ((mx + ex) / 2 + wag, Y((mh + eh) / 2)), (ex, Y(eh))], [1.6, 3.4, 3.0, 0.6], 12))
        return sum(out, [])
    g["TAILS"] = {
        0: [plumes([(1.0, 20.0, 12.0, 30.0), (3.0, 12.0, 13.0, 27.0), (6.0, 6.0, 15.0, 25.0)], w) for w in (0, 2)],
        1: [plumes([(1.0, 44.0, 12.0, 38.0), (3.0, 50.0, 12.0, 41.0), (7.0, 55.0, 14.0, 42.0)], w) for w in (0, 2)],
        2: [plumes([(0.5, 30.0, 12.0, 32.0), (0.5, 25.0, 12.0, 30.0), (2.0, 20.0, 13.0, 28.0)], w) for w in (0, 2)],
    }
    _to_body_frame(g)
