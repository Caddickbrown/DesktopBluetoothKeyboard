# Installation Guide for Desktop Bluetooth Keyboard

## The Problem

If you're using MSYS2 Python (like `C:\msys64\ucrt64\bin\python.exe`), installing `bleak` can fail due to:
- Windows path length limitations when building dependencies
- Complex Windows Bluetooth API compilation requirements
- MSYS2-specific build environment issues

## Recommended Solution: Use Standard Windows Python

### Step 1: Install Standard Windows Python
1. Download Python from https://www.python.org/downloads/
2. **Important**: During installation, check the box "Add Python to PATH"
3. Complete the installation

### Step 2: Verify Installation
Open a **new** Command Prompt (not MSYS2 terminal) and run:
```bash
python --version
```
You should see something like `Python 3.12.x` from a standard installation path (not `C:\msys64\...`)

### Step 3: Install Dependencies
```bash
cd C:\Users\dcaddick-brown\Documents\VSCode\DesktopBluetoothKeyboard
pip install bleak
```

### Step 4: Run the Application
```bash
python main.py
```

## Alternative: If You Must Use MSYS2 Python

If you need to stick with MSYS2 Python, try these workarounds:

### Option 1: Virtual Environment in Short Path
```bash
# Create venv in very short path
python -m venv C:\v
C:\v\Scripts\activate  # or C:\v\bin\activate on MSYS2
pip install bleak
```

### Option 2: Try Installation Anyway
```bash
pip install --break-system-packages bleak
```
Note: This may still fail due to the build issues mentioned above.

## Why Standard Windows Python Works Better

- Better integration with Windows build tools
- Shorter default paths
- Pre-compiled wheels available for many packages
- Better support for Windows-specific libraries like `bleak`

## Troubleshooting

**"ModuleNotFoundError: No module named 'bleak'"**
- Make sure you're using the correct Python installation
- Verify with: `python -c "import sys; print(sys.executable)"`
- Reinstall bleak if needed

**Build errors during installation**
- Use standard Windows Python instead of MSYS2
- Ensure you have Visual C++ Build Tools installed (usually comes with Python)

**Bluetooth not working**
- Make sure Bluetooth is enabled on your computer
- Check Windows Bluetooth settings
- Some devices may require pairing first through Windows settings

