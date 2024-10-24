"""
[Description of the module]

File: parser.py
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
import re
from typing import Optional

# ------------------------------------------------------------------------------
# THIRD-PARTY PACKAGES
# ------------------------------------------------------------------------------
from PySide6.QtCore import QObject, Signal, Slot

# ------------------------------------------------------------------------------
# PROJECT PACKAGES
# ------------------------------------------------------------------------------
# fmt: off
from src.message import Message, MessageType  # noqa: E402

# fmt: on

# ==============================================================================
# CONSTANTS
# ==============================================================================


# ==============================================================================
# CLASSES
# ==============================================================================
class Parser(QObject):
    """
    Parses messages received from the SerialHandler and emits processed messages.
    """

    # Signal emitted after parsing a message
    message_parsed = Signal(Message)

    def __init__(self):
        super().__init__()

    def parse_message_fields(msg: str) -> Optional[Message]:
        """
        Parse message fields delimited by []. Returns a Message object.

        Args:
            msg (str): The msg to parse.

        Returns:
            Message: The corresponding Message object.
        """
        try:
            # Extract fields encased in [ ]
            fields = re.findall(r"\[([^\]]*)\]", msg[1:])

            first_field = fields[0].split(":")
            if first_field[0].upper() == "ESL_ID":
                esl_id = first_field[1].strip()

                # Take second field, ignore other fields for now
                second_field = fields[1].split(":")
                match second_field[0].strip().upper():
                    case "DISTANCE":
                        return Message(MessageType.DISTANCE, msg, esl_id, int(second_field[1].strip()))
                    case "BATTERY":
                        return Message(MessageType.BATTERY, msg, esl_id, int(second_field[1].strip()))
                    case "TAG DISCONNECTED":
                        return Message(MessageType.DISCONNECTED, msg, esl_id)
                    case _:
                        return Message(MessageType.OTHER, msg)
            else:
                return Message(MessageType.OTHER, msg)
        except Exception as e:
            logging.error(f"Error parsing message: {e}")
            return None

    @Slot(str)
    def parse_message(self, message: str) -> None:
        """
        Parses the incoming message and emits it.

        Args:
            message (str): The raw message received from SerialHandler.
        """
        # logging.debug(f"Parser received message: {message}")

        parsed_message = message.strip()
        if parsed_message.startswith("#"):
            # Pass the message for parsing without the initial character
            out = Parser.parse_message_fields(parsed_message)
        else:
            out = Message(MessageType.OTHER, message)

        # For now, we simply emit the same message
        self.message_parsed.emit(out)
        # logging.debug(f"Parser emitted parsed message: {parsed_message}")


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
