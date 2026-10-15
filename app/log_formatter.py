import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formata cada registro de log como uma linha JSON (um objeto por linha)."""

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # Traceback vai dentro do JSON para o log continuar sendo uma linha só
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log, ensure_ascii=False)
