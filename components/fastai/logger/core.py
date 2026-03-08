"""
MIT License

Copyright (c) 2023 Thomas GAUDIN

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import sys
from enum import StrEnum

import structlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from structlog.types import EventDict, Processor


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class LogSettings(BaseSettings):
    model_config = SettingsConfigDict(frozen=True, env_prefix="LOG_")

    json_format: bool = Field(default=False)
    level: LogLevel = Field(default=LogLevel.INFO)
    # CLI-specific settings
    verbose: bool = Field(default=False, description="Enable verbose/debug logging")


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


# Base processors shared by all logging configurations
BASE_PROCESSORS: list[Processor] = [
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
]

# API-specific processors for web applications
API_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.ExtraAdder(),
    drop_color_message_key,
]

# CLI-specific processors for command-line applications
CLI_PROCESSORS: list[Processor] = [
    structlog.stdlib.filter_by_level,
    structlog.processors.UnicodeDecoder(),
]

# Combined processor lists for convenience
SHARED_PROCESSORS: list[Processor] = BASE_PROCESSORS + API_PROCESSORS


def setup_api_logging(settings: LogSettings = LogSettings()):
    log_renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    base_processors = SHARED_PROCESSORS.copy()
    if settings.json_format:
        base_processors.append(structlog.processors.format_exc_info)
        log_renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=base_processors
        + [
            # Prepare event dict for `ProcessorFormatter`.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=base_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            # Remove _record & _from_structlog.
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            log_renderer,
        ],
    )

    # TODO: FileHandler
    handler = logging.StreamHandler()
    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.level)

    for _log in ["uvicorn", "uvicorn.error"]:
        # Clear the log handlers for uvicorn loggers, and enable propagation
        # so the messages are caught by our root logger and formatted correctly
        # by structlog
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = True

    def handle_exception(exc_type, exc_value, exc_traceback):
        """
        Log any uncaught exception instead of letting it be printed by Python
        (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
        See https://stackoverflow.com/a/16993115/3641865
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        root_logger.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception


def setup_cli_logging(settings: LogSettings = LogSettings()):
    """
    Configure structured logging for CLI applications.

    Args:
        settings: LogSettings instance with CLI logging configuration.
    """

    # Build a processor list: base + CLI-specific + renderer
    processors = BASE_PROCESSORS + CLI_PROCESSORS

    # Choose renderer based on format preference
    # For CLI, prioritize console_format over json_format for better UX
    if settings.json_format:
        processors.append(structlog.processors.format_exc_info)
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging level
    logging.basicConfig(level=settings.level)


def build_processors(
    include_api: bool = False,
    include_cli: bool = False,
    custom_processors: list[Processor] = None,
) -> list[Processor]:
    """
    Build a custom processor list by combining base processors with specific sets.

    Args:
        include_api: Include API-specific processors (contextvars, extra fields, etc.)
        include_cli: Include CLI-specific processors (filtering, unicode, etc.)
        custom_processors: Additional custom processors to include

    Returns:
        List of structlog processors ready for configuration

    Examples:
        # For a custom CLI-like application
        processors = build_processors(include_cli=True, custom_processors=[my_processor])

        # For a hybrid application needing both API and CLI features
        processors = build_processors(include_api=True, include_cli=True)
    """
    processors = BASE_PROCESSORS.copy()

    if include_api:
        processors.extend(API_PROCESSORS)

    if include_cli:
        processors.extend(CLI_PROCESSORS)

    if custom_processors:
        processors.extend(custom_processors)

    return processors
