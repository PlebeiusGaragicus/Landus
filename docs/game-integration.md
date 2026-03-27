# Game Integration Guide

## Adding a New Game

1. Create a git repo for the game.
2. Add a `game.json` at the repo root (see below).
3. Add the repo as a submodule: `git submodule add <url> games/<name>`
4. The launcher will auto-discover it on next launch.

## game.json Manifest

```json
{
  "name": "Human-readable title",
  "entry": "command to run from game root (e.g. python src/main.py)",
  "players": [1, 2],
  "cover_art": "assets/cover.png",
  "theme_song": "assets/theme.ogg"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| name | yes | Display name in launcher |
| entry | yes | Shell command, run with cwd = game root |
| players | no | Array of supported player counts, default [1] |
| cover_art | no | Path to cover image (relative to game root) |
| theme_song | no | Path to audio file (relative to game root) |

## Game Requirements

- **Self-contained**: all assets, dependencies, and code inside the submodule.
- **Own requirements.txt** (or equivalent) for its dependencies.
- **Own .gitignore**: the root `.gitignore` does not apply inside submodules. Each game repo needs its own (at minimum: `__pycache__/`, `*.pyc`, `.venv/`).
- **ESC contract**: hold ESC for 1 second = clean exit (exit code 0).
- **Fullscreen**: respect `LANDUS_FULLSCREEN=1` env var if applicable.
- **Exit code**: 0 for clean exit, non-zero for crash. Launcher logs non-zero exits.

### Virtual Environment

Games share the **root `.venv`**. The launcher replaces `python` in `game.json` entries with `sys.executable`, so games automatically use the same interpreter and installed packages. Per-game `requirements.txt` files document what each game needs but are not installed separately.

If a game ever requires a conflicting dependency, it can maintain its own venv and specify the full interpreter path in `game.json` `entry` (e.g. `.venv/bin/python src/main.py`).

## Game Structure (recommended)

```
game-name/
├── game.json
├── requirements.txt
├── README.md
├── docs/
├── assets/
│   ├── cover.png
│   └── theme.ogg
└── src/
    └── main.py
```

## Code Patterns

### sys.path Bootstrap

The launcher runs `python src/main.py` with `cwd=game_root`. Python adds `game_root/src/` to `sys.path` but **not** `game_root/` itself, so `from src.config import ...` will fail. Every game entry point needs this before any `src.*` imports:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Text Rendering

`arcade.draw_text()` rebuilds a texture every frame. Use `arcade.Text` objects instead -- they cache the rendered texture and only re-render when content changes.

```python
# in __init__
self._score_text = arcade.Text("Score: 0", 10, 680, arcade.color.WHITE, 16)

# in on_draw
self._score_text.text = f"Score: {self.score}"
self._score_text.draw()
```

For static labels, just call `.draw()`. For dynamic text (score, level), update `.text` before `.draw()`.

### Rect Drawing (Arcade 3.x)

The old `draw_rectangle_filled` / `draw_rectangle_outline` functions no longer exist. Use `arcade.XYWH` or `arcade.LBWH` to build a rect, then pass it to the new draw functions:

```python
rect = arcade.XYWH(center_x, center_y, width, height)
arcade.draw_rect_filled(rect, color)
arcade.draw_rect_outline(rect, border_color, border_width)
```

`XYWH` = center-based, `LBWH` = left-bottom-based.

### ESC Hold-to-Quit

Track a boolean + accumulator. Show a progress bar so the player knows it's registering.

```python
def __init__(self):
    self.esc_pressed = False
    self.esc_held = 0.0

def on_key_press(self, key, modifiers):
    if key == arcade.key.ESCAPE:
        self.esc_pressed = True

def on_key_release(self, key, modifiers):
    if key == arcade.key.ESCAPE:
        self.esc_pressed = False
        self.esc_held = 0.0

def on_update(self, delta_time):
    if self.esc_pressed:
        self.esc_held += delta_time
        if self.esc_held >= 1.0:
            self.window.close()
            return

def on_draw(self):
    if self.esc_held > 0:
        bar_w = 200 * (self.esc_held / 1.0)
        bar = arcade.XYWH(self.window.width / 2, 20, bar_w, 8)
        arcade.draw_rect_filled(bar, arcade.color.ORANGE)
```
