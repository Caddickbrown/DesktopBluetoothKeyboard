"""
Check which Python installation is being used and provide guidance
"""
import sys
import os

print("=" * 60)
print("Python Installation Check")
print("=" * 60)
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print()

python_path = sys.executable.lower()

if "msys" in python_path or "mingw" in python_path:
    print("⚠️  WARNING: You're using MSYS2 Python")
    print()
    print("Bleak installation will likely FAIL with MSYS2 Python due to:")
    print("  - Windows path length limitations (260 char limit)")
    print("  - Build tool compatibility issues")
    print()
    print("RECOMMENDED SOLUTION:")
    print("1. Install standard Windows Python from https://www.python.org/downloads/")
    print("2. During installation, check 'Add Python to PATH'")
    print("3. Open a NEW Command Prompt (not MSYS2/PowerShell)")
    print("4. Verify with: python --version")
    print("   (Should NOT show C:\\msys64\\... path)")
    print("5. Then run: pip install bleak")
    print()
    print("Alternative: Try enabling long paths in Windows:")
    print("  - Run as Administrator: reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f")
    print("  - Restart computer")
    print("  - Then try: pip install --break-system-packages bleak")
else:
    print("✓ You're using standard Windows Python")
    print("  This should work better for installing bleak!")
    print()
    print("Try installing bleak with:")
    print("  pip install bleak")
    print()
    if "venv" in python_path or "virtualenv" in python_path:
        print("Note: You're in a virtual environment - that's good!")

print()
print("=" * 60)

