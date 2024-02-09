#!/usr/bin/env python3

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(log_dir, log_level=logging.INFO):
    """
    Set up logging for the application.

    Args:
    log_dir (str): Directory where log files will be stored.
    log_level (int): Logging level. Default is logging.INFO.
    """
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            raise Exception(f"Error creating log directory {log_dir}: {e}")

    # Configure loggers
    loggers = {
        # log commands 
        'cmdline': {
            'filename': 'cmdline.log',
            'level': log_level,
            'format': '%(asctime)s - %(message)s'
        },
        # debug log
        'debug': {
            'filename': 'debug.log',
            'level': logging.DEBUG,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        # log json from AWS, etc.
        'json': {
            'filename': 'json.log',
            'level': logging.DEBUG,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }

    for key, value in loggers.items():
        handler = RotatingFileHandler(os.path.join(log_dir, value['filename']), maxBytes=10485760, backupCount=5)
        handler.setLevel(value['level'])
        formatter = logging.Formatter(value['format'])
        handler.setFormatter(formatter)
        logger = logging.getLogger(key)
        logger.setLevel(value['level'])
        logger.addHandler(handler)
        logger.propagate = False

def get_loggers():
    """
    Returns the configured loggers.

    Returns:
        dict: A dictionary of configured loggers.
    """
    return {
        'cmdline': logging.getLogger('cmdline'),
        'debug': logging.getLogger('debug'),
        'json': logging.getLogger('json')
    }
