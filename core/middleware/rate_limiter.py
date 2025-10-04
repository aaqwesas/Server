# ratelimit.py
import time
from collections import defaultdict
from typing import DefaultDict
from fastapi import FastAPI, Request
import asyncio
import logging

from fastapi.responses import JSONResponse


logger = logging.getLogger("server")


class RateLimiter:
    def __init__(self, max_requests: int = 5, reset_interval_seconds: int = 3600):
        self.max_requests = max_requests
        self.reset_interval_seconds = reset_interval_seconds
        self.client_requests: DefaultDict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_ip: str) -> bool:
        async with self._lock:
            if self.client_requests[client_ip] < self.max_requests:
                self.client_requests[client_ip] += 1
                return True
            return False

    async def reset_counters(self):
        async with self._lock:
            self.client_requests.clear()
        logger.info("[RateLimiter] Counters reset")

    def get_reset_time(self) -> int:
        now = time.time()
        return int((now // self.reset_interval_seconds) + 1) * self.reset_interval_seconds
            


async def periodic_reset_rate_limit(limiter: RateLimiter):
    interval = limiter.reset_interval_seconds

    now = time.time()
    next_reset = ((now // interval) + 1) * interval
    initial_delay = next_reset - now

    logger.info("RateLimiter: First reset in %.0f seconds at %d", initial_delay, next_reset)
    await asyncio.sleep(initial_delay)

    while True:
        await limiter.reset_counters()
        await asyncio.sleep(interval)


async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/tasks/health":
        return await call_next(request)

    limiter = request.app.state.limiter
    client_ip = request.client.host

    if await limiter.is_allowed(client_ip):
        return await call_next(request)

    # Build response on failure
    reset_time = limiter.get_reset_time()
    headers = {
        "Retry-After": str(int(reset_time - time.time())),
        "X-RateLimit-Limit": str(limiter.max_requests),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int(reset_time)),
    }
    return JSONResponse(
        status_code=429,
        content="Rate limit exceeded. Try again later.",
        headers=headers,
    )
    
def rate_limit_reset_scheduler(limiter):
    return asyncio.create_task(periodic_reset_rate_limit(limiter))

async def stop_rate_limit_scheduler(app) -> None:
    if hasattr(app.state, "scheduler_rate"):
        app.state.scheduler_rate.cancel()
        try:
            await app.state.scheduler_rate
        except (asyncio.CancelledError, RuntimeError):
            pass
        logger.info("Rate limit scheduler stopped.")
    else:
        logger.debug("No rate limit scheduler found to stop.")