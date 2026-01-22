"""Main entry point for the PR-Review Scheduler.

This module starts the scheduler service and handles graceful shutdown.

Usage:
    python -m pr_review_scheduler.main
"""

import logging
import signal
import sys
import time
from threading import Event, Thread
from types import FrameType

from pr_review_scheduler import __version__
from pr_review_scheduler.config import get_settings
from pr_review_scheduler.scheduler import (
    create_scheduler,
    shutdown_scheduler,
    start_scheduler,
)
from pr_review_scheduler.sync import sync_schedules

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global scheduler instance for signal handlers
_scheduler = None

# Event for signaling threads to stop
_stop_event = Event()


def signal_handler(signum: int, frame: FrameType | None) -> None:
    """Handle termination signals for graceful shutdown.

    Args:
        signum: Signal number received.
        frame: Current stack frame.
    """
    sig_name = signal.Signals(signum).name
    logger.info("Received signal %s, shutting down...", sig_name)
    _stop_event.set()
    if _scheduler:
        shutdown_scheduler(_scheduler, wait=True)
    sys.exit(0)


def polling_loop(scheduler, poll_interval: int) -> None:
    """Background thread that polls for schedule changes.

    Args:
        scheduler: The APScheduler BackgroundScheduler instance.
        poll_interval: Seconds between polls.
    """
    logger.info("Starting schedule polling loop (interval: %ds)", poll_interval)
    while not _stop_event.is_set():
        try:
            sync_schedules(scheduler)
        except Exception as e:
            logger.error("Error syncing schedules: %s", e)
        _stop_event.wait(timeout=poll_interval)
    logger.info("Polling loop stopped")


def main() -> None:
    """Main entry point for the scheduler service."""
    global _scheduler

    settings = get_settings()

    logger.info("Starting PR-Review Scheduler v%s", __version__)
    logger.info("Database URL: %s", settings.database_url)
    logger.info("Poll interval: %d seconds", settings.schedule_poll_interval)

    # Create and start scheduler
    _scheduler = create_scheduler()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        start_scheduler(_scheduler)

        # Initial sync
        logger.info("Performing initial schedule sync...")
        sync_schedules(_scheduler)

        # Start polling thread
        poll_thread = Thread(
            target=polling_loop,
            args=(_scheduler, settings.schedule_poll_interval),
            daemon=True,
        )
        poll_thread.start()

        logger.info("Scheduler is running. Press Ctrl+C to exit.")

        # Keep the main thread alive
        while not _stop_event.is_set():
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        _stop_event.set()
        shutdown_scheduler(_scheduler, wait=True)


if __name__ == "__main__":
    main()
