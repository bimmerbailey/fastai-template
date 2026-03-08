import time
from dataclasses import dataclass, field

import structlog
from asgi_correlation_id.context import correlation_id
from fastapi import FastAPI
from starlette.types import Message, Receive, Scope, Send


@dataclass
class LoggingMiddleware:
    app: FastAPI
    logger: structlog.stdlib.BoundLogger = field(
        default_factory=lambda: structlog.stdlib.get_logger(__name__)
    )

    async def __call__(self, scope: "Scope", receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # NOTE: Only logs on http requests, not startup/shutdown events
            await self.app(scope, receive, send)
            return

        structlog.contextvars.clear_contextvars()
        request_id = correlation_id.get()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter_ns()
        status_code = 500

        async def send_logging(message: "Message") -> None:
            """Getting the status code from the response"""
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_logging)
        except Exception:
            self.logger.exception("Unhandled exception")
            raise
        finally:
            process_time = time.perf_counter_ns() - start_time

            client_host = None
            client_port = None
            if scope["client"] is not None:
                client_host, client_port = scope["client"]

            self.logger.info(
                "Handled request",
                client_host=client_host,
                client_port=client_port,
                http_path=scope["path"],
                http_status_code=status_code,
                http_method=scope["method"],
                http_version=scope["http_version"],
                http_duration_ms=process_time / 10e6,
                request_id=request_id,
            )
