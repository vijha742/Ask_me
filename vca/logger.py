"""
Logging configuration for vca
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


class VCALogger:
    """Centralized logging for vca"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = logging.getLogger('vca')
            self.logger.setLevel(logging.DEBUG)
            self._initialized = True
    
    def setup(self, repo_root: str = None, debug: bool = False):
        """
        Setup logging with file and console handlers
        
        Args:
            repo_root: Root directory of the repository (for log file location)
            debug: Enable debug mode with verbose output
        """
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # Console handler - only show WARNING and above unless debug mode
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.DEBUG if debug else logging.WARNING)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler - always log everything
        if repo_root:
            log_dir = Path(repo_root) / '.vca' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create log file with timestamp
            log_file = log_dir / f'vca_{datetime.now().strftime("%Y%m%d")}.log'
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
            
            self.logger.info(f"Logging initialized. Log file: {log_file}")
    
    def get_logger(self):
        """Get the logger instance"""
        return self.logger


# Global logger instance
def get_logger():
    """Get the global vca logger"""
    return VCALogger().get_logger()


def setup_logging(repo_root: str = None, debug: bool = False):
    """Setup logging for vca"""
    VCALogger().setup(repo_root, debug)
