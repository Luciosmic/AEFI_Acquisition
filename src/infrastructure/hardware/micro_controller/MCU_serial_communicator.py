import serial
import threading
import time

class MCU_SerialCommunicator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MCU_SerialCommunicator, cls).__new__(cls)
                    cls._instance.ser = None
                    cls._instance.port = None
                    cls._instance.baudrate = 9600
                    cls._instance.lock = threading.Lock()
        return cls._instance

    def connect(self, port, baudrate=9600):
        """Establish serial connection."""
        with self.lock:
            if self.ser and self.ser.is_open:
                if self.port == port:
                    return True  # Already connected to the same port
                else:
                    self.ser.close() # Close if different port

            self.port = port
            self.baudrate = baudrate
            try:
                self.ser = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=8,
                    stopbits=serial.STOPBITS_ONE,
                    parity=serial.PARITY_NONE,
                    timeout=1,
                    write_timeout=1
                )
                return True
            except Exception as e:
                print(f"Serial connection error: {e}")
                return False

    def disconnect(self):
        """Close serial connection."""
        with self.lock:
            if self.ser and self.ser.is_open:
                self.ser.close()

    def send_command(self, command):
        """Send command and return response."""
        if not self.ser or not self.ser.is_open:
            return False, "Not connected"

        with self.lock:
            try:
                if not command.endswith('*'):
                    command += '*'
                
                self.ser.write(command.encode())
                
                # Special handling for acquisition command 'm'
                if command.startswith('m') and command[1:].replace('*', '').isdigit():
                    confirmation = self.ser.readline() # Read confirmation
                    
                    data_response = self.ser.readline() # Read data
                    
                    response_str = data_response.decode('ascii', errors='ignore').rstrip('\r\n')
                    return True, response_str
                else:
                    response = self.ser.readline()
                    
                    response_str = response.decode('ascii', errors='ignore').rstrip('\r\n')
                    return True, response_str
            except Exception as e:
                print(f"[MCU_Serial] Error: {e}")
                return False, str(e)
