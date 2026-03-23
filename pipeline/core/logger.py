import logging
import os.path
import sys
from datetime import datetime
from pathlib import Path

__all__ = ["pipeline_logger"]

pipeline_logger = logging.getLogger("pipeline")
pipeline_logger.setLevel(logging.DEBUG)

# Build up log path, write logs to user home dir
_exe_name = Path(sys.executable).stem
_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
_log_name = f"pipeline-{_exe_name}-{_datetime}.log"
_log_path = os.path.join(os.path.expanduser("~"), "pipeline_logs", _log_name)
os.makedirs(os.path.abspath(os.path.join(_log_path, "../..")), exist_ok=True)

# --- File handler ---
_file_handler = logging.FileHandler(_log_path)
_file_handler.setLevel(logging.DEBUG)  # Log everything to the file
_file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
_file_handler.setFormatter(_file_formatter)
pipeline_logger.addHandler(_file_handler)

# --- Stdout handler (INFO and below) ---
_stdout_handler = logging.StreamHandler(sys.stdout)
_stdout_handler.setLevel(logging.DEBUG)  # Send INFO and DEBUG to stdout
_stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)
_stdout_formatter = logging.Formatter("%(levelname)s: %(message)s")
_stdout_handler.setFormatter(_stdout_formatter)
pipeline_logger.addHandler(_stdout_handler)

# --- Stderr handler (WARNING and above) ---
_stderr_handler = logging.StreamHandler(sys.stderr)
_stderr_handler.setLevel(logging.WARNING)  # Send WARNING and above to stderr
_stderr_formatter = logging.Formatter("%(levelname)s: %(message)s")
_stderr_handler.setFormatter(_stderr_formatter)
pipeline_logger.addHandler(_stderr_handler)
