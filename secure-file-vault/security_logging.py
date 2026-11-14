import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import has_request_context, request
from flask_login import current_user


LOG_FOLDER = Path(__file__).resolve().parent / "logs"
LOG_FOLDER.mkdir(exist_ok=True)

LOG_FILE = LOG_FOLDER / "security.log"

security_logger = logging.getLogger("security")

if not security_logger.handlers:
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8"
    )

    handler.setFormatter(logging.Formatter("%(message)s"))
    security_logger.addHandler(handler)

security_logger.setLevel(logging.INFO)
security_logger.propagate = False


def log_security_event(event, outcome, user_id=None, details=None):
    if user_id is None and has_request_context():
        if current_user.is_authenticated:
            user_id = current_user.id

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "user_id": user_id,
        "source_ip": request.remote_addr if has_request_context() else None,
        "outcome": outcome
    }

    if details:
        log_entry["details"] = details

    security_logger.info(
        json.dumps(log_entry, ensure_ascii=False)
    )