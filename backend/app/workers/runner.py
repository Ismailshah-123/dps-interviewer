import asyncio
import logging
import signal
from app.core.config import settings
from app.core.observability import job_running
from app.workers.processor import run_pending_jobs_once

logger = logging.getLogger(__name__)

async def main():
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass
    logger.info("worker_started", extra={"event": "worker.started"})
    while not stop.is_set():
        try:
            await run_pending_jobs_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("worker_iteration_failed", extra={"event": "worker.iteration_failed"})
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.worker_poll_seconds)
        except asyncio.TimeoutError:
            pass
    logger.info("worker_stopping", extra={"event": "worker.stopping"})
    await asyncio.sleep(min(settings.worker_shutdown_seconds, 2))
    logger.info("worker_stopped", extra={"event": "worker.stopped"})

if __name__ == '__main__':
    asyncio.run(main())
