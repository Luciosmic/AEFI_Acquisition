# ADR-002: Rust-Based Scan Engine for High-Performance Flyscan

## Status
Proposed

## Context
The AEFI Acquisition project requires a **Flyscan** mode (continuous acquisition during movement) to improve measurement speed and data density.
-   **Legacy Implementation**: Uses a Python `while` loop that polls position and triggers acquisition. This is limited by the Python Global Interpreter Lock (GIL) and scheduler, typically capping reliable performance at ~100Hz.
-   **User Goal**: Implement the Flyscan logic in **Rust** to achieve real-time performance, determinism, and potential publication value.
-   **Integration**: The system must still integrate with **PyMoDAQ** for the GUI, high-level orchestration, and data visualization.

## Decision

We will implement a **Hybrid Python/Rust Architecture** where the critical scanning loop and hardware control are offloaded to a Rust extension module.

### 1. The `aefi-scan-engine` (Rust Core)
We will create a Rust crate `aefi-scan-engine` exposed to Python via **PyO3**.

-   **Responsibilities**:
    -   **Hardware Control**: Direct communication with the Arcus motor controller (via `serialport` or FFI to DLL) to bypass Python overhead.
    -   **Real-Time Loop**: A high-performance loop that handles:
        1.  Sending motion commands (or monitoring continuous motion).
        2.  Reading position feedback at high frequency (>1kHz).
        3.  Triggering detectors (via hardware TTL or low-latency software trigger).
    -   **Data Buffering**: Storing results in a lock-free ring buffer.

### 2. Python Integration (Composition over Inheritance)
-   **Pattern**: **Hexagonal Architecture (Ports & Adapters)**. We will **NOT** inherit from PyMoDAQ's `CustomApp` or `CustomExt` for the core logic.
-   **Domain Layer**:
    -   **Design:** To be defined via **Event Storming**.
    -   **Expected Concepts:** `ScanPort` (input port) and `ScanObserver` (output port).
    -   Pure Python, no PyMoDAQ dependencies.
-   **Infrastructure Layer**:
    -   `RustScanAdapter`: Implements `ScanPort`. Wraps the `RustScanExecutor` binding.
    -   `PyMoDAQView`: A UI class that *uses* PyMoDAQ widgets (Plotting, DockArea) but does not drive the application logic. It subscribes to the Domain via `ScanObserver`.
-   **Workflow**:
    1.  `StudyService` (App Layer) calls `scan_port.execute(scan)`.
    2.  `RustScanAdapter` (Infra Layer) translates this to Rust calls.
    3.  Rust Engine executes the loop and calls back with data.
    4.  `RustScanAdapter` notifies `StudyService` and `PyMoDAQView` (via Observer).

### 3. Hardware Abstraction & Rust Role
-   **Direct Control**: The `RustScanExecutor` will take *exclusive* control of the Arcus motor serial port during the scan.
    -   *Constraint*: The standard PyMoDAQ plugin for Arcus must "release" or close the port before the Rust engine starts.
    -   *Solution*: The Rust engine manages the port lifecycle for the duration of the scan.
-   **Data Flow**:
    -   The Rust engine buffers data in memory.
    -   On completion (or periodically), it returns data to Python.
    -   The `RustScanAdapter` converts this to Domain entities (`ScanResults`).

## Consequences

### Positive
-   **Strict DDD**: Business logic is completely decoupled from the GUI framework.
-   **Testability**: The Domain and Application layers can be tested without PyMoDAQ or a GUI.
-   **Flexibility**: We can swap PyMoDAQ for another GUI or run headless without changing the core logic.
-   **Performance**: Retains the >1kHz loop speed of Rust.

### Negative
-   **Boilerplate**: Requires writing Adapter classes instead of just subclassing PyMoDAQ's convenience classes.
-   **Integration Effort**: We must manually wire PyMoDAQ widgets to our Domain events instead of getting "magic" connections.

## Implementation Strategy
1.  **Prototype**: Create a minimal Rust module that connects to the Arcus motor and performs a simple "move and read" loop.
2.  **Benchmark**: Compare the loop frequency of the Rust prototype vs. the legacy Python code.
3.  **Integrate**: Wrap the prototype in a PyMoDAQ plugin structure.
