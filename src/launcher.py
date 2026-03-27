import logging
from typing import Optional

import arcade

from src.audio import AudioManager
from src.config import Config
from src.input_handler import InputHandler
from src.process_manager import GameInfo, discover_games, launch_game

log = logging.getLogger(__name__)

CARD_WIDTH = 280
CARD_HEIGHT = 380
CARD_SPACING = 40
SCROLL_SPEED = 12


class LauncherView(arcade.View):
    """Game selection carousel."""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.input = InputHandler(config)
        self.audio = AudioManager()

        self.games: list[GameInfo] = []
        self.selected_index: int = 0
        self.scroll_offset: float = 0.0
        self.target_offset: float = 0.0

        self._cover_textures: dict[int, Optional[arcade.Texture]] = {}
        self._last_themed_index: int = -1
        self._error_message: Optional[str] = None
        self._error_timer: float = 0.0

        w = config.screen_width
        h = config.screen_height
        cx = w / 2
        self._no_games_text = arcade.Text(
            "No games found", cx, h / 2,
            arcade.color.GRAY, 24, anchor_x="center", anchor_y="center",
        )
        self._no_games_hint = arcade.Text(
            "Add games to the games/ directory", cx, h / 2 - 40,
            arcade.color.DARK_GRAY, 14, anchor_x="center", anchor_y="center",
        )
        self._nav_hint = arcade.Text(
            "[ A/D ] Navigate   [ F ] Launch", cx, 30,
            (120, 120, 140), 12, anchor_x="center",
        )
        self._card_title = arcade.Text("", 0, 0, arcade.color.WHITE, 16, anchor_x="center", anchor_y="center")
        self._error_text = arcade.Text("", cx, h - 40, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center")

    def on_show_view(self):
        arcade.set_background_color((20, 20, 30))
        self.games = discover_games(self.config.games_dir)
        self._load_covers()
        if self.games:
            self._select(0)

    def _load_covers(self):
        for i, game in enumerate(self.games):
            if game.cover_art and game.cover_art.is_file():
                try:
                    self._cover_textures[i] = arcade.load_texture(str(game.cover_art))
                    continue
                except Exception:
                    pass
            self._cover_textures[i] = None

    def _select(self, index: int):
        if not self.games:
            return
        self.selected_index = index % len(self.games)
        self.target_offset = self.selected_index * (CARD_WIDTH + CARD_SPACING)
        game = self.games[self.selected_index]
        if self.selected_index != self._last_themed_index:
            self._last_themed_index = self.selected_index
            if game.theme_song and game.theme_song.is_file():
                self.audio.play(game.theme_song)
            else:
                self.audio.stop()

    def on_key_press(self, key: int, modifiers: int):
        self.input.on_key_press(key)
        if not self.games:
            return

        p1 = self.input.state.player1
        if p1.left:
            self._select(self.selected_index - 1)
        elif p1.right:
            self._select(self.selected_index + 1)
        elif p1.action1 or p1.action2 or p1.action3:
            self._launch_selected()

    def on_key_release(self, key: int, modifiers: int):
        self.input.on_key_release(key)

    def _launch_selected(self):
        game = self.games[self.selected_index]
        self.audio.stop()
        log.info("Launching game: %s", game.name)

        self.window.close()

        exit_code = launch_game(game)

        if exit_code != 0:
            self._error_message = f"{game.name} crashed (code {exit_code})"
            self._error_timer = 3.0

        self._reopen_window()

    def _reopen_window(self):
        window = arcade.open_window(
            self.config.screen_width,
            self.config.screen_height,
            self.config.title,
            fullscreen=self.config.fullscreen,
        )
        window.show_view(self)

    def on_update(self, delta_time: float):
        diff = self.target_offset - self.scroll_offset
        self.scroll_offset += diff * min(1.0, SCROLL_SPEED * delta_time)

        if self._error_timer > 0:
            self._error_timer -= delta_time
            if self._error_timer <= 0:
                self._error_message = None

    def on_draw(self):
        self.clear()
        w = self.window.width
        h = self.window.height
        cx = w / 2
        cy = h / 2

        if not self.games:
            self._no_games_text.draw()
            self._no_games_hint.draw()
            return

        for i, game in enumerate(self.games):
            card_x = cx + i * (CARD_WIDTH + CARD_SPACING) - self.scroll_offset
            card_y = cy
            is_selected = i == self.selected_index
            scale = 1.1 if is_selected else 0.85

            cw = CARD_WIDTH * scale
            ch = CARD_HEIGHT * scale

            border_color = (100, 180, 255) if is_selected else (60, 60, 80)
            card_rect = arcade.XYWH(card_x, card_y, cw, ch)
            arcade.draw_rect_filled(card_rect, (30, 30, 45))
            arcade.draw_rect_outline(card_rect, border_color, 3 if is_selected else 1)

            tex = self._cover_textures.get(i)
            if tex:
                img_h = ch - 60
                img_w = cw - 20
                img_rect = arcade.XYWH(card_x, card_y + 15, img_w, img_h)
                arcade.draw_texture_rect(tex, img_rect)

            self._card_title.text = game.name
            self._card_title.x = card_x
            self._card_title.y = card_y - ch / 2 + 20
            self._card_title.color = arcade.color.WHITE if is_selected else arcade.color.LIGHT_GRAY
            self._card_title.font_size = 16 if is_selected else 13
            self._card_title.bold = is_selected
            self._card_title.draw()

        self._nav_hint.draw()

        if self._error_message:
            err_rect = arcade.XYWH(cx, h - 40, 500, 40)
            arcade.draw_rect_filled(err_rect, (180, 40, 40, 200))
            self._error_text.text = self._error_message
            self._error_text.draw()
