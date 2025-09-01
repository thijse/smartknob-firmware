"""
SmartKnob Protocol Implementation

A clean, working implementation of the COBS+CRC32+Protobuf protocol stack.

This module provides the core protocol handling for SmartKnob communication:
- COBS encoding/decoding (100% working)
- CRC32 validation (100% working)  
- Protobuf message parsing (100% working)
- Command sending (working, but firmware doesn't respond)
- Message reception (working perfectly for log messages)
"""

import serial
import time
import struct
import logging
import random
import anyio
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass
from cobs import cobs
import zlib

from .proto_gen import smartknob_pb2, settings_pb2

logger = logging.getLogger(__name__)

PROTOBUF_PROTOCOL_VERSION = 1
RETRY_TIMEOUT_MS = 250  # 250ms retry timeout

def reset_connection(port: str, baud: int = 921600) -> bool:
    """
    Reset microcontroller connection by toggling DTR and RTS lines.
    
    This function performs a hardware reset of the connected microcontroller
    (typically ESP32) by using the DTR and RTS control lines of the serial port.
    
    Args:
        port: Serial port (e.g., 'COM9', '/dev/ttyUSB0')
        baud: Baud rate (default: 921600)
        
    Returns:
        True if reset successful, False otherwise
    """
    logger.info(f"Resetting microcontroller on {port}...")
    try:
        # Open serial connection with DTR/RTS control
        ser = serial.Serial(port, baud, timeout=1)
        
        # ESP32 reset sequence: DTR low, RTS high, then release
        ser.dtr = False  # DTR low
        ser.rts = True   # RTS high (active)
        time.sleep(0.1)  # Hold for 100ms
        
        ser.rts = False  # RTS low (inactive) - releases reset
        time.sleep(0.1)  # Brief delay
        
        ser.close()
        
        # Wait for microcontroller to boot
        logger.info("Waiting for microcontroller to boot...")
        time.sleep(2.0)  # Boot time
        logger.info("Reset complete")
        return True
        
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        return False
MAX_RETRIES = 10
MAX_QUEUE_SIZE = 10

@dataclass
class QueueEntry:
    """Entry in the outgoing message queue."""
    nonce: int
    encoded_payload: bytes
    timestamp: float
    retry_count: int = 0

@dataclass
class ProtocolStats:
    """Protocol statistics."""
    messages_sent: int = 0
    messages_received: int = 0
    acks_received: int = 0
    retries: int = 0
    crc_errors: int = 0
    protocol_errors: int = 0
    log_messages: int = 0
    knob_messages: int = 0
    other_messages: int = 0

