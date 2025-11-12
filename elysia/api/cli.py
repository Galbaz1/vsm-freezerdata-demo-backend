import os
from dotenv import set_key, load_dotenv
from rich import print
from pathlib import Path
import logging.config

load_dotenv()

if "FIRST_START_ELYSIA" not in os.environ:
    print(
        "\n\n[bold green]Starting Elysia for the first time. This may take a minute to complete...[/bold green]\n\n"
    )
    set_key(".env", "FIRST_START_ELYSIA", "1")

import click
import uvicorn
from elysia.api.core.log import logger


# Setup logs directory and Uvicorn logging config
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True, parents=True)

class PathFilter:
    """
    Drop noisy static asset requests from uvicorn.access logs.
    """
    def __init__(self, patterns=None):
        default = ["/_next/", "/static/", "/favicon.ico", "/docs", "/redoc", "/openapi.json"]
        self.patterns = patterns or default

    def filter(self, record):
        msg = record.getMessage()
        if "GET " in msg or "HEAD " in msg:
            for p in self.patterns:
                if p in msg:
                    return False
        return True


class ConnectionNoiseFilter:
    """
    Drop repetitive connection open/closed noise.
    """
    def filter(self, record):
        msg = record.getMessage().lower()
        if "connection open" in msg or "connection closed" in msg:
            return False
        return True

UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        },
    },
    "filters": {
        "drop_static": {
            "()": "elysia.api.cli.PathFilter",
        },
        "drop_connections": {
            "()": "elysia.api.cli.ConnectionNoiseFilter",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": str(LOGS_DIR / "uvicorn.log"),
            "encoding": "utf-8",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "filters": ["drop_static", "drop_connections"],
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "fastapi": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


@click.group()
def cli():
    """Main command group for Elysia."""
    pass


@cli.command()
@click.option(
    "--port",
    default=8000,
    help="FastAPI Port",
)
@click.option(
    "--host",
    default="localhost",
    help="FastAPI Host",
)
@click.option(
    "--reload",
    default=True,
    help="FastAPI Reload",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error"]),
    help="Log level (file gets DEBUG, console gets this level)",
)
def start(port, host, reload, log_level):
    """
    Run the FastAPI application.
    
    Logs are written to:
    - logs/elysia.log (all logs)
    - logs/uvicorn.log (HTTP access logs)
    """
    logger.info("Elysia backend starting with host=%s port=%s reload=%s", host, port, reload)
    print(
        f"\n[cyan]Elysia ready on http://{host}:{port}[/cyan] "
        f"(logs → logs/elysia.log · logs/uvicorn.log)\n"
    )

    uvicorn.run(
        "elysia.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        log_config=UVICORN_LOG_CONFIG,
    )


if __name__ == "__main__":
    cli()
