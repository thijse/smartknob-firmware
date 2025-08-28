"""
SmartKnob Connection Utilities

Utilities for finding and connecting to SmartKnob devices.
"""

import serial
import serial.tools.list_ports
import logging
import time
from typing import List, Optional, Tuple
from .protocol import SmartKnobConnection, SmartKnobProtocol

logger = logging.getLogger(__name__)

# USB VID/PID pairs for known SmartKnob devices 
SMARTKNOB_USB_IDS = [
    (0x1a86, 0x7523),  # CH340 USB-to-serial chip
    (0x303a, 0x1001),  # ESP32-S3 native USB
]

# Keywords to exclude (likely not SmartKnob devices)
EXCLUDE_KEYWORDS = [
    "bluetooth", "bt", "hid", "mouse", "keyboard", "audio", "webcam", 
    "camera", "printer", "scanner", "modem", "fax", "virtual", "loopback"
]

def find_smartknob_ports(validate_protocol: bool = False) -> List[str]:
    """
    Find SmartKnob serial ports using multiple detection methods.
    
    Args:
        validate_protocol: If True, test each port with protocol validation
        
    Returns:
        List of port names that are likely SmartKnob devices
    """
    logger.info("Searching for SmartKnob devices...")
    
    # Get all available serial ports
    available_ports = serial.tools.list_ports.comports()
    logger.debug(f"Found {len(available_ports)} total serial ports")
    
    candidates = []
    
    # Method 1: USB VID/PID matching (most reliable)
    vid_pid_matches = []
    for port in available_ports:
        if port.vid is not None and port.pid is not None:
            if (port.vid, port.pid) in SMARTKNOB_USB_IDS:
                vid_pid_matches.append(port.device)
                logger.info(f"✅ USB VID/PID match: {port.device} - {port.description} "
                           f"(VID:0x{port.vid:04x}, PID:0x{port.pid:04x})")
    
    if vid_pid_matches:
        logger.info(f"Found {len(vid_pid_matches)} devices with matching USB VID/PID")
        candidates.extend(vid_pid_matches)
    
    # Method 2: Description-based filtering (fallback)
    if not candidates:
        logger.info("No USB VID/PID matches, trying description-based detection...")
        
        for port in available_ports:
            description = (port.description or "").lower()
            manufacturer = (port.manufacturer or "").lower()
            
            # Skip excluded devices
            if any(keyword in description or keyword in manufacturer 
                   for keyword in EXCLUDE_KEYWORDS):
                logger.debug(f"Excluding {port.device}: {port.description}")
                continue
            
            # Look for ESP32 or USB-serial indicators
            if any(keyword in description or keyword in manufacturer for keyword in 
                   ["esp32", "ch340", "cp210", "cp2102", "ftdi", "usb serial", "uart"]):
                candidates.append(port.device)
                logger.info(f"📝 Description match: {port.device} - {port.description}")
    
    # Method 3: Protocol validation (optional, most reliable but slower)
    if validate_protocol and candidates:
        logger.info("Validating candidates with protocol test...")
        validated_ports = []
        
        for port in candidates:
            if _validate_smartknob_protocol(port):
                validated_ports.append(port)
                logger.info(f"✅ Protocol validated: {port}")
            else:
                logger.debug(f"❌ Protocol validation failed: {port}")
        
        if validated_ports:
            candidates = validated_ports
        else:
            logger.warning("No ports passed protocol validation, returning unvalidated candidates")
    
    # Fallback: return all ports if nothing found
    if not candidates:
        logger.warning("No SmartKnob candidates found, returning all available ports")
        candidates = [port.device for port in available_ports]
    
    logger.info(f"Final candidates: {candidates}")
    return candidates

def _validate_smartknob_protocol(port: str, timeout: float = 2.0) -> bool:
    """
    Test if a port responds like a SmartKnob device.
    
    Args:
        port: Serial port to test
        timeout: Maximum time to wait for response
        
    Returns:
        True if device responds with expected protocol
    """
    try:
        # Open port with short timeout
        ser = serial.Serial(port=port, baudrate=921600, timeout=0)
        
        # Send 'q' to switch to protobuf mode
        ser.write(b"q")
        ser.flush()
        time.sleep(0.2)
        
        # Look for protobuf-like data (0x00 delimited frames)
        start_time = time.time()
        buffer = bytearray()
        
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                buffer.extend(ser.read(ser.in_waiting))
                
                # Look for frame delimiters and reasonable frame sizes
                if b'\x00' in buffer:
                    frames = buffer.split(b'\x00')
                    for frame in frames[:-1]:  # Exclude incomplete last frame
                        if 10 <= len(frame) <= 200:  # Reasonable protobuf frame size
                            ser.close()
                            return True
            else:
                time.sleep(0.01)
        
        ser.close()
        return False
        
    except Exception as e:
        logger.debug(f"Protocol validation failed for {port}: {e}")
        return False

def get_port_info(port: str) -> dict:
    """
    Get detailed information about a serial port.
    
    Args:
        port: Serial port name
        
    Returns:
        Dictionary with port information
    """
    available_ports = serial.tools.list_ports.comports()
    
    for p in available_ports:
        if p.device == port:
            return {
                'device': p.device,
                'description': p.description,
                'manufacturer': p.manufacturer,
                'vid': f"0x{p.vid:04x}" if p.vid else None,
                'pid': f"0x{p.pid:04x}" if p.pid else None,
                'serial_number': p.serial_number,
                'location': p.location,
                'interface': p.interface
            }
    
    return {'device': port, 'description': 'Port not found'}

def connect_smartknob(port: Optional[str] = None, baud: int = 921600) -> Optional[SmartKnobConnection]:
    """
    Connect to a SmartKnob device.
    
    Args:
        port: Specific port to connect to, or None to auto-detect
        baud: Baud rate (default: 921600)
        
    Returns:
        SmartKnobConnection instance if successful, None otherwise
    """
    ports_to_try = [port] if port else find_smartknob_ports()
    
    for port_name in ports_to_try:
        logger.info(f"Attempting to connect to {port_name}")
        
        try:
            connection = SmartKnobConnection(port_name, baud)
            if connection.connect():
                logger.info(f"Successfully connected to SmartKnob on {port_name}")
                return connection
        except Exception as e:
            logger.debug(f"Failed to connect to {port_name}: {e}")
            continue
    
    logger.error("Failed to connect to any SmartKnob device")
    return None
