import logging
import json
from datetime import datetime, timezone
import uuid
import os

class JSONFormatter(logging.Formatter):
    """Formateador de logs en formato JSON estructurado para trazabilidad"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "modulo": record.name,
            "mensaje": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', str(uuid.uuid4())),
            "archivo": record.filename,
            "linea": record.lineno
        }
        
        if record.exc_info and record.exc_info[1]:
            log_entry["error"] = str(record.exc_info[1])
            log_entry["tipo_error"] = type(record.exc_info[1]).__name__
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logger():
    """Configurar logger estructurado"""
    
    os.makedirs("logs", exist_ok=True)
    
    logger = logging.getLogger("aegis")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    # Handler para archivo JSON
    file_handler = logging.FileHandler("logs/aegis.log", encoding="utf-8")
    file_handler.setFormatter(JSONFormatter())
    
    # Handler para errores
    error_handler = logging.FileHandler("logs/aegis_errores.log", encoding="utf-8")
    error_handler.setFormatter(JSONFormatter())
    error_handler.setLevel(logging.ERROR)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()