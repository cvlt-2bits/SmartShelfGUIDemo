"""
main script for the project, initializes the app and launches the GUI

File: main.py
Author: @cvlt
Date: 2024-10-03
Copyright: 2024, 2BiTS Srl., All rights reserved.

No part of this document must be reproduced in any form - including copied,
transcribed, printed, or by any electronic means - without specific written
permission from 2BiTS Srl.
"""

# ==============================================================================
# PACKAGES
# ==============================================================================

# ------------------------------------------------------------------------------
# STANDARD PACKAGES
# ------------------------------------------------------------------------------
import argparse
import json
import logging
import os
import sys
import signal
from datetime import datetime

# ------------------------------------------------------------------------------
# THIRD-PARTY PACKAGES
# ------------------------------------------------------------------------------
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication

# ------------------------------------------------------------------------------
# PROJECT PACKAGES
# ------------------------------------------------------------------------------
# Adjust the project root path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.insert(0, project_root)

# fmt: off
from src.serial_handler import SerialHandler                                    # noqa: E402
from src.gui.interface import MainWindow, ConfigWindow                          # noqa: E402
from src.parser import Parser                                                   # noqa: E402
# fmt: on

# ==============================================================================
# CONSTANTS
# ==============================================================================
LOG_LEVEL = logging.DEBUG


# ==============================================================================
# CLASSES
# ==============================================================================
class Application:
    """
    Class representing the Application behaviour.
    """

    def __init__(self, config: dict):
        # Initialize QApplication
        self.app = QApplication(sys.argv)

        # Check that configurations passed are valid
        self._get_config(config)

        # Initialize Widgets
        self.serial_handler = SerialHandler(self.serial_config)
        self.parser = Parser()
        self.window = MainWindow(self.shelf_config)  # Initialize GUI
        self.window.show()

        self._setup_signals_qt()

        # Handle termination signals (Ctrl+C / X button on window)
        self._register_signal_handlers()

        # Apply stylesheet
        with open("config/style.qss", "r") as f:
            _style = f.read()
            self.app.setStyleSheet(_style)

    def _get_config(self, config: dict):
        """Check that the configuration are valid and get the configuration for different components.

        Args:
            config (dict): _description_
        """
        # Get Configuration for different components
        self.serial_config = config.get("serial", None)
        self.shelf_config = config.get("shelf", None)

        # Check that configurations are present
        if self.serial_config is None:
            logging.error("Serial configuration not found in the configuration file.")
            sys.exit(1)
        if self.shelf_config is None:
            logging.error("Shelf configuration not found in the configuration file.")
            sys.exit(1)

    def _setup_signals_qt(self) -> None:
        """Connect signals and slots between children objects."""
        # Connect SerialHandler's signals to MainWindow's slot
        self.serial_handler.message_received.connect(self.parser.parse_message)
        self.serial_handler.message_sent.connect(self.parser.parse_message)
        self.serial_handler.serial_port_closed.connect(self.handle_serial_port_closed)
        self.serial_handler.serial_port_opened.connect(self.handle_serial_port_opened)

        # Connect Parser's signal to MainWindow's slot
        self.parser.message_parsed.connect(self.window.message_received)

        # Connect MainWindow's signals to SerialHandler
        self.window.serial_command.connect(self.serial_handler.send_message)

        self.window.serial_interface.open_settings.connect(self.open_config_window)

    def _close_port_if_open(self) -> None:
        """Close the serial port if it's open."""
        if self.serial_handler.serial.isOpen():
            self.serial_handler.serial.close()
            logging.info("Serial port closed.")

    def _handle_termination(self, sig, frame) -> None:
        """Signal handler to gracefully shut down

        Args:
            sig (int): Signal number
            frame (frame): Current stack frame
        """
        logging.debug(f"Received termination signal: {sig}. Closing the Application.")
        self._close_port_if_open()
        self.app.quit()

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for SIGINT and SIGTERM signals."""

        # Register the signal handler for SIGINT and SIGTERM
        signal.signal(signal.SIGINT, self._handle_termination)
        signal.signal(signal.SIGTERM, self._handle_termination)

    @Slot()
    def open_config_window(self) -> None:
        """
        Opens the ConfigWindow dialog.
        """
        self.config_window = ConfigWindow(self.serial_config)
        self.config_window.open_port.connect(self.apply_new_settings)
        self.config_window.close_port.connect(self.serial_handler.close_serial)
        self.config_window.exec()  # Show as modal dialog

    @Slot(dict)
    def apply_new_settings(self, new_config: dict) -> None:
        """
        Applies new serial port settings from the ConfigWindow.

        Args:
            new_config (dict): The new serial port configuration.
        """
        logging.info("Applying new serial port settings.")
        self.serial_handler.update_serial_config(new_config)

    @Slot(str)
    def handle_serial_port_closed(self, message: str) -> None:
        """
        Handles the serial_port_closed signal from SerialHandler.
        Updates the GUI accordingly.
        """
        self.parser.parse_message(message)

    @Slot(str)
    def handle_serial_port_opened(self, message: str) -> None:
        """
        Handles the serial_port_opened signal from SerialHandler.
        Updates the GUI accordingly.
        """
        self.parser.parse_message(message)

    def run(self) -> None:
        """Run the application."""
        try:
            sys.exit(self.app.exec())
        except Exception as e:
            logging.exception(f"Application encountered an unexpected error: {e}")
            self._close_port_if_open()
            sys.exit(1)


# ==============================================================================
# FUNCTIONS
# ==============================================================================
def log_setup() -> None:
    """Set up the logging system."""

    # Get the timestamp
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Define the log file name
    log_file = f"logs/{now}.log"

    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s.%(msecs)03d %(module)-17s %(funcName)-21s %(levelname)-8s %(message)s",
        datefmt="%y-%m-%d,%H:%M:%S",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],  # Log file + console
    )

    logging.debug("Logging system set up.")

    return


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Smart Shelf Demo App")
    parser.add_argument(
        "--config",
        type=str,
        default="config/app.json",
        help="Config file path (default: config/app.json)",
    )

    return parser.parse_args()


def load_config_json(path: str) -> dict:
    """Load the configuration file from path.

    Args:
        path (str): The path to the configuration file.

    Returns:
        dict: A dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the file is not found in the given path.
    """
    # Check if the file exists
    if not os.path.exists(path):
        logging.error(f"File not found in path: {path}")
        raise FileNotFoundError(f"File not found in path: {path}")

    # Open the file
    with open(path, "r") as file:
        # Catch a JSONDecodeError if the file is not a valid JSON
        try:
            config = json.load(file)

            # Print configuration
            logging.debug(config)

            return config
        except json.JSONDecodeError as e:
            logging.exception(f"Exception loading JSON Config {e}")
            raise


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    # Parse command-line arguments
    args = parse_cli_args()

    # Set up logging
    # TODO: (very low priority) Take LOG config from CLI Args
    log_setup()

    # Load configuration file
    config = load_config_json(args.config)

    # Initialize and run the application
    app = Application(config)
    app.run()


if __name__ == "__main__":
    main()
