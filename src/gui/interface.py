"""
Contains the Graphic User Interface definition for the project

File: interface.py
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
import logging

# ------------------------------------------------------------------------------
# THIRD-PARTY PACKAGES
# ------------------------------------------------------------------------------
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSlider,
    QSizePolicy,
)
from PySide6.QtGui import QPixmap

# ------------------------------------------------------------------------------
# PROJECT PACKAGES
# ------------------------------------------------------------------------------
from src.gui.shelf import ShelfWidget
from src.gui.serial import SerialInterfaceWidget
from src.message import Message
from src.gui.components import ScaledLabel

# ==============================================================================
# CONSTANTS
# ==============================================================================


# ==============================================================================
# CLASSES
# ==============================================================================


class ConfigWindow(QDialog):
    """
    Configuration window for serial port settings.
    """

    # Signals to communicate with Application
    open_port = Signal(dict)
    close_port = Signal()

    def __init__(self, config: dict):
        super().__init__()

        self._setup_ui(config)
        self._setup_layout()

        # Connect signals
        self.open_button.clicked.connect(self.open_port_clicked)
        self.close_button.clicked.connect(self.close_port_clicked)

    def _setup_ui(self, config: dict) -> None:
        """Set up the UI elements for the ConfigWindow.

        Args:
            config (dict): _description_
        """
        self.setWindowTitle("Serial Port Configuration")
        self.setModal(True)
        self.setGeometry(150, 150, 400, 300)

        # Initialize Widgets/Elements
        self.port_input = self._create_input_field("Port:", config.get("port", "COM3"))
        self.baudrate_input = self._create_input_field("Baudrate:", str(config.get("baudrate", "115200")))
        self.data_bits_input = self._create_combobox("Data Bits:", ["5", "6", "7", "8"], config.get("data_bits", 8))
        self.parity_input = self._create_combobox(
            "Parity:", ["None", "Even", "Odd", "Mark", "Space"], config.get("parity", "None")
        )
        self.stop_bits_input = self._create_combobox("Stop Bits:", ["1", "1.5", "2"], str(config.get("stop_bits", 1)))
        self.flow_control_input = self._create_combobox(
            "Flow Control:", ["None", "RTS/CTS", "XON/XOFF"], config.get("flow_control", "None")
        )

        # Open/Close Port Buttons
        self.open_button = QPushButton("Open Port")
        self.close_button = QPushButton("Close Port")

    def _setup_layout(self) -> None:
        """Set up the layout for the ConfigWindow."""
        # Set Layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Grid layout for labels and input fields
        self.grid_layout = QGridLayout()
        self.layout.addLayout(self.grid_layout)

        input_widgets = [
            (self.port_input["label"], self.port_input["input"]),
            (self.baudrate_input["label"], self.baudrate_input["input"]),
            (self.data_bits_input["label"], self.data_bits_input["input"]),
            (self.parity_input["label"], self.parity_input["input"]),
            (self.stop_bits_input["label"], self.stop_bits_input["input"]),
            (self.flow_control_input["label"], self.flow_control_input["input"]),
        ]

        for row, (label, input_widget) in enumerate(input_widgets):
            self.grid_layout.addWidget(label, row, 0)
            self.grid_layout.addWidget(input_widget, row, 1)

        # Buttons Layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.open_button)
        self.buttons_layout.addWidget(self.close_button)
        self.layout.addLayout(self.buttons_layout)

    def _create_input_field(self, label_text: str, default_value: str) -> dict:
        """Creates a QLabel and QLineEdit pair for input fields."""
        label = QLabel(label_text)
        input_field = QLineEdit(default_value)
        return {"label": label, "input": input_field}

    def _create_combobox(self, label_text: str, items: list, current_text: str) -> dict:
        """Creates a QLabel and QComboBox pair for selection fields."""
        label = QLabel(label_text)
        combobox = QComboBox()
        combobox.addItems(items)
        combobox.setCurrentText(f"{current_text}")
        return {"label": label, "input": combobox}

    @Slot()
    def open_port_clicked(self):
        """
        Gathers the settings from input fields and emits the open_port signal.
        """
        try:
            config = {
                "port": self.port_input["input"].text().strip(),
                "baudrate": int(self.baudrate_input["input"].text().strip()),
                "data_bits": int(self.data_bits_input["input"].currentText()),
                "parity": self.parity_input["input"].currentText(),
                "stop_bits": float(self.stop_bits_input["input"].currentText()),
                "flow_control": self.flow_control_input["input"].currentText(),
            }

            self.open_port.emit(config)
            QMessageBox.information(self, "Port Opened", "Serial port has been opened.")
        except ValueError as ve:
            QMessageBox.critical(self, "Invalid Input", f"Please ensure all fields are filled correctly.\nError: {ve}")

    @Slot()
    def close_port_clicked(self):
        """
        Emits the close_port signal.
        """
        self.close_port.emit()
        QMessageBox.information(self, "Port Closed", "Serial port has been closed.")


class MainWindow(QWidget):
    """Main window of the application."""

    virtual_shelf_update = Signal(Message)
    serial_command = Signal(str)  # New signal to propagate measure commands

    def __init__(self, config: dict):
        super().__init__()

        self._setup_ui(config)
        self._setup_layout()
        self._setup_signals_qt()

    def _setup_ui(self, config: dict) -> None:
        """Set up the UI elements for the MainWindow.

        Args:
            config (dict): _description_
        """
        # Initialize UI Elements
        self.setWindowTitle("Smart Shelf Demo")

        screen_geometry = self.screen().geometry()
        width = int(screen_geometry.width() * 0.6)
        height = int(screen_geometry.height() * 0.6)
        left = int(screen_geometry.width() * 0.1)
        top = int(screen_geometry.height() * 0.1)
        self.setGeometry(left, top, width, height)

        # Main Components
        self.shelf = ShelfWidget(config)  # Shows shelf replica
        self.serial_interface = SerialInterfaceWidget()  # Shows console with messages and input field
        self.terminal_placeholder_label = QLabel("Restricted Area: Nerds Only. Slide to Enter.")

        self.terminal_placeholder_label.setWordWrap(True)  # Enable word wrap for the QLabel
        self.terminal_placeholder_label.setObjectName("placeholder_label")

        # Slider Labels
        self.off_label = QLabel("0x00")  # Label representing "off" in a nerdy way
        self.off_label.setObjectName("off_label")
        self.on_label = QLabel("0x01")  # Label representing "on" in a nerdy way
        self.on_label.setObjectName("on_label")

        # Nerd Level Slider Switch
        self.nerd_level_slider = QSlider(Qt.Horizontal)
        self.nerd_level_slider.setMinimum(0)
        self.nerd_level_slider.setMaximum(1)
        self.nerd_level_slider.setValue(1)  # Default to showing the serial interface
        self.nerd_level_slider.setTickPosition(QSlider.NoTicks)
        self.nerd_level_slider.setTickInterval(1)
        self.nerd_level_slider.setFixedWidth(120)  # Fixed width for better control over the space it takes

        # Set the initial visibility of the serial interface based on the slider value
        self.serial_interface.setVisible(self.nerd_level_slider.value() == 1)

        # 2BiTS Logo
        self.logo = QPixmap("content/logo.png")

        # self.logo_image = QLabel()
        self.logo_image = ScaledLabel()
        self.logo_image.setPixmap(self.logo)

        self.logo_image.setScaledContents(False)

        # # Ensure the logo scales within the container
        self.logo_image.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Ignored
        )  # This will make sure the container is resized to fit the image

        # 2BiTS Website QR Code
        self.qr = QPixmap("content/qrcode.png")

        # self.qr_image = QLabel()
        self.qr_image = ScaledLabel()
        self.qr_image.setPixmap(self.qr)

        self.qr_image.setScaledContents(False)

        self.qr_image.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Ignored
        )  # This will make sure the image is resized to fit its container

        self.spacer = QWidget()

    def _setup_layout(self) -> None:
        """Set up the layout for the MainWindow."""

        # Main Layout
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setSpacing(1)
        self.setLayout(self.mainLayout)

        # Left Layout
        self.mainLayout.addWidget(self.shelf, stretch=80)

        # Right Layout
        self.rightLayout = QVBoxLayout()
        self.rightLayout.setSpacing(1)
        self.mainLayout.addLayout(self.rightLayout, stretch=20)

        # Create a horizontal layout for the slider and its left and right labels
        self.slider_layout = QHBoxLayout()
        self.slider_layout.addWidget(self.off_label, alignment=Qt.AlignRight)
        self.slider_layout.addWidget(self.nerd_level_slider)
        self.slider_layout.addWidget(self.on_label, alignment=Qt.AlignLeft)

        self.rightLayout.addLayout(self.slider_layout, stretch=10)

        self.nerd_level_layout = QVBoxLayout()
        self.rightLayout.addLayout(self.nerd_level_layout, stretch=55)

        # Add terminal interface
        self.nerd_level_layout.addWidget(self.serial_interface)
        self.terminal_placeholder_label.setVisible(self.nerd_level_slider.value() == 0)  # Initially hidden
        self.nerd_level_layout.addWidget(self.terminal_placeholder_label, stretch=50)

        # Layout for logo and QR code
        self.info_layout = QVBoxLayout()
        self.info_layout.setObjectName("info_layout")
        self.info_layout.setSpacing(10)
        self.rightLayout.addLayout(self.info_layout, stretch=35)

        self.info_layout.addWidget(self.logo_image, stretch=65)
        self.info_layout.addWidget(self.qr_image, stretch=25)
        self.info_layout.addWidget(self.spacer, stretch=10)

    def _setup_signals_qt(self) -> None:
        """Set up the signals for the MainWindow."""
        # Connect ShelfWidget's measure_command signal to MainWindow's shelf_serial_command
        self.shelf.serial_command.connect(self.serial_command.emit)
        # Connect SerialInterfaceWidget's signals to SerialHandler's slots
        self.serial_interface.send_message.connect(self.serial_command.emit)
        # Allows to signal that the shelf needs graphics update
        self.virtual_shelf_update.connect(self.shelf.update_shelf)
        # Nerd Level Slider Switch
        self.nerd_level_slider.valueChanged.connect(self.toggle_serial_interface)

    @Slot(Message)
    def message_received(self, message: Message):
        """
        Appends a received message to the SerialInterfaceWidget's text edit.

        Args:
            message (str): The message to append.
        """
        # logging.debug(f"MainWindow received: {message}")

        # Append the message to the SerialInterfaceWidget
        self.serial_interface.append_message(message.content)

        # Signal the ShelfWidget that there's new info
        self.virtual_shelf_update.emit(message)

    @Slot()
    def toggle_serial_interface(self):
        """
        Slot to toggle the visibility of the serial interface.
        """
        is_on = self.nerd_level_slider.value() == 1
        self.serial_interface.setVisible(is_on)
        self.terminal_placeholder_label.setVisible(self.nerd_level_slider.value() == 0)  # Initially hidden


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
