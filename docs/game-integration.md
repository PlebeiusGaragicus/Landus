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
- **ESC contract**: hold ESC for 1 second = clean exit (exit code 0).
- **Fullscreen**: respect `LANDUS_FULLSCREEN=1` env var if applicable.
- **Exit code**: 0 for clean exit, non-zero for crash. Launcher logs non-zero exits.

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
