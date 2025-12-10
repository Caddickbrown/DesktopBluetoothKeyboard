"""
Alternative Bluetooth implementation using SimpleBLE (if available)
SimpleBLE is easier to install than bleak on some systems
"""
import asyncio
import struct
from typing import Optional, List
from dataclasses import dataclass

try:
    import simpleble
    SIMPLEBLE_AVAILABLE = True
except ImportError:
    SIMPLEBLE_AVAILABLE = False
    simpleble = None


@dataclass
class BluetoothDeviceInfo:
    """Bluetooth device information"""
    name: str
    address: str
    device_handle: Optional[object] = None


class SimpleBLEKeyboardService:
    """Bluetooth HID keyboard using SimpleBLE library"""
    
    HID_SERVICE_UUID = "00001812-0000-1000-8000-00805f9b34fb"
    HID_REPORT_UUID = "00002a4d-0000-1000-8000-00805f9b34fb"
    
    def __init__(self):
        self.connected_device: Optional[BluetoothDeviceInfo] = None
        self.is_connected = False
        self.peripheral = None
        
    def scan_for_devices(self, timeout: float = 10.0) -> List[BluetoothDeviceInfo]:
        """Scan for Bluetooth devices"""
        if not SIMPLEBLE_AVAILABLE:
            return []
        
        devices = []
        try:
            adapters = simpleble.Adapter.get_adapters()
            if not adapters:
                return []
            
            adapter = adapters[0]
            adapter.set_callback_on_scan_found(self._on_device_found)
            
            adapter.scan_start()
            time.sleep(timeout)
            adapter.scan_stop()
            
            # Devices found via callback would be stored
            # This is simplified - full implementation would collect devices
        except Exception as e:
            print(f"Scan error: {e}")
        
        return devices
    
    def _on_device_found(self, device):
        """Callback for found devices"""
        pass
    
    def connect(self, device: BluetoothDeviceInfo) -> bool:
        """Connect to device"""
        if not SIMPLEBLE_AVAILABLE:
            return False
        
        try:
            # SimpleBLE connection logic
            self.connected_device = device
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect"""
        self.is_connected = False
        self.connected_device = None
        self.peripheral = None
    
    def _char_to_hid_code(self, char: str) -> Optional[int]:
        """Convert character to HID key code"""
        char_upper = char.upper()
        if 'A' <= char_upper <= 'Z':
            return ord(char_upper) - ord('A') + 4
        if '0' <= char <= '9':
            return 39 if char == '0' else ord(char) - ord('0') + 30
        special_chars = {
            ' ': 44, '\n': 40, '\r': 40, '\t': 43,
            '-': 45, '=': 46, '[': 47, ']': 48, '\\': 49,
            ';': 51, "'": 52, '`': 53, ',': 54, '.': 55, '/': 56,
        }
        return special_chars.get(char)
    
    def _create_hid_report(self, key_code: int, modifier: int = 0) -> bytes:
        """Create HID keyboard report"""
        report = bytearray(8)
        report[0] = modifier
        report[2] = key_code
        return bytes(report)
    
    def send_key(self, key_code: int, modifier: int = 0):
        """Send key press"""
        if not self.is_connected:
            return False
        # SimpleBLE write logic here
        return True
    
    def send_character(self, char: str):
        """Send character"""
        key_code = self._char_to_hid_code(char)
        if key_code is None:
            return
        modifier = 2 if char.isupper() or char in '!@#$%^&*()_+{}|:"<>?' else 0
        self.send_key(key_code, modifier)
        time.sleep(0.01)
        self.send_key(0, 0)
    
    def send_backspace(self):
        """Send backspace"""
        self.send_key(42, 0)
        time.sleep(0.01)
        self.send_key(0, 0)

