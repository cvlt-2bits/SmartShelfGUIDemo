"""
[Description of the module]

File: shelf.py
Author: @cvlt
Date: 2024-10-04
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
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PySide6.QtGui import QPixmap


# ------------------------------------------------------------------------------
# PROJECT PACKAGES
# ------------------------------------------------------------------------------
from src.message import Message, MessageType
from src.gui.components import ScaledLabel

# ==============================================================================
# CONSTANTS
# ==============================================================================


# ==============================================================================
# CLASSES
# ==============================================================================
class RailWidget(QFrame):
    """
    Custom widget that contains a progress bar on the left and a button above an item label on the right.
    """

    # Signals
    send_command = Signal(str)

    def __init__(
        self,
        rail_empty_distance: int,
        rail_full_distance: int,
        item_length: int,
        esl_id: str,
        mac_address: str,
        image_path: str,
        parent=None,
    ):
        super().__init__(parent)

        self.esl_id = esl_id  # Store ESL ID for this rail
        self.mac_address = mac_address

        self.rail_empty_distance = rail_empty_distance
        self.rail_full_distance = rail_full_distance
        self.item_length = item_length
        self.tolerance = int(0.25 * item_length)

        self.max_items = (rail_empty_distance - rail_full_distance) // item_length

        self.image_path = image_path

        self._setup_ui()
        self._setup_layout()
        self._setup_signals_qt()

    def _setup_ui(self) -> None:
        # Initialize UI Elements
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setOrientation(Qt.Vertical)
        self.progress_bar.setRange(0, self.max_items)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        # Button
        self.measure_button = QPushButton("Measure")

        self.item_label = ScaledLabel()
        self.item_label.setPixmap(QPixmap(self.image_path))
        # This will make sure the image is resized to fit its container
        self.item_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        add_shadow_effect(self.item_label, 10, 3, 3, QColor(0, 0, 0, 80))

        # Item Count Button (styled as label)
        # Write # to know we just initialized and no data received for rail yet
        self.item_count_button = QPushButton(f"#/{self.max_items}")
        self.item_count_button.setObjectName("item_count_label")
        self.item_count_button.setFlat(True)  # Remove button borders to make it look like a label

        add_shadow_effect(self, 15, 5, 5, QColor(0, 0, 0, 150))

    def _setup_layout(self) -> None:
        """Setup the layout of the RailWidget."""
        # Create the main vertical layout for the widget
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        # Top Layout containing the progress bar and the measure/item labels
        top_layout = QHBoxLayout()
        # Contains item, buttons, etc.
        item_layout = QVBoxLayout()

        # Add button and label to the item layout with specified stretch
        item_layout.addWidget(self.measure_button, stretch=10)
        item_layout.addWidget(self.item_label, stretch=90)

        # Add the progress bar to the right of the item layout
        top_layout.addWidget(self.progress_bar, stretch=20)
        top_layout.addLayout(item_layout, stretch=80)

        # Add everyting to the main layout
        main_layout.addLayout(top_layout, stretch=80)
        main_layout.addWidget(self.item_count_button, stretch=20)

    def _setup_signals_qt(self):
        # Measure button
        self.measure_button.clicked.connect(self.on_measure_button_clicked)
        # Item count label (connect)
        self.item_count_button.clicked.connect(self.on_item_count_label_clicked)

    def update_distance(self, distance: int):
        """
        Update the progress bar value based on the distance.
        """
        n_items = (self.rail_empty_distance - distance + self.tolerance) // self.item_length

        # Force 0 -> self.max_item range for values on progress bar and item count
        n_items = min(max(n_items, 0), self.max_items)

        self.progress_bar.setValue(n_items)
        self.item_count_button.setText(f"{n_items}/{self.max_items}")

    def update_connection_status(self, connected: bool):
        """
        Update the connection status of the RailWidget by setting opacity in the UI.
        """
        color = "#FFFFFF" if connected else "#D32F2F"
        self.item_count_button.setStyleSheet(f"""
            QPushButton#item_count_label {{
                color: {color};
            }}""")

    @Slot()
    def on_measure_button_clicked(self):
        """
        Slot that gets called when the measure button is clicked.
        Emits the command to measure.
        """
        command = f"esl_c force_measure {self.esl_id}"
        self.send_command.emit(command)

    @Slot()
    def on_item_count_label_clicked(self):
        """Emit a command when the item count label is clicked."""
        command = f"esl_c acl connect_addr 1 {self.mac_address}"
        self.send_command.emit(command)


class ShelfWidget(QFrame):
    """
    Custom widget that arranges RailWidgets in two rows:
    - Top Row: 7 RailWidgets
    - Bottom Row: 4 RailWidgets
    """

    TOP_ROW_ELEMENTS = 7
    BOTTOM_ROW_ELEMENTS = 4
    TOTAL_ELEMENTS = TOP_ROW_ELEMENTS + BOTTOM_ROW_ELEMENTS

    # Signal to emit measure commands from any RailWidget
    serial_command = Signal(str)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)

        esl_ids = config.get("ids", [])
        mac_addresses = config.get("mac_addresses", [])
        rails_empty_distance = config.get("rail_empty_distance", [])
        rails_full_distance = config.get("rail_full_distance", [])
        items_length = config.get("item_length", [])
        item_image_paths = config.get("image_path", [])

        if len(esl_ids) != (ShelfWidget.TOTAL_ELEMENTS):
            logging.warning(f"Expected 11 ESL IDs, got {len(esl_ids)}.")

        # Convert the parameters (ESL_ID to hex string, lengths to integers)
        esl_ids = [f"{int(id, 16):04X}" for id in esl_ids]
        rails_empty_distance = [int(length) for length in rails_empty_distance]
        rails_full_distance = [int(length) for length in rails_full_distance]
        items_length = [int(length) for length in items_length]

        self.setup_ui(esl_ids, mac_addresses, rails_empty_distance, rails_full_distance, items_length, item_image_paths)

    def setup_ui(
        self,
        esl_ids: list,
        mac_addresses: list,
        rails_empty_distance: list,
        rails_full_distance: list,
        items_length: list,
        item_image_paths: list,
    ) -> None:
        """Setup the shelf UI layout

        Args:
            esl_ids (list): List of ESL IDs
            mac_addresses (list): List of MAC addresses
            rails_empty_distance (list): List of empty distances
            rails_full_distance (list): List of full distances
            items_length (list): List of item lengths
            item_image_paths (list): List of item image paths
        """
        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        self.setLayout(main_layout)

        self.rails = {}

        # Top Row Layout
        top_row_layout = QHBoxLayout()
        top_row_layout.setSpacing(15)

        # Add rails to top row
        for index, id in enumerate(esl_ids[: ShelfWidget.TOP_ROW_ELEMENTS]):
            self.rails[id] = RailWidget(
                rails_empty_distance[index],
                rails_full_distance[index],
                items_length[index],
                id,
                mac_addresses[index],
                item_image_paths[index],
            )

            top_row_layout.addWidget(self.rails[id])

            # Connect the signal to the handler
            self.rails[id].send_command.connect(self.serial_command.emit)

        # Bottom Row Layout
        bottom_row_layout = QHBoxLayout()
        bottom_row_layout.setSpacing(15)

        # Add 4 RailWidgets to the bottom row
        for index, id in enumerate(esl_ids[ShelfWidget.TOP_ROW_ELEMENTS : ShelfWidget.TOTAL_ELEMENTS]):
            self.rails[id] = RailWidget(
                rails_empty_distance[index + ShelfWidget.TOP_ROW_ELEMENTS],
                rails_full_distance[index + ShelfWidget.TOP_ROW_ELEMENTS],
                items_length[index + ShelfWidget.TOP_ROW_ELEMENTS],
                id,
                mac_addresses[index + ShelfWidget.TOP_ROW_ELEMENTS],
                item_image_paths[index + ShelfWidget.TOP_ROW_ELEMENTS],
            )

            bottom_row_layout.addWidget(self.rails[id])

            # Connect the signal to the handler
            self.rails[id].send_command.connect(self.serial_command.emit)

        main_layout.addLayout(top_row_layout, stretch=40)
        main_layout.addLayout(bottom_row_layout, stretch=60)

        # Apply drop shadow effect to the ShelfWidget
        add_shadow_effect(self, 20, 8, 8, QColor(0, 0, 0, 100))

    def is_rail_valid(self, esl_id: int) -> bool:
        """
        Check if the given ESL ID is associated to one of the rails.

        Args:
            esl_id (int): The ESL ID to check.

        Returns:
            bool: True if the ID is valid, False otherwise.
        """
        return esl_id in self.rails

    @Slot(Message)
    def update_shelf(self, message: Message):
        """
        Update the shelf status based on the received message.

        Args:
            msg (Message): The message containing the shelf status.
        """
        # Check if the message has a message ID, if it has one check if it's associated to one of the rails, otherwise ignores the message
        if (message.esl_id is not None) and self.is_rail_valid(message.esl_id):
            rail = self.rails[message.esl_id]
            # Update the rails based on the message type
            match message.msg_type:
                case MessageType.DISTANCE:
                    rail.update_connection_status(True)
                    # Compute number of item
                    rail.update_distance(message.data)
                    # rail.update_distance(message.data)
                case MessageType.DISCONNECTED:
                    rail.update_connection_status(False)
                case MessageType.BATTERY:
                    rail.update_connection_status(True)
                case _:
                    pass
        elif message.esl_id is not None:
            logging.debug(f"ESL ID {message.esl_id} not on the shelf, ignoring.")


# ==============================================================================
# FUNCTIONS
# ==============================================================================
def add_shadow_effect(widget, blur_radius, x_offset, y_offset, color):
    """
    Utility function to add a shadow effect to a widget.

    Args:
        widget (QWidget): The widget to apply the shadow effect to.
        blur_radius (int): The blur radius of the shadow.
        x_offset (int): Horizontal offset for the shadow.
        y_offset (int): Vertical offset for the shadow.
        color (QColor): Color of the shadow.
    """
    shadow_effect = QGraphicsDropShadowEffect(widget)
    shadow_effect.setBlurRadius(blur_radius)
    shadow_effect.setXOffset(x_offset)
    shadow_effect.setYOffset(y_offset)
    shadow_effect.setColor(color)
    widget.setGraphicsEffect(shadow_effect)


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    """
    This block is executed only if the file is run as a script.
    If this file is imported as a module in another script, this block will not
    be executed.
    """
