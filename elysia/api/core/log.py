import logging
import logging.handlers
import warnings
import time
from collections import defaultdict, deque
from rich.logging import RichHandler
import litellm
import dspy
from pathlib import Path

# Initialize the logger as a module-level variable
_logger = None

# Setup logs directory
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True, parents=True)


class DebugInfoFilter(logging.Filter):
    """Block all DEBUG and INFO level messages from console (kept in file logs)."""
    
    def filter(self, record):
        # Only allow WARNING and above to console
        return record.levelno >= logging.WARNING


class ConsoleNoiseFilter(logging.Filter):
    """Filter out noisy messages from console output (kept in file logs)."""
    
    noisy_substrings = [
        "closing websocket: unexpected asgi message",
        "websocket already closed",
        "connection open",
        "connection closed",
        "deprecationwarning",
        "resourcewarning",
        "userwarning",
    ]
    
    def filter(self, record):
        msg = record.getMessage().lower()
        # Filter out Python warnings from console
        if record.name == "py.warnings":
            return False
        # Filter out noisy substrings
        return not any(substring in msg for substring in self.noisy_substrings)


class RateLimitFilter(logging.Filter):
    """Rate limit duplicate messages to console (max N per minute)."""
    
    def __init__(self, max_per_minute=3):
        self.max = max_per_minute
        self.seen = defaultdict(lambda: deque())
    
    def filter(self, record):
        # Create key from logger name, level, and message prefix
        key = (record.name, record.levelno, record.getMessage()[:120])
        now = time.time()
        dq = self.seen[key]
        
        # Remove entries older than 60 seconds
        while dq and now - dq[0] > 60:
            dq.popleft()
        
        # Allow if under limit
        if len(dq) < self.max:
            dq.append(now)
            return True
        
        # Suppress if over limit
        return False


def get_logger():
    """Get the singleton logger instance."""
    global _logger
    if _logger is None:
        # Configure basic logging if not already configured
        if not logging.root.handlers:
            FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
            
            # File handler (rotating, logs to file)
            file_handler = logging.handlers.RotatingFileHandler(
                LOGS_DIR / "elysia.log",
                encoding="utf-8",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            file_handler.setFormatter(logging.Formatter(FORMAT))
            file_handler.setLevel(logging.DEBUG)
            
            # Console handler (minimal output - warnings/errors only)
            console_handler = RichHandler(rich_tracebacks=True, markup=True)
            console_handler.setLevel(logging.WARNING)
            # Add filters to console handler only - MUST be first to block DEBUG/INFO
            console_handler.addFilter(DebugInfoFilter())  # Blocks all DEBUG/INFO
            console_handler.addFilter(ConsoleNoiseFilter())
            console_handler.addFilter(RateLimitFilter(max_per_minute=2))
            
            logging.basicConfig(
                level="DEBUG",
                format=FORMAT,
                datefmt="[%X]",
                handlers=[file_handler, console_handler],
            )
            
            # Capture Python warnings and route through logging
            logging.captureWarnings(True)

        # Set log levels for specific loggers
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.INFO)
        logging.getLogger("fastapi").setLevel(logging.INFO)
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("starlette").setLevel(logging.INFO)
        logging.getLogger("tzlocal").setLevel(logging.WARNING)
        logging.getLogger("grpc").setLevel(logging.INFO)
        logging.getLogger("grpc._channel").setLevel(logging.WARNING)
        logging.getLogger("dspy").setLevel(logging.WARNING)
        logging.getLogger("dspy").propagate = False
        logging.getLogger("LiteLLM").setLevel(logging.WARNING)
        logging.getLogger("LiteLLM").propagate = False
        logging.getLogger("LiteLLM Router").setLevel(logging.WARNING)
        logging.getLogger("LiteLLM Router").propagate = False
        logging.getLogger("LiteLLM Proxy").setLevel(logging.WARNING)
        logging.getLogger("LiteLLM Proxy").propagate = False
        logging.getLogger("matplotlib").setLevel(logging.WARNING)
        logging.getLogger("matplotlib").propagate = False
        
        # Additional noisy loggers - set to WARNING/ERROR for console
        logging.getLogger("weaviate").setLevel(logging.WARNING)
        logging.getLogger("websockets").setLevel(logging.ERROR)
        logging.getLogger("pydantic").setLevel(logging.ERROR)
        logging.getLogger("py.warnings").setLevel(logging.WARNING)  # Python warnings logger
        
        # Suppress known noisy warnings at source (they'll still go to file logs)
        warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"websockets")
        warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"uvicorn\.protocols\.websockets")
        warnings.filterwarnings("ignore", category=ResourceWarning, module=r"rich\.text")
        warnings.filterwarnings("ignore", category=UserWarning, module=r"pydantic")
        warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"weaviate\.collections\.filters")

        _logger = logging.getLogger("rich")
        _logger.setLevel(logging.DEBUG)  # Allow DEBUG in code, filter blocks it from console

    return _logger


def set_log_level(level: str):
    """Set the level for the main application logger."""
    logger = get_logger()
    logger.setLevel(level)


# Initialize the logger
logger = get_logger()

dspy.disable_litellm_logging()
dspy.disable_logging()
litellm.suppress_debug_info = True
