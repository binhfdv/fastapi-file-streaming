import logging
import sys
from colorama import init, Fore

# Initialize colorama for Windows compatibility
init(autoreset=True)

class CustomLogger:
    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }

    def __init__(self, log_file="app.log", level=logging.DEBUG):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)

        if not self.logger.hasHandlers():
            self._setup_handlers(log_file)

    def _setup_handlers(self, log_file):
        # Console handler with color formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(self._get_colored_formatter())

        # File handler without colors
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s]: %(message)s", "%Y-%m-%d %H:%M:%S"))

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def _get_colored_formatter(self):
        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                log_color = CustomLogger.COLORS.get(record.levelname, Fore.WHITE)
                return f"{log_color}[{self.formatTime(record)}] [{record.levelname}]: {record.getMessage()}"
        
        return ColoredFormatter()

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

# Example Usage
if __name__ == "__main__":
    log = CustomLogger()
    log.debug("This is a debug message.")
    log.info("This is an info message.")
    log.warning("This is a warning message.")
    log.error("This is an error message.")
    log.critical("This is a critical error!")
