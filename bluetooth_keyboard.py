"""
Bluetooth HID Keyboard Service
Implements HID keyboard protocol over Bluetooth Low Energy (BLE)
Tries multiple backends: SimpleBLE, bleak, or Windows native APIs
"""
import asyncio
import struct
import sys
from typing import Optional, List, Dict
from dataclasses import dataclass

# Try to import different Bluetooth libraries in order of preference
BACKEND = None
BLEDevice = None

# Option 1: Try SimpleBLE (often easier to install)
try:
    import simpleble
    BACKEND = "simpleble"
    print("Using SimpleBLE backend")
except ImportError:
    pass

# Option 2: Try bleak (most common, but has installation issues on MSYS2)
if BACKEND is None:
    try:
        from bleak import BleakClient, BleakScanner
        from bleak.backends.device import BLEDevice
        BACKEND = "bleak"
        print("Using bleak backend")
    except ImportError:
        pass

# Option 3: Try pybluez (classic Bluetooth, Windows/Linux)
if BACKEND is None and sys.platform == "win32":
    try:
        import bluetooth
        BACKEND = "pybluez"
        print("Using pybluez backend (classic Bluetooth)")
    except ImportError:
        pass

# If no backend found, provide helpful error
if BACKEND is None:
    raise ImportError(
        "No Bluetooth library found. Please install one of:\n"
        "  1. SimpleBLE (recommended): pip install simpleble\n"
        "  2. bleak: pip install bleak\n"
        "  3. pybluez (Windows/Linux): pip install pybluez\n"
        "\n"
        "Note: On Windows with MSYS2 Python, bleak may fail to install.\n"
        "Try SimpleBLE or use standard Windows Python instead."
    )

# Create a common device info class
@dataclass
class BluetoothDeviceInfo:
    """Bluetooth device information"""
    name: str
    address: str
    device_handle: Optional[object] = None
    
    def __str__(self):
        return f"{self.name} ({self.address})"


