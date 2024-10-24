"""
Implements message class

File: message.py
Author: @cvlt
Date: 2024-10-09
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
from enum import Enum, auto
from typing import Optional


# ------------------------------------------------------------------------------
# THIRD-PARTY PACKAGES
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# PROJECT PACKAGES
# ------------------------------------------------------------------------------

# ==============================================================================
# CONSTANTS
# ==============================================================================


# ==============================================================================
# Enumeratives
# ==============================================================================
class MessageType(Enum):
    """
    Enumeration of message types.
    """

    DISTANCE = auto()
    BATTERY = auto()
    DISCONNECTED = auto()
    OTHER = auto()


# ==============================================================================
# CLASSES
# ==============================================================================
class Message:
    """
    Message type to hold data for messages parsed from the serial port.

    Attributes:
        msg_type (MessageType): The message type.
        content (str): The message content.
        esl_id (Optional[str]): The ESL ID, formatted as a hexadecimal string.
        data (Optional[int]): The data value, such as distance or battery level.
    """

    def __init__(
        self,
        msg_type: MessageType,
        content: str,
        esl_id: Optional[str] = None,
        data: Optional[int] = None,
    ):
        """
        Initializes the Message with the given parameters. Parameters that are not passed and are not type or content, are set to None.

        Args:
            param1 (type1): Description of param1.
            param2 (type2): Description of param2.
        """
        self.msg_type = msg_type
        self.content = content
        self.esl_id = self._convert_esl_id(esl_id)
        self.data = data

    def __str__(self) -> str:
        """
        Returns a string representation of the Message.

        Returns:
            str: A string representing the Message instance.
        """

        components = [f"type[{self.msg_type.name}]"]

        if self.esl_id:
            components.append(f"esl_id[{self.esl_id}]")

        match self.msg_type:
            case MessageType.DISTANCE:
                components.append(f"distance[{self.data}] content[{self.content}]")
            case MessageType.BATTERY:
                components.append(f"battery[{self.data}] content[{self.content}]")
            case MessageType.DISCONNECTED:
                components.append(f"content[{self.content}]")
            case MessageType.OTHER:
                components.append(f"content[{self.content}]")

        return " ".join(components)

    def _convert_esl_id(self, esl_id: str) -> Optional[str]:
        """
        Converts the given ESL ID to a formatted hexadecimal string.

        Args:
            esl_id (str): The ESL ID as a string.

        Returns:
            Optional[str]: The formatted ESL ID as a 4-character hexadecimal string, or None if conversion fails.
        """
        try:
            return f"{int(esl_id, 16):04X}"
        except Exception as e:
            return None


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
