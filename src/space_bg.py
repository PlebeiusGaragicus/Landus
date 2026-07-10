"""Procedural space background for the launcher: parallax stars, planets,
shooting stars, and a vignette. All textures are generated with numpy/PIL at
startup -- no image assets.
"""

from __future__ import annotations

import math
import random

import arcade
import numpy as np
from PIL import Image


def _sphere_rgba(radius: int, color_fn, light=(-0.45, -0.35)) -> np.ndarray:
    """Shaded sphere as (d, d, 4) uint8. color_fn(nx, ny) -> (h, w, 3) floats.

    nx/ny are surface coords in [-1, 1]; lighting is lambert + limb falloff
    from the given light direction (screen-space, z implied).
    """
    d = radius * 2
    yy, xx = np.mgrid[0:d, 0:d]
    nx = (xx - radius + 0.5) / radius
    ny = (yy - radius + 0.5) / radius
    rr = np.sqrt(nx * nx + ny * ny)
    nz = np.sqrt(np.clip(1.0 - rr * rr, 0.0, 1.0))

    lx, ly = light
    lz = math.sqrt(max(0.0, 1.0 - lx * lx - ly * ly))
    lam = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)
    shade = 0.22 + 0.78 * lam

    color = color_fn(nx, ny)  # (d, d, 3)
    out = np.zeros((d, d, 4), dtype=np.uint8)
    out[..., :3] = np.clip(color * shade[..., None], 0, 255).astype(np.uint8)
    # 1.5px soft edge
    out[..., 3] = (np.clip((1.0 - rr) * radius / 1.5, 0.0, 1.0) * 255).astype(np.uint8)
    return out


def _gas_giant(radius: int, rng: random.Random) -> Image.Image:
    """Banded purple/indigo giant."""
    palette = np.array([
        (96, 78, 160), (128, 104, 196), (78, 64, 138), (156, 128, 214),
        (88, 74, 150), (120, 96, 188), (70, 58, 126), (140, 112, 200),
    ], dtype=np.float64)

    phase = rng.uniform(0, math.tau)

    def color_fn(nx, ny):
        band = ny + 0.07 * np.sin(nx * 5.0 + phase) + 0.03 * np.sin(nx * 11.0)
        idx = ((band + 1.0) * 0.5 * len(palette) * 1.6).astype(np.intp) % len(palette)
        return palette[idx]

    return Image.fromarray(_sphere_rgba(radius, color_fn), "RGBA")


def _moon(radius: int, rng: random.Random) -> Image.Image:
    """Gray cratered moon."""
    d = radius * 2
    base = np.full((d, d, 3), (168, 165, 172), dtype=np.float64)
    for _ in range(14):
        cx = rng.uniform(0.15, 0.85) * d
        cy = rng.uniform(0.15, 0.85) * d
        cr = rng.uniform(0.06, 0.2) * d
        yy, xx = np.mgrid[0:d, 0:d]
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        base[dist < cr] *= 0.82
        rim = (dist >= cr) & (dist < cr * 1.25)
        base[rim] *= 1.08

    def color_fn(nx, ny):
        return base

    return Image.fromarray(_sphere_rgba(radius, color_fn), "RGBA")


def _ringed_planet(radius: int) -> Image.Image:
    """Teal planet with a pale ring; canvas is wider than the sphere."""
    ring_rx = radius * 2.3
    ring_ry = radius * 0.62
    w = int(ring_rx * 2) + 4
    h = radius * 2 + int(ring_ry) + 8
    canvas = np.zeros((h, w, 4), dtype=np.uint8)
    cx, cy = w // 2, h // 2

    def color_fn(nx, ny):
        d = nx.shape[0]
        swirl = 18 * np.sin(ny * 3.0 + nx * 1.5)
        col = np.empty((d, d, 3), dtype=np.float64)
        col[..., 0] = 64 + swirl
        col[..., 1] = 170 + swirl
        col[..., 2] = 178 + swirl * 0.5
        return col

    sphere = _sphere_rgba(radius, color_fn)

    # Ring: signed distance to an ellipse in canvas space, tilted look via ry.
    yy, xx = np.mgrid[0:h, 0:w]
    ex = (xx - cx) / ring_rx
    ey = (yy - cy) / ring_ry
    er = np.sqrt(ex * ex + ey * ey)
    ring_band = np.clip(1.0 - np.abs(er - 0.86) / 0.14, 0.0, 1.0)
    inner_gap = np.clip((er - 0.62) / 0.06, 0.0, 1.0)
    ring_alpha = ring_band * inner_gap * 160

    canvas[..., 0] = 205
    canvas[..., 1] = 195
    canvas[..., 2] = 225
    canvas[..., 3] = ring_alpha.astype(np.uint8)

    # Ring passes BEHIND the top half of the sphere: clear it inside the
    # sphere silhouette above center, keep it in front below.
    sy0, sx0 = cy - radius, cx - radius
    yy_s, xx_s = np.mgrid[0:radius * 2, 0:radius * 2]
    in_sphere = ((xx_s - radius) ** 2 + (yy_s - radius) ** 2) < radius * radius
    top_half = yy_s < radius
    region = canvas[sy0:sy0 + radius * 2, sx0:sx0 + radius * 2]
    region[..., 3][in_sphere & top_half] = 0

    # Composite the sphere over the ring (alpha blend).
    sa = sphere[..., 3:4].astype(np.float64) / 255.0
    region[..., :3] = (sphere[..., :3] * sa + region[..., :3] * (1 - sa)).astype(np.uint8)
    region[..., 3] = np.maximum(region[..., 3], sphere[..., 3])

    return Image.fromarray(canvas, "RGBA")


