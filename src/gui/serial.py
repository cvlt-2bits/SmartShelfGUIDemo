"""
Contains the Graphic User Interface definition for the project

File: gui.py
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

# ------------------------------------------------------------------------------
# THIRD-PARTY PACKAGES
# ------------------------------------------------------------------------------
from PySide6.QtCore import Signal, Slot, QEvent
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# ------------------------------------------------------------------------------
# PROJECT PACKAGES
# ------------------------------------------------------------------------------

# ==============================================================================
# CONSTANTS
# ==============================================================================


# ==============================================================================
# CLASSES
# ==============================================================================


class SerialInterfaceWidget(QWidget):
    """
    Custom widget that encapsulates the serial interface UI components.
    """

    # Define custom signals
    send_message = Signal(str)
    open_settings = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_layout()
        self._setup_signals_qt()

    def _setup_ui(self) -> None:
        # Widgets
        # QTextEdit to display messages
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("serial_text_output")
        self.text_edit.setReadOnly(True)

        # QLineEdit for message input
        self.input_field = QLineEdit()
        self.input_field.setObjectName("terminal_input")
        self.input_field.setPlaceholderText(">")
        # Send message on Enter key press
        self.input_field.returnPressed.connect(self.handle_send)

        # QPushButton for sending messages
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("send_button")

        # QPushButton for opening settings
        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("settings_button")

    def _setup_layout(self) -> None:
        """Sets up the layout of the widget."""
        # Layout
        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(5)
        self.setLayout(self.layout)

        # Horizontal layout for text fields
        self.text_fields_layout = QVBoxLayout()
        self.text_fields_layout.setSpacing(0)

        # Horizontal layout for input and send button
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(3)

        self.text_fields_layout.addWidget(self.text_edit)
        self.text_fields_layout.addWidget(self.input_field)

        # QTextEdit to display messages
        self.layout.addLayout(self.text_fields_layout)
        # Buttons
        self.layout.addLayout(self.buttons_layout)

        # QLineEdit for message input
        self.buttons_layout.addWidget(self.settings_button)
        # QPushButton for sending messages
        self.buttons_layout.addWidget(self.send_button)

    def _setup_signals_qt(self) -> None:
        """
        Connects signals and slots between children objects.
        """
        # Signals
        # QPushButton for opening settings
        self.settings_button.clicked.connect(self.handle_settings)

        self.send_button.clicked.connect(self.handle_send)

    def append_message(self, message: str) -> None:
        """
        Appends a received or sent message to the text edit widget.

        Args:
            message (str): The message to append.
        """
        self.text_edit.append(message)
        # Auto-scroll to the bottom
        self.text_edit.moveCursor(QTextCursor.End)

    @Slot()
    def handle_send(self):
        """
        Handles the SEND button click event.
        Retrieves the message from the input field and emits it to be sent over serial.
        """
        message = self.input_field.text().strip()
        if not message:
            QMessageBox.warning(self, "Input Error", "Please enter a message to send.")
            return

        # Emit the send request
        self.send_message.emit(message)

        # Display the sent message in the GUI
        self.append_message(f"COMMAND[{message}]")

        # Clear the input field
        self.input_field.clear()

    @Slot()
    def handle_settings(self):
        """
        Handles the Settings button click event.
        Emits the open_settings signal to open the ConfigWindow.
        """
        self.open_settings.emit()


# ==============================================================================
# FUNCTIONS
# ==============================================================================

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    """
    This block is executed only if the file is run as a script.
    If this file is imported as a module in another script, this block will not
    be executed.
    """
