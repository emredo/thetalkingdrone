"""
Simulation monitor module to track and log simulation time periodically.
"""

import threading
from typing import Optional

from src.environment.service import EnvironmentService
from src.utils.logger import logger


class SimulationMonitor:
    """Monitor for periodically logging simulation time and other metrics."""

    def __init__(self, environment: EnvironmentService, interval: int = 10):
        """
        Initialize simulation monitor.

        Args:
            environment: The environment service to monitor
            interval: Logging interval in seconds
        """
        self.environment = environment
        self.interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False

    def start(self) -> None:
        """Start the monitor thread."""
        if self._is_running:
            logger.warning("Simulation monitor is already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self._is_running = True
        logger.info(f"Simulation monitor started with {self.interval}s interval")

    def stop(self) -> None:
        """Stop the monitor thread."""
        if not self._is_running:
            logger.warning("Simulation monitor is not running")
            return

        self._stop_event.set()
        if self._thread:
            self._thread.join(
                timeout=2.0
            )  # Wait up to 2 seconds for thread to terminate
        self._is_running = False
        logger.info("Simulation monitor stopped")

    def _monitor_loop(self) -> None:
        """Internal monitoring loop that runs in a separate thread."""
        while not self._stop_event.is_set():
            # Log the current simulation time (but don't update it)
            sim_time = self.environment.state.time
            logger.info(f"Simulation time: {sim_time:.2f}s")

            # Sleep for the specified interval
            # Using wait with timeout allows for responsive shutdown
            self._stop_event.wait(self.interval)


# Singleton instance to be used across the application
_simulation_monitor: Optional[SimulationMonitor] = None


def get_simulation_monitor(environment: EnvironmentService) -> SimulationMonitor:
    """Get or create the singleton simulation monitor."""
    global _simulation_monitor
    if _simulation_monitor is None:
        _simulation_monitor = SimulationMonitor(environment)
    return _simulation_monitor
