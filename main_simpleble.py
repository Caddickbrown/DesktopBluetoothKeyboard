"""
Desktop Bluetooth Keyboard - Main Application (SimpleBLE Version)
Cross-platform GUI application to use desktop as Bluetooth keyboard using SimpleBLE
"""
import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional, List

try:
    from bluetooth_keyboard_simpleble import SimpleBLEKeyboardService, BluetoothDeviceInfo, SIMPLEBLE_AVAILABLE
    BLUETOOTH_AVAILABLE = True
except ImportError as e:
    BLUETOOTH_AVAILABLE = False
    SimpleBLEKeyboardService = None
    BluetoothDeviceInfo = None
    SIMPLEBLE_AVAILABLE = False
    IMPORT_ERROR = str(e)


class BluetoothKeyboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Desktop Bluetooth Keyboard (SimpleBLE)")
        self.root.geometry("800x700")
        
        if not BLUETOOTH_AVAILABLE or not SIMPLEBLE_AVAILABLE:
            self.show_installation_error()
            return
        
        self.bluetooth_service = SimpleBLEKeyboardService(logger=self.log)
        self.devices: List[BluetoothDeviceInfo] = []
        self.selected_device: Optional[BluetoothDeviceInfo] = None
        self.last_text = ""
        self.loop = None
        
        self.setup_ui()
        self.setup_event_loop()
    
    def show_installation_error(self):
        """Show error message about missing SimpleBLE library"""
        error_frame = ttk.Frame(self.root, padding="20")
        error_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(error_frame, text="SimpleBLE Not Installed", 
                         font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        error_text = f"""SimpleBLE library not found. Please install it:

Error: {IMPORT_ERROR if not BLUETOOTH_AVAILABLE else 'SimpleBLE not available'}

Installation:
   pip install simpleble

Note: SimpleBLE is often easier to install than bleak, especially on Windows.

After installation, restart this application."""
        
        text_widget = scrolledtext.ScrolledText(error_frame, wrap=tk.WORD, 
                                                height=10, width=70)
        text_widget.insert("1.0", error_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=10)
        
        close_button = ttk.Button(error_frame, text="Close", 
                                 command=self.root.destroy)
        close_button.pack(pady=10)
    
    def setup_event_loop(self):
        """Setup asyncio event loop for tkinter"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Connection section
        conn_frame = ttk.LabelFrame(main_frame, text="Bluetooth Connection", padding="10")
        conn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        conn_frame.columnconfigure(0, weight=1)
        
        device_frame = ttk.Frame(conn_frame)
        device_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        device_frame.columnconfigure(0, weight=1)
        
        self.device_combo = ttk.Combobox(device_frame, state="readonly", width=40)
        self.device_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.scan_button = ttk.Button(device_frame, text="Scan", command=self.on_scan_clicked)
        self.scan_button.grid(row=0, column=1, padx=(0, 10))
        
        self.connect_button = ttk.Button(device_frame, text="Connect", command=self.on_connect_clicked, state="disabled")
        self.connect_button.grid(row=0, column=2)
        
        self.status_label = ttk.Label(conn_frame, text="Status: Not connected", foreground="gray")
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Typing section
        typing_frame = ttk.LabelFrame(main_frame, text="Type Here", padding="10")
        typing_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        typing_frame.columnconfigure(0, weight=1)
        typing_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        self.input_text = scrolledtext.ScrolledText(typing_frame, height=8, wrap=tk.WORD)
        self.input_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.input_text.bind('<KeyRelease>', self.on_text_changed)
        self.input_text.config(state="disabled")
        
        # Instructions
        instructions_frame = ttk.LabelFrame(main_frame, text="Instructions", padding="10")
        instructions_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        instructions_text = """1. Click 'Scan' to discover Bluetooth devices
2. Select your device from the dropdown
3. Click 'Connect' to pair and connect
4. Type in the text field above - your keystrokes will be sent to the connected device

Note: Your device must support Bluetooth HID (Human Interface Device) profile.
Using SimpleBLE backend."""
        
        ttk.Label(instructions_frame, text=instructions_text, justify=tk.LEFT, foreground="darkgray").grid(row=0, column=0, sticky=tk.W)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear button
        clear_button = ttk.Button(main_frame, text="Clear Input", command=self.on_clear_clicked)
        clear_button.grid(row=4, column=0, sticky=tk.E)
        
        self.log("Application started. Ready to scan for devices.")
    
    def log(self, message: str):
        """Add message to log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def on_scan_clicked(self):
        """Handle scan button click"""
        self.scan_button.config(state="disabled")
        self.status_label.config(text="Status: Scanning...")
        self.log("Starting device scan...")
        
        # Run async scan in event loop
        task = asyncio.run_coroutine_threadsafe(self.scan_devices(), self.loop)
        task.add_done_callback(self.on_scan_complete)
    
    async def scan_devices(self):
        """Scan for Bluetooth devices"""
        try:
            self.devices = await self.bluetooth_service.scan_for_devices(timeout=10.0)
            return self.devices
        except Exception as e:
            self.log(f"Error scanning: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def on_scan_complete(self, task):
        """Handle scan completion"""
        try:
            devices = task.result()
            self.device_combo['values'] = [str(d) for d in devices]
            
            if devices:
                self.device_combo.current(0)
                self.connect_button.config(state="normal")
                self.log(f"Found {len(devices)} device(s)")
            else:
                self.log("No devices found")
                messagebox.showinfo("Scan Complete", "No Bluetooth devices found.")
        except Exception as e:
            self.log(f"Scan error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Error scanning for devices: {e}")
        finally:
            self.scan_button.config(state="normal")
            self.status_label.config(text="Status: Scan complete")
    
    def on_connect_clicked(self):
        """Handle connect button click"""
        selection = self.device_combo.current()
        if selection < 0 or selection >= len(self.devices):
            messagebox.showwarning("No Device", "Please select a device first.")
            return
        
        self.selected_device = self.devices[selection]
        self.connect_button.config(state="disabled")
        self.status_label.config(text="Status: Connecting...")
        self.log(f"Attempting to connect to {self.selected_device.name or self.selected_device.address}...")
        
        # Run async connect in event loop
        task = asyncio.run_coroutine_threadsafe(self.connect_device(), self.loop)
        task.add_done_callback(self.on_connect_complete)
    
    async def connect_device(self):
        """Connect to selected device"""
        try:
            return await self.bluetooth_service.connect(self.selected_device)
        except Exception as e:
            self.log(f"Connection error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def on_connect_complete(self, task):
        """Handle connection completion"""
        try:
            connected = task.result()
            if connected:
                device_name = self.selected_device.name or self.selected_device.address
                self.status_label.config(text=f"Status: Connected to {device_name}", foreground="green")
                self.log(f"Successfully connected to {device_name}")
                self.input_text.config(state="normal")
                self.input_text.focus()
            else:
                self.status_label.config(text="Status: Connection failed", foreground="red")
                self.log("Connection failed. Make sure the device supports HID keyboard profile.")
                self.connect_button.config(state="normal")
                messagebox.showerror("Connection Failed", 
                    "Failed to connect. Make sure:\n"
                    "- The device supports Bluetooth HID profile\n"
                    "- The device is in pairing mode\n"
                    "- Bluetooth is enabled on both devices")
        except Exception as e:
            self.log(f"Connection error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Error connecting: {e}")
            self.connect_button.config(state="normal")
    
    def on_text_changed(self, event):
        """Handle text input changes"""
        if not self.bluetooth_service.is_connected:
            return
        
        current_text = self.input_text.get("1.0", tk.END)
        current_text = current_text.rstrip('\n')
        
        if len(current_text) > len(self.last_text):
            # Text was added
            new_text = current_text[len(self.last_text):]
            asyncio.run_coroutine_threadsafe(self.send_text(new_text), self.loop)
        elif len(current_text) < len(self.last_text):
            # Text was deleted
            delete_count = len(self.last_text) - len(current_text)
            asyncio.run_coroutine_threadsafe(self.send_backspaces(delete_count), self.loop)
        
        self.last_text = current_text
    
    async def send_text(self, text: str):
        """Send text characters"""
        for char in text:
            if char == '\n' or char == '\r':
                await self.bluetooth_service.send_character('\n')
            else:
                await self.bluetooth_service.send_character(char)
            await asyncio.sleep(0.05)  # Small delay between characters
    
    async def send_backspaces(self, count: int):
        """Send backspace keys"""
        for _ in range(count):
            await self.bluetooth_service.send_backspace()
            await asyncio.sleep(0.05)
    
    def on_clear_clicked(self):
        """Handle clear button click"""
        self.input_text.delete("1.0", tk.END)
        self.last_text = ""
    
    def on_closing(self):
        """Handle window closing"""
        if self.bluetooth_service.is_connected:
            asyncio.run_coroutine_threadsafe(self.bluetooth_service.disconnect(), self.loop)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = BluetoothKeyboardApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Run the asyncio event loop in a separate thread
    import threading
    def run_event_loop():
        asyncio.set_event_loop(app.loop)
        app.loop.run_forever()
    
    loop_thread = threading.Thread(target=run_event_loop, daemon=True)
    loop_thread.start()
    
    root.mainloop()


if __name__ == "__main__":
    main()

