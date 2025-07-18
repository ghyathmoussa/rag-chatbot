import sys
from pathlib import Path
from loguru import logger
from typing import Optional


class Logger:
    """
    A centralized logger class using Loguru for the RAG chatbot application.
    Provides structured logging with file rotation and customizable formatting.
    """
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        """
        Initialize the logger with specified configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional path to log file. If None, uses default location
        """
        self.log_level = log_level.upper()
        self.log_file = log_file or "logs/rag_chatbot.log"
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure the logger with custom format and handlers."""
        # Remove default handler
        logger.remove()
        
        # Custom format for console output
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        
        # Custom format for file output
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        )
        
        # Add console handler with colors
        logger.add(
            sys.stderr,
            format=console_format,
            level=self.log_level,
            colorize=True
        )
        
        # Create logs directory if it doesn't exist
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add file handler with rotation
        logger.add(
            self.log_file,
            format=file_format,
            level=self.log_level,
            rotation="10 MB",  # Rotate when file reaches 10 MB
            retention="30 days",  # Keep logs for 30 days
            compression="zip",  # Compress old logs
            enqueue=True,  # Thread-safe logging
            backtrace=True,  # Include full traceback in error logs
            diagnose=True  # Include variable values in traceback
        )
        
        # Add error file handler for errors and above
        error_log_file = str(log_path.parent / f"error_{log_path.name}")
        logger.add(
            error_log_file,
            format=file_format,
            level="ERROR",
            rotation="5 MB",
            retention="60 days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
    
    def get_logger(self):
        """Return the configured logger instance."""
        return logger
    
    def set_level(self, level: str):
        """Change the logging level dynamically."""
        self.log_level = level.upper()
        self._setup_logger()


# Global logger instance
_logger_instance = None


def get_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> logger:
    """
    Get or create a global logger instance.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        
    Returns:
        Configured Loguru logger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = Logger(log_level, log_file)
    
    return _logger_instance.get_logger()


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Setup the global logger with specified configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    """
    global _logger_instance
    _logger_instance = Logger(log_level, log_file)


# Convenience functions for direct logging
def debug(message: str, **kwargs):
    """Log a debug message."""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs):
    """Log an info message."""
    get_logger().info(message, **kwargs)


def warning(message: str, **kwargs):
    """Log a warning message."""
    get_logger().warning(message, **kwargs)


def error(message: str, **kwargs):
    """Log an error message."""
    get_logger().error(message, **kwargs)


def critical(message: str, **kwargs):
    """Log a critical message."""
    get_logger().critical(message, **kwargs)


def exception(message: str, **kwargs):
    """Log an exception with traceback."""
    get_logger().exception(message, **kwargs)


# Example usage and configuration
if __name__ == "__main__":
    # Example usage
    setup_logger("DEBUG")
    
    logger = get_logger()
    logger.info("Logger initialized successfully")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Using convenience functions
    info("RAG Chatbot application started")
    debug("Processing user query...")
    warning("API rate limit approaching")
    error("Failed to connect to vector database")
