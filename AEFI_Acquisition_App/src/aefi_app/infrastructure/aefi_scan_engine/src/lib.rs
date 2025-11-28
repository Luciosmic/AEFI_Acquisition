mod arcus_driver;
use arcus_driver::ArcusController;
use pyo3::prelude::*;
use std::time::Duration;
use std::thread;

/// A Python module implemented in Rust.
#[pymodule]
fn aefi_scan_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<RustScanExecutor>()?;
    Ok(())
}

#[pyclass]
struct RustScanExecutor {
    port_name: String,
    baud_rate: u32,
    controller: Option<ArcusController>,
}

#[pymethods]
impl RustScanExecutor {
    #[new]
    fn new(port_name: String, baud_rate: u32) -> Self {
        RustScanExecutor {
            port_name,
            baud_rate,
            controller: None,
        }
    }

    fn connect(&mut self) -> PyResult<String> {
        match ArcusController::connect(&self.port_name, self.baud_rate) {
            Ok(ctrl) => {
                self.controller = Some(ctrl);
                Ok(format!("Connected to {} at {}", self.port_name, self.baud_rate))
            }
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string())),
        }
    }

    fn move_axis(&mut self, axis: char, position: i32) -> PyResult<String> {
        if let Some(ctrl) = &mut self.controller {
            ctrl.move_to(axis, position)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
            Ok(format!("Moved {} to {}", axis, position))
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Not connected"))
        }
    }

    fn start_scan(&mut self, x_min: i32, x_max: i32, step: i32) -> PyResult<Vec<(i32, i32)>> {
        if let Some(ctrl) = &mut self.controller {
            let mut results = Vec::new();
            let mut current_x = x_min;

            // Move to start
            ctrl.move_to('x', x_min)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
            
            // Wait for arrival at start (simple polling for now)
            while let Ok(pos) = ctrl.get_position('x') {
                if (pos - x_min).abs() < 10 { break; }
                thread::sleep(Duration::from_millis(10));
            }

            // Scan loop
            while current_x <= x_max {
                // 1. Move to next position
                ctrl.move_to('x', current_x)
                    .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

                // 2. Busy wait / Poll for position (Critical loop)
                // In a real flyscan, we might not wait for full stop, but trigger when in window
                loop {
                    let pos = ctrl.get_position('x')
                        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
                    
                    if (pos - current_x).abs() < 5 {
                        // 3. Trigger Acquisition (Placeholder)
                        // In real impl: set TTL high, wait, set low
                        // For now, just record position
                        results.push((current_x, pos));
                        break;
                    }
                    // Ultra-short sleep to prevent CPU hogging, but keep high responsiveness
                    thread::sleep(Duration::from_micros(100)); 
                }

                current_x += step;
            }
            
            Ok(results)
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Not connected"))
        }
    }
}