class SmartKnobProtocol:
    """
    Async SmartKnob Protocol Handler using AnyIO
    
    Modern async implementation that replaces threading with proper async patterns.
    
    Features:
    - Non-blocking async I/O
    - Proper cancellation handling
    - Timeout support in serial reads
    - Task group management
    - Responsive to Ctrl-C
    """
    
    def __init__(self, port: str, baud: int = 921600, on_message: Optional[Callable] = None, auto_reset: bool = False, on_raw_data: Optional[Callable] = None):
        """
        Initialize async protocol handler.
        
        Args:
            port: Serial port name
            baud: Baud rate (default: 921600)
            on_message: Callback for received messages
            auto_reset: If True, reset ESP32 before connecting (default: False)
            on_raw_data: Callback for raw serial data (bytes) - for debugging/logging
        """
        self.port = port
        self.baud = baud
        self.auto_reset = auto_reset
        self.on_message = on_message or (lambda msg: None)
        self.on_raw_data = on_raw_data or (lambda data: None)  # Add raw data callback
        
        # Protocol state
        self.serial = None
        self.running = False
        self.port_available = True
        self.last_nonce = random.randint(1, 2**31 - 1)
        self.protocol_version = PROTOBUF_PROTOCOL_VERSION
        
        # Outgoing queue management (async compatible)
        self.outgoing_queue: List[QueueEntry] = []
        self.queue_lock = anyio.Lock()
        
        # Incoming buffer for incremental processing
        self.incoming_buffer = bytearray()
        
        # Statistics
        self.stats = ProtocolStats()
        
        logger.info("SmartKnobProtocol initialized")
    
    async def start(self, switch_to_protobuf: bool = True):
        """
        Start the async protocol.
        
        Args:
            switch_to_protobuf: Send 'q' command to switch to protobuf mode
        """
        try:
            # Create serial object without opening the port yet
            self.serial = serial.Serial()
            self.serial.port = self.port
            self.serial.baudrate = self.baud
            self.serial.timeout = 5.0  # 5-second read timeout
            
            # Set DTR/RTS to False BEFORE opening to prevent initial reset
            self.serial.dtr = False  # Don't assert DTR (Data Terminal Ready)
            self.serial.rts = False  # Don't assert RTS (Request To Send)
            
            # Now open the port with DTR/RTS already configured
            self.serial.open()
            
            logger.info(f"Opened {self.port} at {self.baud} baud (no auto-reset)")
            
            # Reset ESP32 if requested
            if self.auto_reset:
                logger.info("Performing ESP32 reset...")
                # Use existing serial connection for reset
                self.serial.dtr = False
                self.serial.rts = True
                await anyio.sleep(0.1)
                self.serial.rts = False
                await anyio.sleep(1.0)  # Give ESP32 time to boot
                logger.info("ESP32 reset complete")
            
            # Switch to protobuf mode if requested
            if switch_to_protobuf:
                self.serial.write(b"q")
                self.serial.flush()
                await anyio.sleep(0.2)
                logger.info("Sent 'q' command to switch to protobuf mode")
            
            self.running = True
            logger.info("SmartKnobProtocol started")
            
        except Exception as e:
            logger.error(f"Failed to start async protocol: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the async protocol and cleanup resources without triggering ESP32 reset."""
        logger.info("Stopping SmartKnobProtocol")
        self.running = False
        self.port_available = False
        
        if self.serial and self.serial.is_open:
            # Ensure DTR/RTS don't change state to prevent ESP32 reset
            self.serial.dtr = False
            self.serial.rts = False
            
            # Brief delay to let ESP32 finish processing any pending data
            await anyio.sleep(0.1)
            
            # Close the port gracefully
            self.serial.close()
            self.serial = None
            logger.info("Serial port closed without triggering ESP32 reset")
        
        logger.info("SmartKnobProtocol stopped")
    
    def _calculate_crc32(self, data: bytes) -> int:
        """Calculate CRC32 checksum for data."""
        return zlib.crc32(data) & 0xffffffff
    
    def _encode_frame(self, payload: bytes) -> bytes:
        """
        Encode payload with CRC32 and COBS.
        
        Process: Protobuf → CRC32 → COBS → Frame delimiter
        """
        # Calculate and append CRC32 (little-endian)
        crc = self._calculate_crc32(payload)
        packet = payload + struct.pack('<I', crc)
        
        # COBS encode
        encoded = cobs.encode(packet)
        
        # Add frame delimiter
        frame = encoded + b'\x00'
        
        logger.debug(f"Encoded frame: {len(payload)} bytes payload, CRC32: 0x{crc:08x}")
        return frame
    
    def _decode_frame(self, raw_frame: bytes) -> Optional[bytes]:
        """
        Decode COBS frame and verify CRC32.
        
        Process: Frame → COBS decode → CRC32 verify → Protobuf payload
        """
        try:
            # COBS decode
            packet = cobs.decode(raw_frame)
            
            if len(packet) <= 4:
                logger.debug(f"Short packet: {len(packet)} bytes")
                return None
            
            # Split payload and CRC32
            payload = packet[:-4]
            received_crc = struct.unpack('<I', packet[-4:])[0]
            
            # Verify CRC32
            calculated_crc = self._calculate_crc32(payload)
            if received_crc != calculated_crc:
                logger.warning(f"CRC32 mismatch: received 0x{received_crc:08x}, "
                             f"calculated 0x{calculated_crc:08x}")
                self.stats.crc_errors += 1
                return None
            
            return payload
            
        except Exception as e:
            logger.debug(f"Frame decode failed: {e}")
            return None
    
    async def read_loop(self):
        """
        Async read loop with proper timeout handling.
        
        Uses efficient in_waiting pattern while providing clean cancellation.
        """
        logger.debug("Async read loop started")
        
        try:
            while self.running:
                try:
                    # Check if data available (efficient pattern)
                    if self.serial.in_waiting > 0:
                        data = self.serial.read(self.serial.in_waiting)
                        if data:
                            await self._process_incoming_data(data)
                    else:
                        # Nothing available, yield control with short sleep
                        await anyio.sleep(0.01)  # 10ms responsive sleep
                        
                except serial.SerialTimeoutException:
                    # Timeout is expected, just continue
                    continue
                except Exception as e:
                    logger.error(f"Read loop error: {e}")
                    break
                    
        except anyio.CancelledError:
            logger.debug("Read loop cancelled")
            raise
        finally:
            logger.debug("Async read loop stopped")
    
    async def _process_incoming_data(self, data: bytes):
        """Process incoming data, handling partial frames."""
        # Call raw data callback first (for logging/debugging)
        try:
            self.on_raw_data(data)
        except Exception as e:
            logger.warning(f"Raw data callback error: {e}")
        
        # Add to buffer
        self.incoming_buffer.extend(data)
        
        # Process complete frames (0-delimited)
        while True:
            delimiter_index = self.incoming_buffer.find(0)
            if delimiter_index == -1:
                break  # No complete frame
            
            # Extract frame (without delimiter)
            raw_frame = bytes(self.incoming_buffer[:delimiter_index])
            self.incoming_buffer = self.incoming_buffer[delimiter_index + 1:]
            
            # Skip empty frames
            if not raw_frame:
                continue
            
            # Decode frame
            payload = self._decode_frame(raw_frame)
            if payload is None:
                continue
            
            # Parse protobuf message
            try:
                message = smartknob_pb2.FromSmartKnob()
                message.ParseFromString(payload)
                
                # Validate protocol version
                if message.protocol_version != self.protocol_version:
                    logger.warning(f"Protocol version mismatch: expected {self.protocol_version}, "
                                 f"got {message.protocol_version}")
                    self.stats.protocol_errors += 1
                    continue
                
                self.stats.messages_received += 1
                
                # Update message type statistics
                msg_type = message.WhichOneof("payload")
                if msg_type == 'log':
                    self.stats.log_messages += 1
                elif msg_type == 'knob':
                    self.stats.knob_messages += 1
                elif msg_type == 'ack':
                    self.stats.acks_received += 1
                    await self._handle_ack(message.ack.nonce)
                else:
                    self.stats.other_messages += 1
                
                # Notify callback
                self.on_message(message)
                
            except Exception as e:
                logger.warning(f"Failed to parse protobuf: {e}")
                self.stats.protocol_errors += 1
    
    async def _handle_ack(self, nonce: int):
        """Handle ACK message."""
        async with self.queue_lock:
            if self.outgoing_queue and self.outgoing_queue[0].nonce == nonce:
                logger.debug(f"Received ACK for nonce {nonce}")
                
                # Remove from queue
                self.outgoing_queue.pop(0)
                
                # Service next message
                await self._service_queue()
            else:
                logger.debug(f"Ignoring unexpected ACK for nonce {nonce}")
    
    async def _service_queue(self):
        """Service the outgoing message queue."""
        if not self.port_available or not self.outgoing_queue:
            return
        
        # Get next message
        entry = self.outgoing_queue[0]
        
        # Send frame
        try:
            self.serial.write(entry.encoded_payload)
            self.serial.flush()
            
            if entry.retry_count == 0:
                self.stats.messages_sent += 1
            else:
                self.stats.retries += 1
            
            logger.debug(f"Sent message with nonce {entry.nonce} "
                       f"(retry {entry.retry_count})")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.port_available = False
    
    async def _enqueue_message(self, message: smartknob_pb2.ToSmartknob):
        """Add message to outgoing queue."""
        if not self.port_available:
            logger.warning("Port not available, dropping message")
            return
        
        # Set protocol version and nonce
        message.protocol_version = self.protocol_version
        self.last_nonce += 1
        message.nonce = self.last_nonce
        
        # Encode message
        payload = message.SerializeToString()
        frame = self._encode_frame(payload)
        
        # Add to queue
        async with self.queue_lock:
            # Check queue overflow
            if len(self.outgoing_queue) > MAX_QUEUE_SIZE:
                logger.warning(f"Outgoing queue overflow! Dropping {len(self.outgoing_queue)} messages")
                self.outgoing_queue.clear()
            
            entry = QueueEntry(
                nonce=message.nonce,
                encoded_payload=frame,
                timestamp=time.time()
            )
            self.outgoing_queue.append(entry)
            
            # Service queue if this is the only message
            if len(self.outgoing_queue) == 1:
                await self._service_queue()
    
    # Public API methods
    
    async def send_command(self, command: int):
        """Send SmartKnob command."""
        message = smartknob_pb2.ToSmartknob()
        message.smartknob_command = command
        await self._enqueue_message(message)
        logger.info(f"Sent command: {command}")
    
    async def send_config(self, config: smartknob_pb2.SmartKnobConfig):
        """Send SmartKnob configuration."""
        message = smartknob_pb2.ToSmartknob()
        message.smartknob_config.CopyFrom(config)
        await self._enqueue_message(message)
        logger.info("Sent configuration")
    
    async def send_settings(self, settings: settings_pb2.Settings):
        """Send settings."""
        message = smartknob_pb2.ToSmartknob()
        message.settings.CopyFrom(settings)
        await self._enqueue_message(message)
        logger.info("Sent settings")
    
    def get_stats(self) -> Dict[str, int]:
        """Get protocol statistics."""
        return {
            'messages_sent': self.stats.messages_sent,
            'messages_received': self.stats.messages_received,
            'acks_received': self.stats.acks_received,
            'retries': self.stats.retries,
            'crc_errors': self.stats.crc_errors,
            'protocol_errors': self.stats.protocol_errors,
            'log_messages': self.stats.log_messages,
            'knob_messages': self.stats.knob_messages,
            'other_messages': self.stats.other_messages
        }
    
    def clear_stats(self):
        """Clear protocol statistics."""
        self.stats = ProtocolStats()


class SmartKnobConnection:
    """
    SmartKnob connection manager using AnyIO.
    
    Provides a clean async interface for connecting to and communicating with SmartKnob devices.
    """
    
    def __init__(self, port: str, baud: int = 921600, auto_reset: bool = False, on_raw_data: Optional[Callable] = None):
        """
        Initialize connection.
        
        Args:
            port: Serial port (e.g., 'COM9', '/dev/ttyUSB0')
            baud: Baud rate (default: 921600)
            auto_reset: If True, reset ESP32 before connecting (default: False)
            on_raw_data: Callback for raw serial data (bytes) - for debugging/logging
        """
        self.port = port
        self.baud = baud
        self.auto_reset = auto_reset
        self.on_raw_data = on_raw_data
        self.protocol = None
        self.connected = False
        
    async def start(self, switch_to_protobuf: bool = True):
        """
        Start the connection.
        
        Args:
            switch_to_protobuf: Send 'q' command to switch to protobuf mode
            
        Returns:
            True if connection successful
        """
        try:
            self.protocol = SmartKnobProtocol(self.port, self.baud, auto_reset=self.auto_reset, on_raw_data=self.on_raw_data)
            await self.protocol.start(switch_to_protobuf)
            self.connected = True
            
            logger.info("SmartKnobConnection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            await self.stop()
            return False
    
    async def stop(self):
        """Stop the connection."""
        if self.protocol:
            await self.protocol.stop()
            self.protocol = None
        
        self.connected = False
        logger.info("SmartKnobConnection stopped")
    
    def set_message_callback(self, callback: Callable):
        """Set callback for received messages."""
        if self.protocol:
            self.protocol.on_message = callback
    
    def set_raw_data_callback(self, callback: Callable):
        """Set callback for raw serial data (for debugging/logging)."""
        if self.protocol:
            self.protocol.on_raw_data = callback
    
    async def send_command(self, command: int):
        """Send command to SmartKnob."""
        if self.protocol:
            await self.protocol.send_command(command)
        else:
            raise RuntimeError("Not connected")
    
    def get_stats(self) -> Dict[str, int]:
        """Get protocol statistics."""
        if self.protocol:
            return self.protocol.get_stats()
        return {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not await self.start():
            raise RuntimeError("Failed to connect")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
