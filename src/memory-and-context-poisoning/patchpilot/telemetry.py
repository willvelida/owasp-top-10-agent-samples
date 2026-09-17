"""Application Insights initialization with local logging fallback."""

from __future__ import annotations

import logging
import os


def configure_telemetry() -> logging.Logger:
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(logger_name="patchpilot")
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger("patchpilot")
