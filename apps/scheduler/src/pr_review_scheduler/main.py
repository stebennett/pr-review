"""Main entry point for the PR-Review Scheduler.

This module starts the scheduler service and handles graceful shutdown.

Usage:
    python -m pr_review_scheduler.main
"""

import logging
import signal
import sys
import time
from types import FrameType

from pr_review_scheduler import __version__
from pr_review_scheduler.config import get_settings
from pr_review_scheduler.scheduler import (
    create_scheduler,
    get_all_jobs,
    shutdown_scheduler,
    start_scheduler,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global scheduler instance for signal handlers
_scheduler = None


def signal_handler(signum: int, frame: FrameType | None) -> None:
    """Handle termination signals for graceful shutdown.

    Args:
        signum: Signal number received.
        frame: Current stack frame.
    """
    sig_name = signal.Signals(signum).name
    logger.info("Received signal %s, shutting down...", sig_name)
    if _scheduler:
        shutdown_scheduler(_scheduler, wait=True)
    sys.exit(0)


def main() -> None:
    """Main entry point for the scheduler service."""
    global _scheduler

    settings = get_settings()

    logger.info("Starting PR-Review Scheduler v%s", __version__)
    logger.info("Configuration:")
    logger.info("  Database URL: %s", settings.database_url)
    logger.info("  Timezone: %s", settings.scheduler_timezone)
    logger.info("  Poll interval: %d seconds", settings.schedule_poll_interval)
    logger.info("  Executor pool size: %d", settings.scheduler_executor_pool_size)

    # Create and start scheduler
    _scheduler = create_scheduler()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        start_scheduler(_scheduler)
        logger.info("Scheduler is running. Press Ctrl+C to exit.")

        # Keep the main thread alive and log status periodically
        status_interval = 300  # Log status every 5 minutes
        elapsed = 0
        while True:
            time.sleep(1)
            elapsed += 1
            if elapsed >= status_interval:
                job_count = len(get_all_jobs(_scheduler))
                logger.info("Scheduler status: %d active jobs", job_count)
                elapsed = 0

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        shutdown_scheduler(_scheduler, wait=True)


if __name__ == "__main__":
    main()
