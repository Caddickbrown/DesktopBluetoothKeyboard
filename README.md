# Desktop Bluetooth Keyboard

A cross-platform Python application that allows you to use your desktop computer as a Bluetooth keyboard. Type into the application and your keystrokes will appear on your connected device (phone, tablet, etc.).

## Features

- **Cross-platform**: Works on Windows, macOS, and Linux
- **Simple GUI**: Easy-to-use interface built with tkinter
- **Bluetooth HID**: Implements Bluetooth HID (Human Interface Device) keyboard protocol
- **Real-time typing**: Type in the text field and see it appear on your connected device

## Requirements

- Python 3.8 or higher
- Bluetooth adapter on your computer
- A device that supports Bluetooth HID keyboard profile (most modern phones/tablets)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

## Usage

1. **Scan for devices**: Click the "Scan" button to discover nearby Bluetooth devices
2. **Select device**: Choose your target device from the dropdown list
3. **Connect**: Click "Connect" to pair and connect to the device
4. **Type**: Start typing in the text field - your keystrokes will be sent to the connected device

## Notes

- Your target device must support the Bluetooth HID (Human Interface Device) profile
- Some devices may require you to put them in pairing mode first
- Make sure Bluetooth is enabled on both your computer and the target device
- The application requires appropriate Bluetooth permissions on your system

## Troubleshooting

- **No devices found**: Make sure Bluetooth is enabled and devices are discoverable
- **Connection failed**: Verify the device supports HID keyboard profile
- **Keystrokes not appearing**: Some devices may require additional setup or permissions

## Platform-Specific Notes

### Windows
- May require running as administrator
- Ensure Bluetooth drivers are installed

### macOS
- May require granting Bluetooth permissions in System Preferences
- Some versions may need additional permissions

### Linux
- Requires BlueZ stack installed (`sudo apt-get install bluez` on Debian/Ubuntu)
- May require running with appropriate permissions

## License

MIT License
