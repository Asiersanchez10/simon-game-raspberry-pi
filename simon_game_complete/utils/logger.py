#!/usr/bin/env python3
"""
Utilidad: Logger
Sistema de logging centralizado para todos los procesos
"""

import logging
import os
from datetime import datetime


def setup_logger(name, level=logging.INFO):
    """
    Configura un logger con formato y handlers personalizados
    
    Args:
        name: Nombre del logger (normalmente el nombre del módulo)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    
    # Crear directorio de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Formato de log
    log_format = logging.Formatter(
        '%(asctime)s - [%(processName)s/%(threadName)s] - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Handler para archivo
    log_file = os.path.join(
        log_dir,
        f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    return logger
