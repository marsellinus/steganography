import logging
import os
import sys
from flask.logging import default_handler

def configure_logging(app):
    """
    Configure logging for the application
    
    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure Flask logger
    app.logger.setLevel(logging.INFO)
    
    # Configure file handler
    file_handler = logging.FileHandler(os.path.join(logs_dir, 'app.log'))
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(module)s: %(message)s'
    ))
    
    # Configure console handler (better formatting)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(module)s: %(message)s'
    ))
    
    # Remove default handler and add our handlers
    app.logger.removeHandler(default_handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    return app