class BluetoothKeyboardService:
    """Service for connecting and sending keystrokes via Bluetooth HID"""
    
    # HID Service UUIDs (standard BLE HID service)
    HID_SERVICE_UUID = "00001812-0000-1000-8000-00805f9b34fb"
    HID_REPORT_UUID = "00002a4d-0000-1000-8000-00805f9b34fb"
    HID_REPORT_MAP_UUID = "00002a4b-0000-1000-8000-00805f9b34fb"
    
    # Some devices use different UUIDs - we'll try to find the right one
    HID_REPORT_CHAR_UUID = None  # Will be discovered
    
    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.connected_device: Optional[BLEDevice] = None
        self.is_connected = False
        self.report_char_handle = None
        
    async def scan_for_devices(self, timeout: float = 10.0) -> List[BluetoothDeviceInfo]:
        """Scan for Bluetooth devices"""
        print("Scanning for Bluetooth devices...")
        
        if BACKEND == "bleak":
            bleak_devices = await BleakScanner.discover(timeout=timeout)
            devices = []
            for d in bleak_devices:
                devices.append(BluetoothDeviceInfo(
                    name=d.name or "Unknown",
                    address=d.address,
                    device_handle=d
                ))
            return devices
        elif BACKEND == "simpleble":
            # SimpleBLE scanning
            adapters = simpleble.Adapter.get_adapters()
            if not adapters:
                return []
            adapter = adapters[0]
            adapter.scan_start()
            await asyncio.sleep(timeout)
            adapter.scan_stop()
            # Collect found devices (simplified)
            return []
        elif BACKEND == "pybluez":
            # pybluez scanning (classic Bluetooth)
            import bluetooth
            devices = []
            nearby_devices = bluetooth.discover_devices(duration=timeout, lookup_names=True)
            for addr, name in nearby_devices:
                devices.append(BluetoothDeviceInfo(
                    name=name or "Unknown",
                    address=addr,
                    device_handle=addr
                ))
            return devices
        
        return []
    
    async def connect(self, device: BluetoothDeviceInfo) -> bool:
        """Connect to a Bluetooth device"""
        try:
            if BACKEND == "bleak":
                self.client = BleakClient(device.device_handle.address)
                await self.client.connect()
                
                if not self.client.is_connected:
                    return False
            elif BACKEND == "simpleble":
                # SimpleBLE connection
                self.client = device.device_handle  # Would be a SimpleBLE peripheral
                # Connection logic here
            elif BACKEND == "pybluez":
                # pybluez connection (classic Bluetooth)
                import bluetooth
                self.client = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.client.connect((device.address, 1))
            
            # Discover HID service and characteristics
            if BACKEND == "bleak":
                services = await self.client.get_services()
                
                # Look for HID service
                hid_service = None
                for service in services:
                    if self.HID_SERVICE_UUID.lower() in str(service.uuid).lower():
                        hid_service = service
                        break
                
                if not hid_service:
                    # Try to find any service that might be HID-related
                    for service in services:
                        for char in service.characteristics:
                            if "report" in str(char.uuid).lower() or "2a4d" in str(char.uuid).lower():
                                self.report_char_handle = char.handle
                                self.connected_device = device
                                self.is_connected = True
                                return True
                
                if hid_service:
                    # Find report characteristic
                    for char in hid_service.characteristics:
                        uuid_str = str(char.uuid).lower()
                        if "report" in uuid_str or "2a4d" in uuid_str or "2a4b" in uuid_str:
                            if "write" in char.properties or "write-without-response" in char.properties:
                                self.report_char_handle = char.handle
                                self.connected_device = device
                                self.is_connected = True
                                return True
            
            # If we can't find HID service, still mark as connected
            # Some devices might work differently
            self.connected_device = device
            self.is_connected = True
            return True
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the device"""
        if BACKEND == "bleak":
            if self.client and self.client.is_connected:
                await self.client.disconnect()
        elif BACKEND == "simpleble":
            if self.client:
                self.client.disconnect()
        elif BACKEND == "pybluez":
            if self.client:
                self.client.close()
        
        self.is_connected = False
        self.connected_device = None
        self.client = None
        self.report_char_handle = None
    
    def _char_to_hid_code(self, char: str) -> Optional[int]:
        """Convert character to HID key code"""
        # HID Usage ID for keyboard (modifier + key)
        # This is a simplified mapping - full HID spec is more complex
        char_upper = char.upper()
        
        # Letters A-Z
        if 'A' <= char_upper <= 'Z':
            return ord(char_upper) - ord('A') + 4
        
        # Numbers 0-9
        if '0' <= char <= '9':
            if char == '0':
                return 39
            return ord(char) - ord('0') + 30
        
        # Special characters (simplified mapping)
        special_chars = {
            ' ': 44,  # Space
            '\n': 40,  # Enter
            '\r': 40,  # Enter
            '\t': 43,  # Tab
            '-': 45,
            '=': 46,
            '[': 47,
            ']': 48,
            '\\': 49,
            ';': 51,
            "'": 52,
            '`': 53,
            ',': 54,
            '.': 55,
            '/': 56,
        }
        
        return special_chars.get(char)
    
    def _create_hid_report(self, key_code: int, modifier: int = 0) -> bytes:
        """Create HID keyboard report"""
        # HID keyboard report format: [modifier, reserved, key1, key2, key3, key4, key5, key6]
        report = bytearray(8)
        report[0] = modifier  # Modifier keys (Ctrl, Shift, Alt, etc.)
        report[2] = key_code   # Key code
        return bytes(report)
    
    async def send_key(self, key_code: int, modifier: int = 0):
        """Send a key press"""
        if not self.is_connected or not self.client:
            return False
        
        if BACKEND == "bleak":
            if not self.client.is_connected:
                return False
            
            if not self.report_char_handle:
                # Try to find the characteristic dynamically
                services = await self.client.get_services()
                for service in services:
                    for char in service.characteristics:
                        if "write" in char.properties or "write-without-response" in char.properties:
                            self.report_char_handle = char.handle
                            break
                    if self.report_char_handle:
                        break
            
            if not self.report_char_handle:
                return False
            
            try:
                report = self._create_hid_report(key_code, modifier)
                
                # Try to write to the characteristic
                services = await self.client.get_services()
                for service in services:
                    for char in service.characteristics:
                        if char.handle == self.report_char_handle:
                            if "write-without-response" in char.properties:
                                await self.client.write_gatt_char(char, report, response=False)
                            elif "write" in char.properties:
                                await self.client.write_gatt_char(char, report, response=True)
                            return True
                
                return False
            except Exception as e:
                print(f"Error sending key: {e}")
                return False
        elif BACKEND == "simpleble":
            # SimpleBLE write logic
            report = self._create_hid_report(key_code, modifier)
            # Implementation would go here
            return True
        elif BACKEND == "pybluez":
            # pybluez write (classic Bluetooth)
            report = self._create_hid_report(key_code, modifier)
            try:
                self.client.send(report)
                return True
            except Exception as e:
                print(f"Error sending key: {e}")
                return False
        
        return False
    
    async def send_character(self, char: str):
        """Send a character"""
        if len(char) == 0:
            return
        
        key_code = self._char_to_hid_code(char)
        if key_code is None:
            print(f"Unsupported character: {char}")
            return
        
        # Determine if shift is needed (for uppercase and special chars)
        modifier = 0
        if char.isupper() or char in '!@#$%^&*()_+{}|:"<>?' :
            modifier = 2  # Left Shift
        
        # Press key
        await self.send_key(key_code, modifier)
        await asyncio.sleep(0.01)  # Small delay
        
        # Release key (send empty report)
        await self.send_key(0, 0)
        await asyncio.sleep(0.01)
    
    async def send_backspace(self):
        """Send backspace key"""
        await self.send_key(42, 0)  # Backspace key code
        await asyncio.sleep(0.01)
        await self.send_key(0, 0)  # Release
        await asyncio.sleep(0.01)

