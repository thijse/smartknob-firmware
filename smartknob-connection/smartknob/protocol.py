"""
SmartKnob Protocol Implementation

A clean, working implementation of the COBS+CRC32+Protobuf protocol stack.

This module provides the core protocol handling for SmartKnob communication:
- COBS encoding/decoding (100% working)
- CRC32 validation (100% working)  
- Protobuf message parsing (100% working)
- Command sending (working, but firmware doesn't respond)
- Message reception (working perfectly for log messages)

ESP32 RESET BEHAVIOR (Experimentally Determined):
================================================
Through interactive testing, we discovered these ESP32 reset patterns:

1. OPENING RULES:
   - Reset occurs ONLY on FIRST connection after ESP32 idle period
   - Requires DTR/RTS=True (default serial behavior)  
   - Subsequent opens do NOT reset (ESP32 has "reset immunity")

2. CLOSING RULES:
   - Reset occurs ONLY if DTR/RTS were True DURING open() call
   - Changing DTR/RTS after open() has NO effect on close behavior
   - Reset behavior is "captured" at open() time

3. PRACTICAL IMPLICATIONS:
   - reset_at_close parameter must be set BEFORE start()
   - ResetAtClose() method only affects FUTURE connections
   - Standalone reset works reliably (ESP32 is idle)
   - Reset while connected may not work (insufficient idle time)
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
    Reset microcontroller by opening/closing serial with reset enabled.
    Simple and reliable - just let the default DTR/RTS behavior work.
    
    OBSERVED ESP32 RESET BEHAVIOR RULES:
    ====================================
    1. OPENING: Reset occurs ONLY on the FIRST connection after ESP32 has been 
       idle/disconnected, AND ONLY if DTR/RTS are True (default). Subsequent 
       opens will NOT reset regardless of DTR/RTS settings.
       
    2. CLOSING: Reset occurs ONLY if DTR/RTS were set to True DURING the open() 
       call. Changing DTR/RTS after connection is open has NO effect on close.
       
    3. RESET IMMUNITY: ESP32 becomes "immune" to resets after first connection 
       until it's been idle for sufficient time.
       
    4. STATE CAPTURE: DTR/RTS reset behavior is "captured" during open() - 
       subsequent changes don't affect close behavior.
    
    Args:
        port: Serial port (e.g., 'COM9', '/dev/ttyUSB0')
        baud: Baud rate (default: 921600)
        
    Returns:
        True if reset successful, False otherwise
    """
    logger.info(f"Resetting microcontroller on {port}...")
    try:
        # Open with default DTR/RTS behavior (allows reset)
        ser = serial.Serial(port, baud, timeout=1)
        # Reset happens automatically on open due to DTR/RTS
        time.sleep(0.1)  # Brief hold
        ser.close()  # Reset happens on close too
        
        # Wait for boot
        logger.info("Waiting for microcontroller to boot...")
        time.sleep(2.0)
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
    
    def __init__(self, port: str, baud: int = 921600, on_message: Optional[Callable] = None, reset_at_close: bool = False, on_raw_data: Optional[Callable] = None):
        """
        Initialize async protocol handler.
        
        IMPORTANT: reset_at_close must be set BEFORE calling start() because
        ESP32 reset behavior is determined during open(), not close().
        
        Args:
            port: Serial port name
            baud: Baud rate (default: 921600)
            on_message: Callback for received messages
            reset_at_close: If True, reset ESP32 when connection closes (default: False)
                          NOTE: This sets DTR/RTS during open() - changes after open() are ignored
            on_raw_data: Callback for raw serial data (bytes) - for debugging/logging
        """
        self.port = port
        self.baud = baud
        self.reset_at_close = reset_at_close
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
        
        logger.info(f"SmartKnobProtocol initialized with reset_at_close={self.reset_at_close}")
    
    async def start(self, switch_to_protobuf: bool = True):
        """
        Start the async protocol.
        
        CRITICAL: The reset_at_close behavior is determined HERE during open().
        ESP32 reset behavior cannot be changed after connection is established.
        
        Args:
            switch_to_protobuf: Send 'q' command to switch to protobuf mode
        """
        try:
            # Create and configure serial
            self.serial = serial.Serial()
            self.serial.port = self.port
            self.serial.baudrate = self.baud
            self.serial.timeout = 5.0
            
            # Simple reset control based on our findings
            if not self.reset_at_close:
                # Prevent reset: Set DTR/RTS to False
                self.serial.dtr = False
                self.serial.rts = False
                logger.info("Opening with reset prevention (DTR/RTS=False)")
            else:
                # Allow reset: Use default behavior (DTR/RTS=True)
                logger.info("Opening with reset enabled (default DTR/RTS)")
            
            # Open port
            self.serial.open()
            logger.info(f"Opened {self.port} at {self.baud} baud")
            
            # Switch to protobuf if requested
            if switch_to_protobuf:
                self.serial.write(b"q")
                self.serial.flush()
                await anyio.sleep(0.2)
                logger.info("Switched to protobuf mode")
            
            self.running = True
            logger.info("SmartKnobProtocol started")
            
        except Exception as e:
            logger.error(f"Failed to start async protocol: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop protocol with optional reset on close."""
        logger.info("Stopping SmartKnobProtocol")
        self.running = False
        self.port_available = False
        
        if self.serial and self.serial.is_open:
            if not self.reset_at_close:
                # Ensure no reset on close
                self.serial.dtr = False
                self.serial.rts = False
                logger.info("Closing without reset (DTR/RTS=False)")
            else:
                logger.info("Closing with reset enabled")
            
            # Brief delay to let ESP32 finish processing any pending data
            await anyio.sleep(0.1)
            
            self.serial.close()
            self.serial = None
            logger.info("Serial port closed")
        
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
                # logger.warning(f"CRC32 mismatch: received 0x{received_crc:08x}, "
                #              f"calculated 0x{calculated_crc:08x}")
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
    
    async def flush_receive_buffer(self):
        """
        Attempt to flush receive buffer by sending garbage terminator.
        
        Theory: Send 0x00 to force PacketSerial to process corrupted buffer,
        fail COBS decode, discard it, and reset to clean state.
        
        Returns:
            True if flush was sent successfully, False otherwise
        """
        if not self.serial or not self.serial.is_open:
            logger.warning("Cannot flush buffer - serial not open")
            return False
        
        try:
            logger.info("Flushing receive buffer with single terminator (0x00)")
            
            # Send a lone 0x00 byte (COBS frame terminator)
            # This should force PacketSerial to process corrupted buffer and discard it
            self.serial.write(b'\x00')
            self.serial.flush()
            
            # Wait briefly for firmware to process
            await anyio.sleep(0.05)
            
            logger.info("Buffer flush sent")
            return True
            
        except Exception as e:
            logger.error(f"Buffer flush failed: {e}")
            return False
    
    async def send_command(self, command: int) -> int:
        """Send SmartKnob command.

        Returns the nonce assigned to the message for optional ACK correlation.
        """
        message = smartknob_pb2.ToSmartknob()
        message.smartknob_command = command
        await self._enqueue_message(message)
        logger.info(f"Sent command: {command}")
        return message.nonce
    
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


    async def send_app_component(self, app_component: smartknob_pb2.AppComponent) -> int:
        """
        Public helper to send an AppComponent payload.
        Returns the nonce assigned to the message for optional ACK correlation.
        """
        message = smartknob_pb2.ToSmartknob()
        message.app_component.CopyFrom(app_component)
        await self._enqueue_message(message)
        return message.nonce

    async def send_multi_choice(
        self,
        component_id: str,
        title: str,
        options: List[str],
        initial_index: int = 0,
        wrap_around: bool = True,
        detent_strength_unit: float = 1.5,
        endstop_strength_unit: float = 1.5,
        led_hue: int = 200,
    ) -> int:
        """
        Compose and send a MULTI_CHOICE app component payload.
        Returns the nonce assigned to the message for optional ACK correlation.
        """
        app_component = smartknob_pb2.AppComponent()
        app_component.component_id = component_id
        # NOTE: Keep numeric literal for compatibility with current proto usage in examples
        # MULTI_CHOICE = 2
        app_component.type = 2
        app_component.display_name = title

        mc = app_component.multi_choice
        # Fresh message, but be explicit for clarity
        del mc.options[:]
        for opt in options or []:
            mc.options.append(str(opt))

        mc.initial_index = int(initial_index)
        mc.wrap_around = bool(wrap_around)
        mc.detent_strength_unit = float(detent_strength_unit)
        mc.endstop_strength_unit = float(endstop_strength_unit)
        mc.led_hue = int(led_hue)

        return await self.send_app_component(app_component)

    async def send_toggle(
        self,
        component_id: str,
        title: str,
        off_label: str = "Off",
        on_label: str = "On",
        initial_state: bool = False,
        snap_point: float = 0.5,
        snap_point_bias: float = 0.0,
        detent_strength_unit: float = 4.0,
        off_led_hue: int = 0,
        on_led_hue: int = 120,
    ) -> int:
        """
        Compose and send a TOGGLE app component payload.
        Returns the nonce assigned to the message for optional ACK correlation.
        """
        app_component = smartknob_pb2.AppComponent()
        app_component.component_id = component_id
        # TOGGLE = 0
        app_component.type = 0
        app_component.display_name = title

        t = app_component.toggle
        t.off_label = str(off_label)
        t.on_label = str(on_label)
        t.initial_state = bool(initial_state)
        t.snap_point = float(snap_point)
        t.snap_point_bias = float(snap_point_bias)
        t.detent_strength_unit = float(detent_strength_unit)
        t.off_led_hue = int(off_led_hue)
        t.on_led_hue = int(on_led_hue)

        return await self.send_app_component(app_component)

    async def send_app_select(self, *, by_id: Optional[int] = None, by_app_id: Optional[str] = None) -> int:
        """
        Compose and send an AppSelect message to switch the active app.
        Exactly one selector must be provided: by_id or by_app_id.
        Enforces app_id length ≤ 32. Returns the assigned nonce.
        """
        # Validate selector
        if (by_id is None and by_app_id is None) or (by_id is not None and by_app_id is not None):
            raise ValueError("Provide exactly one of by_id or by_app_id")

        message = smartknob_pb2.ToSmartknob()
        sel = smartknob_pb2.AppSelect()
        if by_id is not None:
            if int(by_id) < 0:
                raise ValueError("by_id must be a non-negative integer")
            sel.by_id = int(by_id)
            log_desc = f"by_id={sel.by_id}"
        else:
            app_id = str(by_app_id)
            if len(app_id) > 32:
                raise ValueError("app_id must be ≤ 32 characters")
            sel.by_app_id = app_id
            log_desc = f"by_app_id='{sel.by_app_id}'"

        message.app_select.CopyFrom(sel)
        await self._enqueue_message(message)
        logger.info(f"Sent app_select ({log_desc})")
        return message.nonce

    async def _send_frame_immediate(self, message: smartknob_pb2.ToSmartknob) -> int:
        """
        Fire-and-forget send that bypasses the queue and does not wait for ACK.
        Use for single-shot messages (e.g., request_state) to avoid queue head-of-line blocking.
        Returns the nonce assigned.
        """
        if not self.serial:
            raise RuntimeError("Serial not open")
        # Stamp protocol and nonce
        message.protocol_version = self.protocol_version
        self.last_nonce += 1
        message.nonce = self.last_nonce
        # Encode and write
        payload = message.SerializeToString()
        frame = self._encode_frame(payload)
        try:
            self.serial.write(frame)
            self.serial.flush()
            self.stats.messages_sent += 1
            logger.debug(f"Sent immediate (no-queue) message nonce={message.nonce}")
        except Exception as e:
            logger.error(f"Immediate send failed: {e}")
            self.port_available = False
        return message.nonce

    async def send_request_state_immediate(self) -> int:
        """
        Send a ToSmartknob.request_state as an immediate (no-queue) frame.
        Returns the assigned nonce.
        """
        m = smartknob_pb2.ToSmartknob()
        m.request_state.SetInParent()
        return await self._send_frame_immediate(m)

    async def send_app_select_immediate(self, *, by_id: Optional[int] = None, by_app_id: Optional[str] = None) -> int:
        """
        Send AppSelect as an immediate (no-queue) frame. Exactly one selector required.
        """
        if (by_id is None and by_app_id is None) or (by_id is not None and by_app_id is not None):
            raise ValueError("Provide exactly one of by_id or by_app_id")
        m = smartknob_pb2.ToSmartknob()
        sel = smartknob_pb2.AppSelect()
        if by_id is not None:
            if int(by_id) < 0:
                raise ValueError("by_id must be a non-negative integer")
            sel.by_id = int(by_id)
            log_desc = f"by_id={sel.by_id}"
        else:
            app_id = str(by_app_id)
            if len(app_id) > 32:
                raise ValueError("app_id must be ≤ 32 characters")
            sel.by_app_id = app_id
            log_desc = f"by_app_id='{sel.by_app_id}'"
        m.app_select.CopyFrom(sel)
        nonce = await self._send_frame_immediate(m)
        logger.info(f"Sent app_select immediate ({log_desc})")
        return nonce
class SmartKnobConnection:
    """
    SmartKnob connection manager using AnyIO.
    
    Provides a clean async interface for connecting to and communicating with SmartKnob devices.
    """
    
    def __init__(self, port: str, baud: int = 921600, reset_at_close: bool = False, on_raw_data: Optional[Callable] = None):
        """
        Initialize connection.
        
        Args:
            port: Serial port (e.g., 'COM9', '/dev/ttyUSB0')
            baud: Baud rate (default: 921600)
            reset_at_close: If True, reset ESP32 when connection closes (default: False)
            on_raw_data: Callback for raw serial data (bytes) - for debugging/logging
        """
        self.port = port
        self.baud = baud
        self.reset_at_close = reset_at_close
        self.on_raw_data = on_raw_data
        self.protocol = None
        self.connected = False
        
        # App event callbacks
        self._cb_value_selected: Optional[Callable[[int, float], None]] = None
        self._cb_button_pressed: Optional[Callable[[int], None]] = None
        self._last_position: Optional[int] = None
        self._last_press_nonce: int = -1
        
        # User's message callback (to be wrapped)
        self._user_message_callback: Optional[Callable] = None
        
    async def start(self, switch_to_protobuf: bool = True):
        """
        Start the connection.
        
        Args:
            switch_to_protobuf: Send 'q' command to switch to protobuf mode
            
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Creating SmartKnobProtocol with reset_at_close={self.reset_at_close}")
            self.protocol = SmartKnobProtocol(self.port, self.baud, reset_at_close=self.reset_at_close, on_raw_data=self.on_raw_data)
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
        """
        Set callback for received messages.
        
        The callback is automatically wrapped to process app events (value changes, button presses)
        before calling the user's callback.
        """
        if self.protocol:
            # Store user callback
            self._user_message_callback = callback
            
            # Create wrapper that processes app events first
            def wrapped_callback(message):
                # Process app events first
                msg_type = message.WhichOneof("payload")
                if msg_type == "smartknob_state":
                    self._handle_smartknob_state(message.smartknob_state)
                
                # Then call user callback if provided
                if self._user_message_callback:
                    self._user_message_callback(message)
            
            self.protocol.on_message = wrapped_callback
    
    def set_raw_data_callback(self, callback: Callable):
        """Set callback for raw serial data (for debugging/logging)."""
        if self.protocol:
            self.protocol.on_raw_data = callback
    
    async def flush_receive_buffer(self):
        """
        Flush receive buffer before sending next command.
        
        Sends a single 0x00 terminator to force PacketSerial to process
        and discard any corrupted data in the buffer.
        
        Returns:
            True if flush was successful, False otherwise
        """
        if self.protocol:
            return await self.protocol.flush_receive_buffer()
        return False
    
    def on_value_selected(self, callback: Callable[[int, float], None]) -> "SmartKnobConnection":
        """
        Register callback for knob position changes.
        
        The callback is invoked whenever the knob position changes, providing
        the current position and sub-position for fine-grained tracking.
        
        Args:
            callback: Function(position: int, sub_position: float) called when value changes
        
        Returns:
            Self for method chaining
        
        Example:
            conn.on_value_selected(lambda pos, sub: print(f"Position: {pos}, sub: {sub:.3f}"))
        """
        self._cb_value_selected = callback
        return self
    
    def on_button_pressed(self, callback: Callable[[int], None]) -> "SmartKnobConnection":
        """
        Register callback for button presses.
        
        The callback is invoked whenever the knob is pressed, providing the
        position at which the press occurred.
        
        Args:
            callback: Function(position: int) called when button is pressed
        
        Returns:
            Self for method chaining
        
        Example:
            conn.on_button_pressed(lambda pos: print(f"Button pressed at: {pos}"))
        """
        self._cb_button_pressed = callback
        return self
    
    def _handle_smartknob_state(self, state):
        """
        Internal handler for smartknob_state messages.
        
        Processes state changes and triggers registered callbacks for:
        - Value changes (position changed)
        - Button presses (press_nonce changed)
        """
        try:
            # Extract position
            current_position = int(getattr(state, "current_position", 0))
            sub_position = float(getattr(state, "sub_position_unit", 0.0))
            
            # Value selected event (position changed)
            if self._cb_value_selected and (self._last_position is None or current_position != self._last_position):
                self._last_position = current_position
                try:
                    self._cb_value_selected(current_position, sub_position)
                except Exception as e:
                    logger.warning(f"Error in value_selected callback: {e}")
            
            # Button pressed event (press_nonce changed)
            press_nonce = int(getattr(state, "press_nonce", -1))
            if self._cb_button_pressed and press_nonce >= 0 and press_nonce != self._last_press_nonce:
                self._last_press_nonce = press_nonce
                try:
                    self._cb_button_pressed(current_position)
                except Exception as e:
                    logger.warning(f"Error in button_pressed callback: {e}")
                    
        except Exception as e:
            logger.warning(f"Error handling smartknob_state: {e}")
    
    def ResetAtClose(self, enable: bool):
        """
        ResetAtClose(bool) - sets reset behavior persistently.
        
        IMPORTANT LIMITATION: Due to ESP32 behavior, this only takes effect 
        for NEW connections. Changing this on an existing connection will NOT 
        affect the current connection's close behavior because ESP32 reset 
        behavior is determined during open(), not close().
        
        Args:
            enable: If True, device will reset when FUTURE connections close
        """
        self.reset_at_close = enable
        if self.protocol:
            self.protocol.reset_at_close = enable
        logger.info(f"Reset at close {'enabled' if enable else 'disabled'} (takes effect on next connection)")
    
    async def send_command(self, command: int):
        """Send command to SmartKnob."""
        if self.protocol:
            await self.protocol.send_command(command)
        else:
            raise RuntimeError("Not connected")
    
    async def send_config(self, config):
        """Send configuration to SmartKnob."""
        if self.protocol:
            await self.protocol.send_config(config)
        else:
            raise RuntimeError("Not connected")
    
    async def send_settings(self, settings):
        """Send settings to SmartKnob."""
        if self.protocol:
            await self.protocol.send_settings(settings)
        else:
            raise RuntimeError("Not connected")
    
    async def send_app_component(self, app_component):
        """Send app component to SmartKnob."""
        if self.protocol:
            return await self.protocol.send_app_component(app_component)
        else:
            raise RuntimeError("Not connected")
    
    async def send_component(self, component):
        """Send component to SmartKnob (alias for send_app_component)."""
        return await self.send_app_component(component)
    
    async def send_multi_choice(self, *args, **kwargs):
        """Send multi choice component to SmartKnob."""
        if self.protocol:
            return await self.protocol.send_multi_choice(*args, **kwargs)
        else:
            raise RuntimeError("Not connected")
    
    async def send_toggle(self, *args, **kwargs):
        """Send toggle component to SmartKnob."""
        if self.protocol:
            return await self.protocol.send_toggle(*args, **kwargs)
        else:
            raise RuntimeError("Not connected")
    
    async def send_app_select(self, *, by_id: Optional[int] = None, by_app_id: Optional[str] = None, flush_before: bool = True):
        """
        Select app by id or app_id with optional buffer flush.
        
        Args:
            by_id: Select app by numeric ID (0-255)
            by_app_id: Select app by string identifier (max 32 chars)
            flush_before: Send 0x00 terminator first to clear buffer corruption (default: True)
                         This works around a known buffer corruption issue during connection init.
                         
        Returns:
            Nonce of the sent message
            
        Note:
            The flush_before workaround adds ~50ms overhead but ensures reliable packet delivery.
            This is a temporary solution until the root cause of buffer corruption is fixed.
        """
        if flush_before:
            await self.flush_receive_buffer()
        
        if self.protocol:
            return await self.protocol.send_app_select(by_id=by_id, by_app_id=by_app_id)
        else:
            raise RuntimeError("Not connected")

    async def send_request_state_immediate(self):
        """Send request_state as an immediate (no-queue) frame."""
        if self.protocol:
            return await self.protocol.send_request_state_immediate()
        else:
            raise RuntimeError("Not connected")

    async def send_app_select_immediate(self, *, by_id: Optional[int] = None, by_app_id: Optional[str] = None):
        """Select app immediate (no-queue) by id or app_id."""
        if self.protocol:
            return await self.protocol.send_app_select_immediate(by_id=by_id, by_app_id=by_app_id)
        else:
            raise RuntimeError("Not connected")
    
    def get_stats(self) -> Dict[str, int]:
        """Get protocol statistics."""
        if self.protocol:
            return self.protocol.get_stats()
        return {}
    
    async def start_read_loop(self):
        """Start the protocol read loop. Call this within a task group."""
        if self.protocol:
            await self.protocol.read_loop()
        else:
            raise RuntimeError("Not connected")
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not await self.start():
            raise RuntimeError("Failed to connect")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def reset_device(self) -> bool:
        """
        Reset device using simple, reliable method.
        
        RESET BEHAVIOR EXPLAINED:
        ========================
        - Scenario 1 (No connection): Uses standalone reset - RELIABLE
        - Scenario 2 (Connected): Disconnect + reconnect with reset enabled
          
        NOTE: Due to ESP32 "reset immunity" after first connection, the 
        "reset while connected" scenario may not always trigger actual reset
        unless sufficient idle time passes between disconnect/reconnect.
        
        Returns:
            True if reset successful, False otherwise
        """
        logger.info(f"Resetting device on {self.port}...")
        
        try:
            if not self.connected:
                # Scenario 1: No connection - standalone reset
                logger.info("Performing standalone reset")
                return await anyio.to_thread.run_sync(
                    lambda: reset_connection(self.port, self.baud)
                )
            else:
                # Scenario 2: Connected - reset via reconnection
                logger.info("Resetting via reconnection")
                
                # Close current connection
                await self.stop()
                await anyio.sleep(0.2)
                
                # Reconnect with reset enabled
                old_reset_at_close = self.reset_at_close
                self.reset_at_close = True  # Enable reset
                
                try:
                    # This connection will trigger reset due to reset_at_close=True
                    success = await self.start(switch_to_protobuf=True)
                    if success:
                        logger.info("Reset and reconnection successful")
                        return True
                    else:
                        logger.error("Failed to reconnect after reset")
                        return False
                finally:
                    self.reset_at_close = old_reset_at_close
                    
        except Exception as e:
            logger.error(f"Reset failed: {e}")
            return False
