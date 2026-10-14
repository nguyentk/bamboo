"""Unity -> Bamboo (Godot) coordinate system conversion.

Unity:  left-handed,  +Y up, +Z forward, +X right.
Bamboo: right-handed, +Y up, -Z forward, +X right.

Both are Y-up and use meters, so the conversion is a mirror across the XY plane (Z flip),
M = diag(1, 1, -1):

    position  (x, y, z)        -> (x, y, -z)
    direction (x, y, z)        -> (x, y, -z)        (Unity forward +Z -> Bamboo forward -Z)
    scale     (x, y, z)        -> (x, y, z)
    rotation  quat (x, y, z, w) -> (-x, -y, z, w)

The quaternion rule comes from R' = M R M: the rotation axis is a pseudovector, so it maps to
det(M) * M * axis = (-ax, -ay, az) while the angle is unchanged.

Applies to transforms serialized in Unity scenes/prefabs. Mesh data imported from FBX/glTF is
already converted by Bamboo's importers (ufbx / glTF) and must NOT be converted again.
"""

from __future__ import annotations

import math
from typing import Sequence

Vec3 = tuple[float, float, float]
Quat = tuple[float, float, float, float]  # (x, y, z, w), same component order as Unity and Bamboo


def convert_position(v: Sequence[float]) -> Vec3:
    return (float(v[0]), float(v[1]), -float(v[2]))


def convert_direction(v: Sequence[float]) -> Vec3:
    return convert_position(v)


def convert_scale(s: Sequence[float]) -> Vec3:
    return (float(s[0]), float(s[1]), float(s[2]))


def convert_quaternion(q: Sequence[float]) -> Quat:
    return (-float(q[0]), -float(q[1]), float(q[2]), float(q[3]))


def quat_rotate(q: Sequence[float], v: Sequence[float]) -> Vec3:
    """Rotate vector v by unit quaternion q (x, y, z, w): v' = q * v * q^-1."""
    qx, qy, qz, qw = q
    vx, vy, vz = v
    # t = 2 * cross(q.xyz, v)
    tx = 2.0 * (qy * vz - qz * vy)
    ty = 2.0 * (qz * vx - qx * vz)
    tz = 2.0 * (qx * vy - qy * vx)
    # v' = v + w * t + cross(q.xyz, t)
    return (
        vx + qw * tx + (qy * tz - qz * ty),
        vy + qw * ty + (qz * tx - qx * tz),
        vz + qw * tz + (qx * ty - qy * tx),
    )


def quat_from_axis_angle(axis: Sequence[float], angle_rad: float) -> Quat:
    length = math.sqrt(sum(a * a for a in axis))
    ax, ay, az = (a / length for a in axis)
    s = math.sin(angle_rad / 2.0)
    return (ax * s, ay * s, az * s, math.cos(angle_rad / 2.0))
