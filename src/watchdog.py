"""System-level ESC watchdog.

Monitors the ESC key at the OS level. If ESC is held for longer than the
game's own quit threshold (default 3 seconds), the game process is assumed
frozen and is killed via SIGTERM -> SIGKILL escalation.

Games handle ESC themselves at 1 second (Landus ESC protocol). The system
watchdog fires at 3 seconds as a safety net for frozen/unresponsive games.

Platform support:
- macOS: Uses Quartz CGEventTap (avoids pynput's TSM threading crash)
- Linux: Uses pynput keyboard listener
"""

import logging
import os
import platform
import signal
import subprocess
import threading
import time

log = logging.getLogger(__name__)

_MACOS_ESC_KEYCODE = 53


class Watchdog:
    def __init__(
        self,
        process: subprocess.Popen,
        esc_kill_seconds: float = 3.0,
        grace: float = 5.0,
    ):
        self.process = process
        self.esc_kill_seconds = esc_kill_seconds
        self.grace = grace

        self._stop_event = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        self._esc_press_time: float | None = None
        self._lock = threading.Lock()

    def start(self):
        self._monitor_thread = threading.Thread(target=self._run, daemon=True)
        self._monitor_thread.start()

    def stop(self):
        self._stop_event.set()
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=2)

    def _esc_down(self):
        with self._lock:
            if self._esc_press_time is None:
                self._esc_press_time = time.monotonic()

    def _esc_up(self):
        with self._lock:
            self._esc_press_time = None

    def _run(self):
        if platform.system() == "Darwin":
            self._run_macos()
        else:
            self._run_pynput()

    def _run_macos(self):
        """Use Quartz CGEventTap to monitor ESC -- thread-safe on macOS."""
        try:
            import Quartz
        except ImportError:
            log.warning("pyobjc-framework-Quartz not available -- falling back to pynput")
            self._run_pynput()
            return

        watchdog_ref = self

        def _callback(proxy, event_type, event, refcon):
            keycode = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventKeycode,
            )
            if keycode == _MACOS_ESC_KEYCODE:
                if event_type == Quartz.kCGEventKeyDown:
                    watchdog_ref._esc_down()
                elif event_type == Quartz.kCGEventKeyUp:
                    watchdog_ref._esc_up()
            return event

        mask = (
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
            | Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp)
        )
        tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            mask,
            _callback,
            None,
        )

        if tap is None:
            log.warning(
                "CGEventTapCreate failed (grant Accessibility permissions to "
                "Terminal / IDE) -- watchdog ESC monitoring disabled"
            )
            return

        source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
        loop = Quartz.CFRunLoopGetCurrent()
        Quartz.CFRunLoopAddSource(loop, source, Quartz.kCFRunLoopDefaultMode)
        Quartz.CGEventTapEnable(tap, True)

        while not self._stop_event.is_set():
            Quartz.CFRunLoopRunInMode(Quartz.kCFRunLoopDefaultMode, 0.25, False)

            if self.process.poll() is not None:
                break

            with self._lock:
                if self._esc_press_time is not None:
                    held = time.monotonic() - self._esc_press_time
                    if held >= self.esc_kill_seconds:
                        self._escalate()
                        break

        Quartz.CGEventTapEnable(tap, False)

    def _run_pynput(self):
        """Use pynput keyboard listener (Linux / fallback)."""
        try:
            from pynput.keyboard import Key, Listener
        except ImportError:
            log.warning("pynput not installed -- watchdog ESC monitoring disabled")
            return

        def on_press(key):
            if key == Key.esc:
                self._esc_down()

        def on_release(key):
            if key == Key.esc:
                self._esc_up()

        listener = Listener(on_press=on_press, on_release=on_release)
        listener.start()

        while not self._stop_event.is_set():
            self._stop_event.wait(0.25)

            if self.process.poll() is not None:
                break

            with self._lock:
                if self._esc_press_time is not None:
                    held = time.monotonic() - self._esc_press_time
                    if held >= self.esc_kill_seconds:
                        self._escalate()
                        break

        listener.stop()

    def _escalate(self):
        pid = self.process.pid
        if self.process.poll() is not None:
            return

        log.warning(
            "Watchdog: ESC held %.1fs, game process %d still running -- sending SIGTERM",
            self.esc_kill_seconds, pid,
        )
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return

        try:
            self.process.wait(timeout=self.grace)
            log.info("Watchdog: process %d terminated after SIGTERM", pid)
        except subprocess.TimeoutExpired:
            log.warning("Watchdog: process %d did not respond to SIGTERM, sending SIGKILL", pid)
            try:
                os.kill(pid, signal.SIGKILL)
                self.process.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                log.error("Watchdog: failed to kill process %d", pid)
