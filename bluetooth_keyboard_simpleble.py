"""
Alternative Bluetooth implementation using SimpleBLE (if available)
SimpleBLE is easier to install than bleak on some systems
"""
import asyncio
import struct
import time
from typing import Optional, List
from dataclasses import dataclass

try:
    # Try simplepyble first (the correct package name)
    import simplepyble as simpleble
    SIMPLEBLE_AVAILABLE = True
    print("Using simplepyble package")
except ImportError:
    try:
        # Fallback to simpleble
        import simpleble
        SIMPLEBLE_AVAILABLE = True
        print("Using simpleble package")
    except ImportError:
        SIMPLEBLE_AVAILABLE = False
        simpleble = None
        print("SimpleBLE not available")


@dataclass
class BluetoothDeviceInfo:
    """Bluetooth device information"""
    name: str
    address: str
    device_handle: Optional[object] = None
    
    def __str__(self):
        return f"{self.name} ({self.address})"


class SimpleBLEKeyboardService:
    """Bluetooth HID keyboard using SimpleBLE library"""
    
    HID_SERVICE_UUID = "00001812-0000-1000-8000-00805f9b34fb"
    HID_REPORT_UUID = "00002a4d-0000-1000-8000-00805f9b34fb"
    
    def __init__(self, logger=None):
        self.connected_device: Optional[BluetoothDeviceInfo] = None
        self.is_connected = False
        self.peripheral = None
        self.scanned_devices: List[BluetoothDeviceInfo] = []
        self.adapter = None
        self.report_characteristic = None
        self.logger = logger  # Optional logger callback function
        
    async def scan_for_devices(self, timeout: float = 10.0) -> List[BluetoothDeviceInfo]:
        """Scan for Bluetooth devices"""
        if not SIMPLEBLE_AVAILABLE:
            self._log("SimpleBLE not available")
            return []
        
        self.scanned_devices = []
        
        try:
            self._log("Getting adapters...")
            # Try different ways to get adapters based on API
            try:
                adapters = simpleble.Adapter.get_adapters()
            except AttributeError:
                try:
                    adapters = simpleble.get_adapters()
                except AttributeError:
                    self._log("Could not find adapter method")
                    return []
            
            if not adapters or len(adapters) == 0:
                self._log("No Bluetooth adapters found")
                return []
            
            self._log(f"Found {len(adapters)} adapter(s)")
            self.adapter = adapters[0]
            
            # Check if Bluetooth is enabled (method might vary)
            try:
                if hasattr(self.adapter, 'bluetooth_enabled') and not self.adapter.bluetooth_enabled():
                    self._log("Bluetooth is not enabled")
                    return []
            except:
                pass  # Some APIs don't have this method
            
            self._log("Setting up scan callbacks...")
            # Set callback for found devices (try different method names)
            try:
                self.adapter.set_callback_on_scan_found(self._on_device_found)
                self.adapter.set_callback_on_scan_stop(self._on_scan_stop)
            except AttributeError:
                try:
                    self.adapter.set_callback_on_scan_found(lambda device: self._on_device_found(device))
                except:
                    self._log("Could not set scan callbacks - will use polling method")
            
            self._log("Starting scan...")
            # Start scanning (try different method names)
            try:
                self.adapter.scan_start()
            except AttributeError:
                try:
                    self.adapter.scan()
                except Exception as e:
                    self._log(f"Could not start scan: {e}")
                    return []
            
            # Wait for scan to complete
            self._log(f"Scanning for {timeout} seconds...")
            await asyncio.sleep(timeout)
            
            # Stop scanning
            self._log("Stopping scan...")
            try:
                self.adapter.scan_stop()
            except AttributeError:
                try:
                    self.adapter.stop()
                except:
                    pass
            
            # Wait a bit for final callbacks
            await asyncio.sleep(0.5)
            
            # If no devices found via callbacks, try getting scanned results directly
            if len(self.scanned_devices) == 0:
                try:
                    scanned = self.adapter.scan_get_results()
                    for device in scanned:
                        self._on_device_found(device)
                except AttributeError:
                    pass
            
            self._log(f"Scan complete. Found {len(self.scanned_devices)} device(s)")
            
        except Exception as e:
            self._log(f"Scan error: {e}")
            import traceback
            traceback.print_exc()
        
        return self.scanned_devices
    
    def _on_device_found(self, device):
        """Callback for found devices"""
        try:
            # Try different ways to get device info
            name = "Unknown"
            address = "Unknown"
            
            # Try identifier() method
            try:
                name = device.identifier()
            except (AttributeError, TypeError):
                # Try as property
                try:
                    name = device.identifier
                except AttributeError:
                    # Try name() method
                    try:
                        name = device.name()
                    except (AttributeError, TypeError):
                        try:
                            name = device.name
                        except AttributeError:
                            pass
            
            # Try address() method
            try:
                address = device.address()
            except (AttributeError, TypeError):
                # Try as property
                try:
                    address = device.address
                except AttributeError:
                    # Try mac_address()
                    try:
                        address = device.mac_address()
                    except (AttributeError, TypeError):
                        try:
                            address = device.mac_address
                        except AttributeError:
                            pass
            
            if address == "Unknown":
                self._log(f"Warning: Could not get address for device {name}")
                return
            
            # Avoid duplicates
            for existing in self.scanned_devices:
                if existing.address == address:
                    return
            
            device_info = BluetoothDeviceInfo(
                name=name or "Unknown",
                address=address,
                device_handle=device
            )
            self.scanned_devices.append(device_info)
            self._log(f"Found device: {device_info}")
        except Exception as e:
            self._log(f"Error processing device: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_scan_stop(self):
        """Callback when scan stops"""
        pass
    
    def _log(self, message: str):
        """Log a message"""
        if self.logger:
            self.logger(message)
        else:
            print(message)
    
    async def connect(self, device: BluetoothDeviceInfo) -> bool:
        """Connect to device"""
        if not SIMPLEBLE_AVAILABLE:
            self._log("SimpleBLE not available")
            return False
        
        try:
            if not device.device_handle:
                self._log("Device handle is None")
                return False
            
            self._log(f"Connecting to {device.name} ({device.address})...")
            # Connect to the peripheral
            peripheral = device.device_handle
            
            # Connect (SimpleBLE uses blocking calls, so we run in executor)
            loop = asyncio.get_event_loop()
            self._log("Calling connect()...")
            try:
                await loop.run_in_executor(None, peripheral.connect)
            except AttributeError:
                # Try different method names
                try:
                    await loop.run_in_executor(None, lambda: peripheral.connect())
                except Exception as e:
                    self._log(f"Connection method failed: {e}")
                    # Try connecting via adapter
                    try:
                        await loop.run_in_executor(None, lambda: self.adapter.connect(peripheral))
                    except Exception as e2:
                        self._log(f"Adapter connect also failed: {e2}")
                        return False
            
            self._log("Connected! Discovering services...")
            # Discover services (try different method names)
            try:
                services = await loop.run_in_executor(None, peripheral.services)
            except AttributeError:
                try:
                    services = await loop.run_in_executor(None, lambda: peripheral.get_services())
                except Exception as e:
                    print(f"Could not get services: {e}")
                    # Still mark as connected even if we can't discover services
                    self.peripheral = peripheral
                    self.connected_device = device
                    self.is_connected = True
                    return True
            
            self._log(f"Found {len(services)} service(s)")
            
            # Find HID service and report characteristic
            for service in services:
                # Try different ways to get UUID
                try:
                    service_uuid = str(service.uuid()).lower()
                except (AttributeError, TypeError):
                    try:
                        service_uuid = str(service.uuid).lower()
                    except:
                        continue
                
                if "1812" in service_uuid or "hid" in service_uuid.lower():
                    self._log(f"Found HID service: {service_uuid}")
                    # Found HID service, look for report characteristic
                    try:
                        characteristics = await loop.run_in_executor(None, service.characteristics)
                    except AttributeError:
                        try:
                            characteristics = await loop.run_in_executor(None, lambda: service.get_characteristics())
                        except:
                            continue
                    
                    for char in characteristics:
                        try:
                            char_uuid = str(char.uuid()).lower()
                        except (AttributeError, TypeError):
                            try:
                                char_uuid = str(char.uuid).lower()
                            except:
                                continue
                        
                        if "2a4d" in char_uuid or "report" in char_uuid.lower():
                            # Check if it's writable
                            try:
                                can_write = str(char.can_write()).lower()
                            except (AttributeError, TypeError):
                                try:
                                    can_write = str(char.can_write).lower()
                                except:
                                    can_write = ""
                            
                            if "write" in can_write:
                                self.report_characteristic = char
                                self.peripheral = peripheral
                                self.connected_device = device
                                self.is_connected = True
                                self._log(f"Connected to {device.name} and found HID report characteristic: {char_uuid}")
                                return True
            
            # If we can't find HID service, still mark as connected
            # Some devices might work differently
            self._log(f"Connected to {device.name} but HID service not found (may not work)")
            self.peripheral = peripheral
            self.connected_device = device
            self.is_connected = True
            return True
            
        except Exception as e:
            self._log(f"Connection error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def disconnect(self):
        """Disconnect"""
        try:
            if self.peripheral:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.peripheral.disconnect)
        except Exception as e:
            print(f"Disconnect error: {e}")
        finally:
            self.is_connected = False
            self.connected_device = None
            self.peripheral = None
            self.report_characteristic = None
    
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
    
    async def send_key(self, key_code: int, modifier: int = 0):
        """Send key press"""
        if not self.is_connected or not self.peripheral:
            return False
        
        try:
            report = self._create_hid_report(key_code, modifier)
            loop = asyncio.get_event_loop()
            
            if self.report_characteristic:
                # Write to the characteristic
                await loop.run_in_executor(
                    None,
                    lambda: self.peripheral.write_request(
                        self.report_characteristic.uuid(),
                        report
                    )
                )
                return True
            else:
                # Try to find and write to any writable characteristic
                services = await loop.run_in_executor(None, self.peripheral.services)
                for service in services:
                    characteristics = await loop.run_in_executor(None, service.characteristics)
                    for char in characteristics:
                        if "write" in str(char.can_write()).lower():
                            await loop.run_in_executor(
                                None,
                                lambda: self.peripheral.write_request(char.uuid(), report)
                            )
                            return True
        except Exception as e:
            print(f"Error sending key: {e}")
            return False
        
        return False
    
    async def send_character(self, char: str):
        """Send character"""
        if len(char) == 0:
            return
        
        key_code = self._char_to_hid_code(char)
        if key_code is None:
            print(f"Unsupported character: {char}")
            return
        
        modifier = 0
        if char.isupper() or char in '!@#$%^&*()_+{}|:"<>?':
            modifier = 2  # Left Shift
        
        # Press key
        await self.send_key(key_code, modifier)
        await asyncio.sleep(0.01)
        
        # Release key
        await self.send_key(0, 0)
        await asyncio.sleep(0.01)
    
    async def send_backspace(self):
        """Send backspace"""
        await self.send_key(42, 0)  # Backspace key code
        await asyncio.sleep(0.01)
        await self.send_key(0, 0)  # Release
        await asyncio.sleep(0.01)

