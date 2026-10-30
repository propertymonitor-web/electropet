"""Organic shapes for the pet sprites: ellipses, tapered limbs and curved chains, all returned as polygons in design
units so the generator can draw their union.  A leg is built from real bones (thigh, shin, ankle, paw) with a
two-bone solver, so it bends like a leg and not like a stump."""
import math


def ellipse(cx, cy, rx, ry, rot=0.0, n=28):
    c, s = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return pts


def seg(p0, p1, w0, w1, n=5):
    """a tapered limb piece from p0 (half-width w0) to p1 (half-width w1), with round ends"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1e-9
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    a0 = math.atan2(ny, nx)
    pts = []
    for i in range(n + 1):                      # cap at p1 (sweeps from the normal side to the opposite)
        a = a0 - math.pi * i / n
        pts.append((p1[0] + w1 * math.cos(a), p1[1] + w1 * math.sin(a)))
    for i in range(n + 1):                      # cap at p0
        a = a0 + math.pi - math.pi * i / n
        pts.append((p0[0] + w0 * math.cos(a), p0[1] + w0 * math.sin(a)))
    return pts


def chain(points, widths, n=5):
    return [seg(points[i], points[i + 1], widths[i], widths[i + 1], n) for i in range(len(points) - 1)]


def bezier(p0, p1, p2, p3, n=10):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


def curve_chain(ctrl, widths, n=10):
    """a tapered tube along a cubic curve; widths is a list of half-widths sampled evenly along it"""
    pts = bezier(*ctrl, n=n)
    ws = []
    for i in range(len(pts)):
        t = i / (len(pts) - 1) * (len(widths) - 1)
        k = min(int(t), len(widths) - 2)
        f = t - k
        ws.append(widths[k] * (1 - f) + widths[k + 1] * f)
    return chain(pts, ws, 4)


def two_bone(hip, ankle, l1, l2, bend):
    """knee position for a leg from `hip` to `ankle`; bend=+1 puts the knee toward +x, -1 toward -x"""
    dx, dy = ankle[0] - hip[0], ankle[1] - hip[1]
    d = math.hypot(dx, dy)
    d = min(d, l1 + l2 - 0.01)
    d = max(d, abs(l1 - l2) + 0.01)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    ux, uy = dx / (math.hypot(dx, dy) or 1e-9), dy / (math.hypot(dx, dy) or 1e-9)
    mx, my = hip[0] + ux * a, hip[1] + uy * a
    # perpendicular, chosen so that the knee lies toward `bend` in x
    px, py = -uy, ux
    if px * bend < 0:
        px, py = -px, -py
    return (mx + px * h, my + py * h)


def leg(hip, foot, l1, l2, ank_h, bend, w_hip, w_knee, w_ank, w_toe, paw_len, paw_h, hind=True):
    """polygons for one whole leg: hip -> knee -> ankle -> paw.  `foot` is the middle of the paw's ground line."""
    ankle = (foot[0] - (0.6 if hind else 0.2) * (-1 if hind else 1), foot[1] - ank_h)
    if hind:
        ankle = (foot[0] - 1.2, foot[1] - ank_h)          # the hock sits a little behind the paw
    else:
        ankle = (foot[0] - 0.3, foot[1] - ank_h)
    knee = two_bone(hip, ankle, l1, l2, bend)
    polys = chain([hip, knee, ankle, (foot[0] + 0.4, foot[1] - paw_h)], [w_hip, w_knee, w_ank, w_toe], 4)
    # paw: a small oval, longer toward the front
    polys.append(ellipse(foot[0] + paw_len * 0.18, foot[1] - paw_h * 0.55, paw_len * 0.5, paw_h * 0.62, 0.0, 14))
    return polys
