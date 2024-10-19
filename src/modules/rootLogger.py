#!/usr/bin/python3

import logging

def save_logging_configuration():
    """
    Saves the current logging configuration (loggers, handlers, and formatters).
    
    Returns:
    dict: A dictionary containing the saved logging configuration.
    """
    saved_config = {}
    
    root_logger = logging.getLogger()
    saved_config['level'] = root_logger.level
    saved_config['handlers'] = []
    
    for handler in root_logger.handlers:
        handler_config = {
            'class': handler.__class__,
            'level': handler.level,
            'formatter': handler.formatter._fmt if handler.formatter else None
        }
         # Special case for FileHandler (or other handlers needing extra arguments)
        if isinstance(handler, logging.FileHandler):
            handler_config['filename'] = handler.baseFilename
        elif isinstance(handler, logging.StreamHandler):
            handler_config['stream'] = handler.stream

        saved_config['handlers'].append(handler_config)
    
    return saved_config


def restore_logging_configuration(saved_config):
    """
    Restores the logging configuration from the provided saved configuration.

    Args:
    saved_config (dict): The saved logging configuration to restore.
    """
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(saved_config['level'])

    for handler_config in saved_config['handlers']:
        handler_class = handler_config['class']

        # Handle FileHandler by passing in the required filename
        if handler_class == logging.FileHandler:
            handler = handler_class(handler_config['filename'])

        # Handle StreamHandler by passing in the stream (default: sys.stderr)
        elif handler_class == logging.StreamHandler:
            handler = handler_class(handler_config.get('stream', None))

        else:
            # Handle other handlers that do not require specific arguments
            handler = handler_class()

        handler.setLevel(handler_config['level'])

        if handler_config['formatter']:
            formatter = logging.Formatter(handler_config['formatter'])
            handler.setFormatter(formatter)

        root_logger.addHandler(handler)
