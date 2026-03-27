import logging
import os
import signal
import subprocess
import threading

log = logging.getLogger(__name__)


class Watchdog:
    """
    Monitor a subprocess and force-kill it if it becomes unresponsive.

    Checks liveness on a heartbeat interval. If the process has been alive
    longer than `timeout` seconds without exiting, escalate:
    SIGTERM -> grace period -> SIGKILL.
    """

    def __init__(
        self,
        process: subprocess.Popen,
        timeout: float = 30.0,
        heartbeat: float = 2.0,
        grace: float = 5.0,
    ):
        self.process = process
        self.timeout = timeout
        self.heartbeat = heartbeat
        self.grace = grace
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._elapsed = 0.0

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def reset(self):
        """Reset the elapsed timer (call if the game shows signs of life)."""
        self._elapsed = 0.0

    def _run(self):
        while not self._stop_event.is_set():
            self._stop_event.wait(self.heartbeat)
            if self._stop_event.is_set():
                break

            poll = self.process.poll()
            if poll is not None:
                break

            self._elapsed += self.heartbeat
            if self._elapsed >= self.timeout:
                self._escalate()
                break

    def _escalate(self):
        pid = self.process.pid
        log.warning("Watchdog: process %d unresponsive for %.0fs, sending SIGTERM", pid, self._elapsed)
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
