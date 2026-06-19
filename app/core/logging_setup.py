import logging
import os
import sys


def setup_logging(log_file: str = "logs/aris.log") -> None:
    """
    Configures the Python logging system for the AI Recruitment Intelligence System.

    Logs INFO and above to both standard output and a rotating log file.
    Safe to call multiple times — subsequent calls are no-ops if already configured.

    Args:
        log_file: Path to the log file (relative to the working directory).
    """
    if logging.getLogger().handlers:
        # Already configured — skip re-initialisation
        return

    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
