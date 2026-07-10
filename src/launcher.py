import logging
import math
from typing import Optional

import arcade
import numpy as np
from PIL import Image

from src.audio import AudioManager
from src.config import Config
from src.input_handler import InputHandler
from src.process_manager import GameInfo, discover_games, launch_game
from src.space_bg import SpaceBackground

log = logging.getLogger(__name__)

CARD_WIDTH = 280
CARD_HEIGHT = 380
CARD_SPACING = 44
SCROLL_SPEED = 12
SCALE_SELECTED = 1.1
SCALE_IDLE = 0.85

BG_COLOR = (8, 10, 22)
ACCENT = (110, 205, 255)
CARD_BODY = (22, 26, 46)
CARD_STRIP = (14, 17, 32)
BORDER_IDLE = (55, 60, 92)


def _placeholder_cover(index: int, width: int = 240, height: int = 300) -> arcade.Texture:
    """Procedural cover for games without art: hued gradient + diagonal weave."""
    hue = (index * 0.61803) % 1.0  # golden-angle steps keep neighbors distinct
    # Cheap HSV->RGB for s=0.55, two values for a vertical gradient.
    def hsv(v):
        i = int(hue * 6) % 6
        f = hue * 6 - int(hue * 6)
        p, q, t = v * 0.45, v * (1 - 0.55 * f), v * (1 - 0.55 * (1 - f))
        rgb = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
        return np.array(rgb) * 255

    top, bottom = hsv(0.72), hsv(0.28)
    yy, xx = np.mgrid[0:height, 0:width]
    g = (yy / height)[..., None]
    img = top * (1 - g) + bottom * g
    weave = ((xx + yy) // 24) % 2 == 0
    img[weave] *= 0.92
    out = np.zeros((height, width, 4), dtype=np.uint8)
    out[..., :3] = img.astype(np.uint8)
    out[..., 3] = 255
    return arcade.Texture(Image.fromarray(out, "RGBA"))


class LauncherView(arcade.View):
    """Game selection carousel over a drifting space backdrop."""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.input = InputHandler(config)
        self.audio = AudioManager()

        self.games: list[GameInfo] = []
        self.selected_index: int = 0
        self.scroll_offset: float = 0.0
        self.target_offset: float = 0.0
        self.t: float = 0.0
        self._scales: list[float] = []

        self._cover_textures: dict[int, Optional[arcade.Texture]] = {}
        self._placeholders: dict[int, arcade.Texture] = {}
        self._last_themed_index: int = -1
        self._error_message: Optional[str] = None
        self._error_timer: float = 0.0
        self._ui_built = False

    def _build_ui(self):
        """(Re)create GL-bound objects. Called from on_show_view so the view
        survives the window being closed and reopened around a game launch."""
        w = self.config.screen_width
        h = self.config.screen_height
        cx = w / 2

        self.bg = SpaceBackground(w, h)

        # Same font size as the logo so the letters align: a clean drop shadow.
        self._logo_glow = arcade.Text(
            "L A N D U S", cx + 3, h - 63, (0, 0, 0, 160), 40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._logo = arcade.Text(
            "L A N D U S", cx, h - 60, (225, 238, 255), 40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._tagline = arcade.Text(
            "·  A R C A D E  ·", cx, h - 100, (120, 130, 165), 13,
            anchor_x="center", anchor_y="center",
        )
        self._no_games_text = arcade.Text(
            "No games found", cx, h / 2,
            arcade.color.GRAY, 24, anchor_x="center", anchor_y="center",
        )
        self._no_games_hint = arcade.Text(
            "Add games to the games/ directory", cx, h / 2 - 40,
            arcade.color.DARK_GRAY, 14, anchor_x="center", anchor_y="center",
        )
        self._nav_hint = arcade.Text(
            "[ A / D ]  navigate      [ F ]  launch      [ ESC ]  quit",
            cx, 26, (130, 140, 175), 13, anchor_x="center",
        )
        self._launch_hint = arcade.Text(
            "PRESS  F  TO  LAUNCH", cx, 92, (*ACCENT, 255), 18,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._counter = arcade.Text(
            "", w - 28, h - 30, (110, 120, 155), 14, anchor_x="right", anchor_y="center",
        )
        self._card_title = arcade.Text(
            "", 0, 0, arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )
        self._card_letter = arcade.Text(
            "", 0, 0, (255, 255, 255, 210), 64,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self._error_text = arcade.Text(
            "", cx, h - 140, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center",
        )
        self._ui_built = True

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)
        self._build_ui()
        self.games = discover_games(self.config.games_dir)
        self._scales = [SCALE_IDLE] * len(self.games)
        self._load_covers()
        if self.games:
            self._select(self.selected_index if self.selected_index < len(self.games) else 0)

    def _load_covers(self):
        self._cover_textures.clear()
        self._placeholders.clear()
        for i, game in enumerate(self.games):
            if game.cover_art and game.cover_art.is_file():
                try:
                    self._cover_textures[i] = arcade.load_texture(str(game.cover_art))
                    continue
                except Exception:
                    pass
            self._cover_textures[i] = None
            self._placeholders[i] = _placeholder_cover(i)

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

        if self.input.state.menu_quit:
            self.window.close()
            return
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
        self.t += delta_time
        self.bg.update(delta_time)

        diff = self.target_offset - self.scroll_offset
        self.scroll_offset += diff * min(1.0, SCROLL_SPEED * delta_time)

        for i in range(len(self._scales)):
            target = SCALE_SELECTED if i == self.selected_index else SCALE_IDLE
            self._scales[i] += (target - self._scales[i]) * min(1.0, 10 * delta_time)

        if self._error_timer > 0:
            self._error_timer -= delta_time
            if self._error_timer <= 0:
                self._error_message = None

    def _draw_card(self, i: int, game: GameInfo, cx: float, cy: float):
        is_selected = i == self.selected_index
        scale = self._scales[i] if i < len(self._scales) else SCALE_IDLE
        card_x = cx + i * (CARD_WIDTH + CARD_SPACING) - self.scroll_offset
        card_y = cy + (math.sin(self.t * 1.8) * 5 if is_selected else 0)

        cw = CARD_WIDTH * scale
        ch = CARD_HEIGHT * scale

        # Drop shadow
        arcade.draw_rect_filled(
            arcade.XYWH(card_x + 7, card_y - 9, cw, ch), (0, 0, 0, 110),
        )
        # Body + title strip
        card_rect = arcade.XYWH(card_x, card_y, cw, ch)
        arcade.draw_rect_filled(card_rect, CARD_BODY)
        strip_h = 52 * scale
        arcade.draw_rect_filled(
            arcade.XYWH(card_x, card_y - ch / 2 + strip_h / 2, cw, strip_h), CARD_STRIP,
        )

        # Border: layered glow when selected
        if is_selected:
            pulse = 0.7 + 0.3 * math.sin(self.t * 2.4)
            for grow, alpha in ((16, 22), (8, 55)):
                arcade.draw_rect_outline(
                    arcade.XYWH(card_x, card_y, cw + grow, ch + grow),
                    (*ACCENT, int(alpha * pulse)), 2,
                )
            arcade.draw_rect_outline(card_rect, ACCENT, 3)
        else:
            arcade.draw_rect_outline(card_rect, BORDER_IDLE, 1)

        # Cover art (or procedural placeholder + initial)
        img_rect = arcade.XYWH(card_x, card_y + strip_h / 2, cw - 20, ch - strip_h - 20)
        tex = self._cover_textures.get(i)
        if tex is not None:
            arcade.draw_texture_rect(tex, img_rect)
        else:
            arcade.draw_texture_rect(self._placeholders[i], img_rect)
            self._card_letter.text = game.name[:1].upper()
            self._card_letter.x = card_x
            self._card_letter.y = card_y + strip_h / 2
            self._card_letter.font_size = int(64 * scale)
            self._card_letter.draw()

        # Title
        self._card_title.text = game.name
        self._card_title.x = card_x
        self._card_title.y = card_y - ch / 2 + strip_h / 2
        self._card_title.color = arcade.color.WHITE if is_selected else (170, 176, 200)
        self._card_title.font_size = 17 if is_selected else 13
        self._card_title.bold = is_selected
        self._card_title.draw()

    def on_draw(self):
        self.clear()
        w = self.window.width
        h = self.window.height
        cx = w / 2
        cy = h / 2

        self.bg.draw()

        self._logo_glow.draw()
        self._logo.draw()
        self._tagline.draw()
        arcade.draw_line(cx - 140, h - 122, cx + 140, h - 122, (*ACCENT, 70), 1)

        if not self.games:
            self._no_games_text.draw()
            self._no_games_hint.draw()
            self.bg.draw_vignette()
            return

        # Draw unselected cards first so the selected one sits on top.
        order = [i for i in range(len(self.games)) if i != self.selected_index]
        order.append(self.selected_index)
        for i in order:
            self._draw_card(i, self.games[i], cx, cy)

        alpha = int(150 + 105 * (0.5 + 0.5 * math.sin(self.t * 3.0)))
        self._launch_hint.color = (*ACCENT, alpha)
        self._launch_hint.draw()

        self._counter.text = f"{self.selected_index + 1} / {len(self.games)}"
        self._counter.draw()
        self._nav_hint.draw()

        if self._error_message:
            err_rect = arcade.XYWH(cx, h - 140, 520, 40)
            arcade.draw_rect_filled(err_rect, (120, 26, 36, 225))
            arcade.draw_rect_outline(err_rect, (255, 110, 110), 1)
            self._error_text.text = self._error_message
            self._error_text.draw()

        self.bg.draw_vignette()