def _radial_glow(radius: int, color: tuple[int, int, int], peak: int = 90) -> Image.Image:
    d = radius * 2
    yy, xx = np.mgrid[0:d, 0:d]
    rr = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    alpha = (np.clip(1.0 - rr, 0.0, 1.0) ** 2.2 * peak).astype(np.uint8)
    out = np.zeros((d, d, 4), dtype=np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = color
    out[..., 3] = alpha
    return Image.fromarray(out, "RGBA")


def _vignette(width: int, height: int) -> Image.Image:
    yy, xx = np.mgrid[0:height, 0:width]
    dx = (xx - width / 2) / (width / 2)
    dy = (yy - height / 2) / (height / 2)
    dist = np.sqrt(dx * dx + dy * dy)
    alpha = (np.clip((dist - 0.62) / 0.55, 0.0, 1.0) ** 1.6 * 150).astype(np.uint8)
    out = np.zeros((height, width, 4), dtype=np.uint8)
    out[..., 3] = alpha
    return Image.fromarray(out, "RGBA")


class SpaceBackground:
    """Drifting parallax starfield + planets. draw() under the UI,
    draw_vignette() over it."""

    def __init__(self, width: int, height: int, seed: int = 11):
        self.w = width
        self.h = height
        self.t = 0.0
        rng = random.Random(seed)

        # Parallax layers: (points, drift px/s, size, base color, twinkle)
        def stars(n):
            return [(rng.uniform(0, width), rng.uniform(0, height)) for _ in range(n)]

        self.layers = [
            {"pts": stars(150), "speed": 2.0, "size": 1, "color": (150, 160, 190), "twinkle": False},
            {"pts": stars(90), "speed": 5.0, "size": 2, "color": (200, 210, 235), "twinkle": True},
            {"pts": stars(40), "speed": 9.0, "size": 3, "color": (245, 248, 255), "twinkle": True},
        ]

        # Planets: (texture, cx, cy, scale, bob_amp, bob_rate)
        giant = arcade.Texture(_gas_giant(230, rng))
        moon = arcade.Texture(_moon(30, rng))
        ringed = arcade.Texture(_ringed_planet(46))
        glow_violet = arcade.Texture(_radial_glow(300, (140, 110, 220), peak=70))
        glow_teal = arcade.Texture(_radial_glow(120, (90, 200, 200), peak=45))

        self.planets = [
            # (glow_tex, tex, x, y, draw_w, draw_h, bob_amp, bob_rate)
            (glow_violet, giant, 40, -50, 460, 460, 3.0, 0.10),
            (glow_teal, ringed, width - 150, height - 120, 212, 121, 5.0, 0.07),
            (None, moon, width * 0.16, height - 88, 60, 60, 4.0, 0.05),
        ]

        self._vignette_tex = arcade.Texture(_vignette(width, height))

        self._shoot = None  # (x, y, vx, vy, age)
        self._next_shoot = rng.uniform(4.0, 9.0)
        self._rng = rng

    def update(self, dt: float):
        self.t += dt

        self._next_shoot -= dt
        if self._shoot is None and self._next_shoot <= 0:
            x = self._rng.uniform(self.w * 0.2, self.w * 0.95)
            y = self.h + 20
            speed = self._rng.uniform(500, 750)
            ang = self._rng.uniform(math.radians(215), math.radians(250))
            self._shoot = [x, y, speed * math.cos(ang), -abs(speed * math.sin(ang)), 0.0]
        if self._shoot is not None:
            s = self._shoot
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            s[4] += dt
            if s[4] > 1.4 or s[0] < -60 or s[1] < -60:
                self._shoot = None
                self._next_shoot = self._rng.uniform(5.0, 13.0)

    def draw(self):
        # Stars (drift left, wrap; twinkle by splitting into two alpha groups)
        for li, layer in enumerate(self.layers):
            off = (self.t * layer["speed"]) % self.w
            pts = [((x - off) % self.w, y) for x, y in layer["pts"]]
            r, g, b = layer["color"]
            if layer["twinkle"]:
                a1 = int(255 * (0.65 + 0.35 * math.sin(self.t * 2.1 + li)))
                a2 = int(255 * (0.65 + 0.35 * math.sin(self.t * 3.3 + li * 2 + 1.7)))
                arcade.draw_points(pts[0::2], (r, g, b, a1), layer["size"])
                arcade.draw_points(pts[1::2], (r, g, b, a2), layer["size"])
            else:
                arcade.draw_points(pts, (r, g, b, 255), layer["size"])

        # Planets with glows and a slow bob
        for glow, tex, x, y, dw, dh, amp, rate in self.planets:
            bob = math.sin(self.t * rate * math.tau) * amp
            if glow is not None:
                gw = dw * 1.9
                arcade.draw_texture_rect(glow, arcade.XYWH(x, y + bob, gw, gw))
            arcade.draw_texture_rect(tex, arcade.XYWH(x, y + bob, dw, dh))

        # Shooting star: fading trail behind a bright head
        if self._shoot is not None:
            x, y, vx, vy, age = self._shoot
            fade = 1.0 if age < 1.0 else max(0.0, 1.0 - (age - 1.0) / 0.4)
            n = 7
            for i in range(n):
                t0 = i / n * 0.11
                t1 = (i + 1) / n * 0.11
                alpha = int(200 * (1 - i / n) * fade)
                arcade.draw_line(
                    x - vx * t0, y - vy * t0, x - vx * t1, y - vy * t1,
                    (220, 230, 255, alpha), 2,
                )
            arcade.draw_points([(x, y)], (255, 255, 255, int(255 * fade)), 3)

    def draw_vignette(self):
        arcade.draw_texture_rect(
            self._vignette_tex, arcade.XYWH(self.w / 2, self.h / 2, self.w, self.h),
        )
