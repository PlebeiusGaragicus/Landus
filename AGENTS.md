# Agent Instructions

## Conventions

- Each game is a **separate git submodule** under `games/`. Games are fully self-contained (own assets, deps, docs, README).
- The launcher and games share **no code**. Games are spawned as subprocesses.
- The only contract between launcher and game is `game.json` at the game's root.
- Games may use any language or engine. The launcher is Python / Arcade library.

## game.json Contract

```json
{
  "name": "Human-readable title",
  "entry": "shell command to run the game from its root dir",
  "players": [1, 2],
  "cover_art": "relative/path/to/cover.png",
  "theme_song": "relative/path/to/theme.ogg"
}
```

## Platform Targets

- **Production**: Debian Linux, fullscreen, arcade cabinet hardware
- **Development**: macOS, windowed

Platform is auto-detected via `platform.system()`.

## Documentation Style

- Terse, structured, for agent/AI retrieval
- Avoid verbose prose
- Use tables and code blocks

## Rules

- **Do not run or test games autonomously.** The human tests games manually.
- Do not prompt the user to test.
- Agents handle all development steps as directed by the human.

## ESC Protocol

Games must implement: hold ESC for 1 second = clean exit (code 0). The launcher watchdog will force-kill games that freeze.
