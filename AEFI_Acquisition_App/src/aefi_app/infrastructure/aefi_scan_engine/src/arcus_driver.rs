use serialport::{SerialPort, SerialPortType};
use std::io::{self, Read, Write};
use std::time::Duration;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ArcusError {
    #[error("Serial port error: {0}")]
    Serial(#[from] serialport::Error),
    #[error("IO error: {0}")]
    Io(#[from] io::Error),
    #[error("Timeout waiting for response")]
    Timeout,
    #[error("Invalid response: {0}")]
    InvalidResponse(String),
}

pub struct ArcusController {
    port: Box<dyn SerialPort>,
}

impl ArcusController {
    pub fn connect(port_name: &str, baud_rate: u32) -> Result<Self, ArcusError> {
        let port = serialport::new(port_name, baud_rate)
            .timeout(Duration::from_millis(100))
            .open()?;
        
        Ok(ArcusController { port })
    }

    fn send_command(&mut self, cmd: &str) -> Result<(), ArcusError> {
        self.port.write_all(cmd.as_bytes())?;
        self.port.write_all(b"\r")?; // Terminator
        Ok(())
    }

    fn read_response(&mut self) -> Result<String, ArcusError> {
        let mut buffer: Vec<u8> = Vec::new();
        let mut temp_buf = [0u8; 1];
        
        // Simple read until newline or timeout
        // In production, use a more robust buffered reader
        loop {
            match self.port.read(&mut temp_buf) {
                Ok(n) if n > 0 => {
                    let byte = temp_buf[0];
                    if byte == b'\n' || byte == b'\r' {
                        if !buffer.is_empty() {
                            break;
                        }
                    } else {
                        buffer.push(byte);
                    }
                }
                Ok(_) => continue,
                Err(ref e) if e.kind() == io::ErrorKind::TimedOut => {
                    return Err(ArcusError::Timeout);
                }
                Err(e) => return Err(ArcusError::Io(e)),
            }
        }
        
        Ok(String::from_utf8_lossy(&buffer).to_string())
    }

    pub fn get_position(&mut self, axis: char) -> Result<i32, ArcusError> {
        self.send_command(&format!("P{}", axis))?;
        let resp = self.read_response()?;
        // Response format example: "1000"
        resp.trim().parse::<i32>().map_err(|_| ArcusError::InvalidResponse(resp))
    }

    pub fn move_to(&mut self, axis: char, position: i32) -> Result<(), ArcusError> {
        // Absolute move
        self.send_command(&format!("{}{}", axis, position))?;
        Ok(())
    }

    pub fn is_moving(&mut self) -> Result<bool, ArcusError> {
        // Check status, implementation depends on specific Arcus model
        // Assuming "MST" returns status bitmask
        self.send_command("MST")?;
        let resp = self.read_response()?;
        let status = resp.trim().parse::<i32>().unwrap_or(0);
        // Bit 0 usually indicates moving
        Ok((status & 1) != 0)
    }
    
    pub fn set_high_speed(&mut self, axis: char, speed: i32) -> Result<(), ArcusError> {
        self.send_command(&format!("HS{}={}", axis, speed))?;
        Ok(())
    }
}
