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
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap

# ------------------------------------------------------------------------------
# PROJECT PACKAGES
# ------------------------------------------------------------------------------

# ==============================================================================
# CONSTANTS
# ==============================================================================


# ==============================================================================
# CLASSES
# ==============================================================================


class ScaledLabel(QLabel):
    """
    A QLabel subclass that scales its pixmap to fit the frame size while preserving aspect ratio.

    This class is useful for creating resizable QLabel instances where the displayed image is
    automatically resized along with the widget.

    Attributes:
        _pixmap (QPixmap): Stores the original pixmap to ensure it can be scaled correctly.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the ScaledLabel instance.

        Args:
            *args: Positional arguments passed to QLabel.
            **kwargs: Keyword arguments passed to QLabel.
        """
        super().__init__(*args, **kwargs)
        self._pixmap = self.pixmap()
        self._resised = False

    def resizeEvent(self, event) -> None:
        """
        Handles the widget's resize event to update the pixmap to the appropriate size.

        Args:
            event (QResizeEvent): The resize event.
        """
        self.setPixmap(self._pixmap)

    def setPixmap(self, pixmap: QPixmap) -> None:
        """
        Sets the pixmap for the label and scales it to fit the widget's size.

        Args:
            pixmap (QPixmap): The pixmap to be displayed in the label.
        """
        if not pixmap:
            return
        self._pixmap = pixmap
        return QLabel.setPixmap(
            self, self._pixmap.scaled(self.frameSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )


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
