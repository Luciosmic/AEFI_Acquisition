# Analysis: Integrating Rust Scan Engine with DDD

## Context
The user wants to implement a high-performance Flyscan engine using Rust, integrated into a Python application that strictly follows Domain-Driven Design (DDD) and Hexagonal Architecture. The user previously expressed interest in PyMoDAQ's "Extension" pattern but emphasized that DDD is the priority.

## The Challenge
*   **DDD Goal**: The Domain Layer (`Study`, `SpatialScan`) must remain pure and drive the business logic.
*   **Performance Goal**: The scanning loop must run in Rust (>1kHz) to avoid Python GIL issues.
*   **Integration Goal**: The UI should ideally fit into PyMoDAQ's ecosystem (Dashboard, Dockable).

## Option 1: "Extension-First" (Typical PyMoDAQ Pattern)
In this pattern, the PyMoDAQ Extension (a GUI class) acts as the controller.
*   **Flow**: User clicks "Start" in Extension UI -> Extension configures Rust Engine -> Extension calls `engine.start()` -> Extension receives data -> Extension updates UI.
*   **Role of Domain**: The `Study` entity might be used just to store parameters, or ignored entirely in favor of UI settings.
*   **Pros**: Fits perfectly into PyMoDAQ examples; easy to implement "Live View".
*   **Cons**: **Violates DDD**. The business logic (sequencing scans, managing study state) leaks into the UI/Infrastructure layer. The Domain Model becomes "Anemic".

## Option 2: "DDD-First" (Hexagonal Architecture)
In this pattern, the Application Service drives the process.
*   **Flow**: User clicks "Start" in UI -> UI calls `StudyService.run_study()` -> Service retrieves `Study` -> Service calls `ScanPort.execute_scan(scan)` -> `RustScanAdapter` (Infra) calls Rust Engine -> Results returned to Service -> Service updates `Study`.
*   **Role of Domain**: Central. `Study` enforces rules (e.g., "cannot start 2D scan if 1D scan failed").
*   **Pros**: **Strict DDD compliance**. Decoupled from PyMoDAQ (easier to test, swap engines).
*   **Cons**: Harder to integrate "Live View" (real-time plotting) because the Service is "blocking" or needs a complex callback mechanism to update the UI during execution.

## Proposed Solution: Hybrid (DDD Core + Reactive UI)
We can achieve both by using **Ports & Adapters** with an **Observer Pattern** for the UI.

### Architecture
1.  **Domain Layer**:
    *   `Study` (Aggregate): Manages state (`PENDING` -> `RUNNING`).
    *   `ScanPort` (Interface): Defines `execute_scan(scan: Scan, observer: ScanObserver)`.
2.  **Application Layer**:
    *   `StudyService`: Orchestrates the workflow.
3.  **Infrastructure Layer**:
    *   `RustScanAdapter`: Implements `ScanPort`. Wraps the `RustScanExecutor`.
    *   **PyMoDAQ Extension (UI)**: Acts as the *Client* of the `StudyService` and an *Observer* of the `ScanPort`.

### Workflow
1.  **Setup**: User configures `Study` in PyMoDAQ Extension.
2.  **Trigger**: User clicks "Run". Extension calls `study_service.execute_next_scan(study_id)`.
3.  **Execution**:
    *   Service calls `scan_port.execute_scan(scan, observer=ui_callback)`.
    *   `RustScanAdapter` converts `Scan` to Rust params.
    *   **Rust Engine** runs the loop.
    *   **Real-time**: Rust Engine calls back to Python -> Adapter calls `observer.on_data_point()` -> Extension updates PyMoDAQ Viewer.
4.  **Completion**: Rust returns full results. Adapter returns `ScanResults`. Service updates `Study`.

### Why this fits
*   **DDD**: The `Study` aggregate controls the lifecycle. The `StudyService` orchestrates.
*   **Performance**: The loop is in Rust.
*   **UX**: The PyMoDAQ Extension visualizes data in real-time via the Observer pattern.

## Recommendation
Adopt the **Hybrid DDD approach**.
1.  Define `ScanPort` in Domain.
2.  Implement `RustScanAdapter` in Infrastructure.
3.  Build the PyMoDAQ Extension as a thin UI layer that delegates to `StudyService`.
