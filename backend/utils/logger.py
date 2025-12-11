"""
Enhanced logging configuration for Survey Sensei
Provides structured, colorized, and readable logging output
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and improved readability"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }

    EMOJI_MAP = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }

    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and structure"""

        # Get color for log level
        color = self.COLORS.get(record.levelname, '')
        emoji = self.EMOJI_MAP.get(record.levelname, '')

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]

        # Format module/function info
        location = f"{record.filename}:{record.lineno}"

        # Build formatted message
        parts = [
            f"{self.DIM}[{timestamp}]{self.RESET}",
            f"{color}{self.BOLD}{emoji} {record.levelname}{self.RESET}",
            f"{self.DIM}({location}){self.RESET}",
            f"{record.getMessage()}"
        ]

        formatted = " ".join(parts)

        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


class StructuredLogger:
    """
    Structured logger with semantic methods for different log types
    Provides context-aware logging with consistent formatting
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def api_request(self, method: str, endpoint: str, **kwargs):
        """Log API request"""
        extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"🌐 API Request: {method} {endpoint} {extras}")

    def api_response(self, status: int, endpoint: str, duration_ms: Optional[float] = None):
        """Log API response"""
        duration_str = f"({duration_ms:.0f}ms)" if duration_ms else ""
        emoji = "✅" if status < 400 else "❌"
        self.logger.info(f"{emoji} API Response: {status} {endpoint} {duration_str}")

    def agent_start(self, agent_name: str, action: str):
        """Log agent starting action"""
        self.logger.info(f"🤖 {agent_name}: Starting {action}")

    def agent_complete(self, agent_name: str, action: str, **metrics):
        """Log agent completion with metrics"""
        metrics_str = " | ".join(f"{k}={v}" for k, v in metrics.items())
        self.logger.info(f"🎉 {agent_name}: Completed {action} | {metrics_str}")

    def agent_error(self, agent_name: str, action: str, error: str):
        """Log agent error"""
        self.logger.error(f"💥 {agent_name}: Failed {action} | Error: {error}")

    def database_operation(self, operation: str, table: str, count: Optional[int] = None):
        """Log database operation"""
        count_str = f"({count} rows)" if count is not None else ""
        self.logger.info(f"🗄️  Database: {operation} {table} {count_str}")

    def external_api_call(self, service: str, endpoint: str, **kwargs):
        """Log external API call"""
        extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"🔌 External API: {service} → {endpoint} {extras}")

    def cache_operation(self, operation: str, key: str, hit: Optional[bool] = None):
        """Log cache operation"""
        hit_str = "HIT ✅" if hit is True else "MISS ❌" if hit is False else ""
        self.logger.info(f"💾 Cache: {operation} {key} {hit_str}")

    def step(self, step_number: int, description: str):
        """Log pipeline step"""
        self.logger.info(f"📍 Step {step_number}: {description}")

    def metric(self, name: str, value: any, unit: str = ""):
        """Log metric"""
        self.logger.info(f"📊 Metric: {name} = {value} {unit}")

    def separator(self, title: Optional[str] = None):
        """Log visual separator"""
        if title:
            self.logger.info(f"\n{'='*60}\n  {title}\n{'='*60}")
        else:
            self.logger.info(f"{'─'*60}")

    # Proxy standard logging methods
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, **kwargs)


def setup_logging(level: str = "INFO", use_colors: bool = True) -> None:
    """
    Configure logging for the entire application

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_colors: Whether to use colored output
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Set formatter
    if use_colors:
        formatter = ColoredFormatter()
    else:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) - %(message)s',
            datefmt='%H:%M:%S'
        )

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
