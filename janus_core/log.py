"""Configure logger with yaml-styled format."""

import logging
from typing import Optional

from janus_core.janus_types import LogLevel

FORMAT = """
- timestamp: %(asctime)s
  level: %(levelname)s
  message: %(message)s
  trace: %(module)s
  line: %(lineno)d
""".strip()


def config_logger(
    name: str,
    filename: Optional[str] = None,
    level: LogLevel = logging.INFO,
    capture_warnings: bool = True,
):
    """
    Configure logger with yaml-styled format.

    Parameters
    ----------
    name : str
        Name of logger. Default is None.
    filename : Optional[str]
        Name of log file if writing logs. Default is None.
    level : LogLevel
        Threshold for logger. Default is logging.INFO.
    capture_warnings : bool
        Whether to capture warnings in log. Default is True.

    Returns
    -------
    Optional[logging.Logger]
        Configured logger if `filename` has been specified.
    """
    if filename:
        logger = logging.getLogger(name)

        logging.basicConfig(
            level=level,
            filename=filename,
            filemode="w",
            format=FORMAT,
            encoding="utf-8",
        )
        logging.captureWarnings(capture=capture_warnings)
    else:
        logger = None
    return logger
