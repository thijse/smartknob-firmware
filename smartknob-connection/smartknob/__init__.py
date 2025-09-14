"""
SmartKnob Connection Library

A clean, working implementation of the SmartKnob COBS+CRC32+Protobuf protocol.

This library provides:
- Complete protocol stack implementation (COBS encoding, CRC32 validation, Protobuf parsing)
- Reliable message reception from SmartKnob device
- Command sending capabilities
- Connection management utilities

Status:
- ✅ Protocol stack: 100% working (COBS+CRC32+Protobuf)
- ✅ Message reception: Log messages received perfectly
- ✅ Command sending: Commands sent correctly
- ❌ Command responses: Firmware doesn't respond to commands (needs investigation)
"""

from .protocol import SmartKnobProtocol, SmartKnobConnection
from .connection import connect_smartknob, find_smartknob_ports

__version__ = "1.0.0"
__all__ = ["SmartKnobProtocol", "SmartKnobConnection", "connect_smartknob", "find_smartknob_ports"]
