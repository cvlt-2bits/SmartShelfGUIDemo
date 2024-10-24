"""
Module to read and write to a serial port using PySide6.

File: serial_handler.py
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
import sys
from typing import Optional

# ------------------------------------------------------------------------------
# THIRD-PARTY PACKAGES
# ------------------------------------------------------------------------------
from PySide6.QtCore import QObject, Slot, Signal
from PySide6.QtSerialPort import QSerialPort

# ------------------------------------------------------------------------------
# PROJECT PACKAGES
# ------------------------------------------------------------------------------
# Import project-specific modules (i.e., from this project, under src folder)
# from this_project import some_module

# ==============================================================================
# CONSTANTS
# ==============================================================================
DEFAULT_BAUDRATE = 115200
DEFAULT_DATA_BITS = 8
DEFAULT_PARITY = "None"
DEFAULT_STOP_BITS = 1
DEFAULT_FLOW_CONTROL = "RTS/CTS"


# ==============================================================================
# CLASSES
# ==============================================================================
class SerialHandler(QObject):
    """
    Handles serial communication

    Attributes:
        serial (QSerialPort): The serial port object.
    """

    # Signals to communicate with GUI
    message_received = Signal(str)  # Define a custom signal to emit received messages
    message_sent = Signal(str)  # Define a custom signal to emit sent messages
    serial_port_closed = Signal(str)  # Define a custom signal to emit closed serial port
    serial_port_opened = Signal(str)  # Define a custom signal to emit opened serial port
    serial_port_error = Signal(str)  # Define a custom signal to emit serial port errors

    def __init__(self, serial_config: dict):
        """
        Initializes the SerialHandler with the given parameters.

        Args:
            serial_config (dict): A dictionary containing the serial port configuration.
        """
        super().__init__()

        # Declare the SerialHandler attributes
        self.serial = QSerialPort()

        # Configure the serial port
        self.configure_serial(serial_config)

        # Connect signals
        self.serial.readyRead.connect(self.read_data)
        self.serial.errorOccurred.connect(self.handle_error)

        self.open_serial()

    def open_serial(self) -> None:
        """
        Opens the serial port if it's not already open.
        """
        if not self.serial.isOpen():
            if self.serial.open(QSerialPort.ReadWrite):
                logging.debug(f"Serial port {self.serial.portName()} opened.")
                self.serial_port_opened.emit(f"Serial port {self.serial.portName()} opened.")

            else:
                logging.error(f"Failed to open serial port {self.serial.portName()}: {self.serial.errorString()}")
        else:
            logging.warning(f"Serial port {self.serial.portName()} is already open.")

    def configure_serial(self, config: dict) -> None:
        """Configure the serial port with the given configuration.

        Args:
            config (dict): A dictionary containing the serial port configuration.
        """
        logging.debug("Serial port configuration:")

        try:
            self._set_port_name(config.get("port"))
            self._set_baudrate(config.get("baudrate", DEFAULT_BAUDRATE))
            self._set_data_bits(config.get("data_bits", DEFAULT_DATA_BITS))
            self._set_parity(config.get("parity", DEFAULT_PARITY))
            self._set_stop_bits(config.get("stop_bits", DEFAULT_STOP_BITS))
            self._set_flow_control(config.get("flow_control", DEFAULT_FLOW_CONTROL))
        except ValueError as e:
            logging.error(f"Configuration error: {e}")
            raise

        logging.debug("Serial port configured successfully.")

    def _set_port_name(self, port_name: Optional[str]) -> None:
        """Set the port name for the serial port.

        Args:
            port_name: The name of the serial port.

        Raises:
            ValueError: If port_name is missing.
        """
        if not port_name:
            raise ValueError("Port name must be specified.")

        logging.debug(f"- Name[{port_name}]")

        self.serial.setPortName(port_name)

    def _set_baudrate(self, baudrate: int) -> None:
        """Set the baudrate for the serial port.

        Args:
            baudrate (int): The baudrate to set.
        """
        logging.debug(f"- Baudrate[{baudrate}]")

        self.serial.setBaudRate(baudrate)

    def _set_data_bits(self, data_bits: int) -> None:
        """Set the data bits for the serial port.

        Args:
            data_bits (int): The number of data bits.
        """
        logging.debug(f"- DataBits[{data_bits}]")

        match data_bits:
            case 5:
                data_bits = QSerialPort.Data5
            case 6:
                data_bits = QSerialPort.Data6
            case 7:
                data_bits = QSerialPort.Data7
            case 8:
                data_bits = QSerialPort.Data8
            case _:
                data_bits = QSerialPort.Data8
        self.serial.setDataBits(data_bits)

    def _set_parity(self, parity: str) -> None:
        """Set the parity for the serial port.

        Args:
            parity (str): The parity to set.
        """
        logging.debug(f"- Parity[{parity}]")

        match parity:
            case "None":
                parity = QSerialPort.NoParity
            case "Even":
                parity = QSerialPort.EvenParity
            case "Odd":
                parity = QSerialPort.OddParity
            case "Mark":
                parity = QSerialPort.MarkParity
            case "Space":
                parity = QSerialPort.SpaceParity
            case _:
                pass  # Default action if no pattern matches
        self.serial.setParity(parity)

    def _set_stop_bits(self, stop_bits: float) -> None:
        """Set the stop bits for the serial port.

        Args:
            stop_bits (float): The number of stop bits.
        """
        logging.debug(f"- StopBits[{stop_bits}]")

        match stop_bits:
            case 1:
                stop_bits = QSerialPort.OneStop
            case 1.5:
                stop_bits = QSerialPort.OneAndHalfStop
            case 2:
                stop_bits = QSerialPort.TwoStop
            case _:
                stop_bits = QSerialPort.OneStop
        self.serial.setStopBits(stop_bits)

    def _set_flow_control(self, flow_control: str) -> None:
        """Set the flow control for the serial port.

        Args:
            flow_control (str): The flow control to set.
        """
        logging.debug(f"- FlowControl[{flow_control}]")

        match flow_control:
            case "None":
                flow_control = QSerialPort.NoFlowControl
            case "RTS/CTS":
                flow_control = QSerialPort.HardwareControl
            case "XON/XOFF":
                flow_control = QSerialPort.SoftwareControl
            case _:
                flow_control = QSerialPort.NoFlowControl
        self.serial.setFlowControl(flow_control)

    def update_serial_config(self, new_config: dict):
        """
        Updates the serial port configuration.

        Args:
            new_config (dict): The new serial port configuration.
        """
        is_open = self.serial.isOpen()
        if is_open:
            self.close_serial()

        try:
            self.configure_serial(new_config)

            self.open_serial()

        except ValueError as e:
            logging.error(f"Failed to update serial port configuration: {e}")

    @Slot()
    def close_serial(self):
        """
        Closes the serial port if it is open.
        """
        if self.serial.isOpen():
            logging.debug(f"Closing {self.serial.portName()}.")
            self.serial.close()
            self.serial_port_closed.emit(f"{self.serial.portName()} closed.")

            logging.debug(f"{self.serial.portName()} closed.")
        else:
            logging.warning("Attempted to close a serial port that is not open.")

    @Slot()
    def handle_error(self, error):
        """Handle serial port errors.

        Args:
            error (QSerialPort.SerialPortError): The error code.
        """
        if error == QSerialPort.NoError:
            return
        logging.error(f"Serial port error: {self.serial.errorString()}")
        self.serial_port_error.emit(f"Serial port error: {self.serial.errorString()}")

    @Slot()
    def read_data(self):
        """Read data from the serial port and emit the received message."""
        while self.serial.canReadLine():
            data = self.serial.readLine().data().decode().strip()
            logging.info(f"{data}")

            # Emit the received message
            self.message_received.emit(data)

    @Slot(str)
    def send_message(self, message: str):
        """Send a message through the serial port."""
        if not self.serial.isOpen():
            logging.error("Cannot send message. Serial Port is closed.")

            return

        # Append newline if needed (depends on the receiving device)
        message_to_send = message + "\n"

        bytes_written = self.serial.write(message_to_send.encode())
        if bytes_written == -1:
            logging.error(f"Failed to write data: {self.serial.errorString()}")
        else:
            logging.info(f"{message}")

            # Emit the sent message (optional)
            self.message_sent.emit(message)


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
