# ADR-001: Architecture & Technology Stack for AEFI Acquisition

## Status
Proposed

## Context
The AEFI Acquisition software needs a major refactor to address architectural limitations in the legacy codebase.
-   **Current State:** Legacy code is "bottom-up", tightly coupled to hardware, and difficult to maintain.
-   **Goals:** Implement a **DDD (Domain-Driven Design)** and **SOLID** architecture.
-   **Key Requirement:** Support for **Flyscan** (continuous acquisition during movement), which is critical for performance but not natively supported by the standard PyMoDAQ step-by-step scanner.
-   **Assets:**
    -   `_AEFI_numerical_solver`: Contains a clean DDD domain model (`Study`, `SpatialScan`).
    -   `Legacy_AEFI_Acquisition`: Contains working hardware drivers (`Arcus`, `Agilent`, `Narda`).
    -   `PyMoDAQ`: A modular data acquisition framework proposed as the infrastructure layer.

## Decision

We will adopt a **Hexagonal Architecture (Ports & Adapters)** with **PyMoDAQ** as the primary infrastructure provider.

### 1. Architectural Style: Hexagonal + DDD
-   **Domain Layer (Core):**
    -   **Design:** To be defined via **Event Storming** specifically for the Acquisition context.
    -   **Inspiration:** Will follow the architectural patterns of `_AEFI_numerical_solver` (Aggregates, Value Objects) but **NOT** necessarily its specific models.
    -   **Responsibility:** Pure business logic, state management of the acquisition process. *No hardware dependencies.*

-   **Application Layer:**
    -   **Use Cases:** `CreateStudy`, `RunScan`, `ExportData`.
    -   **Ports (Interfaces):**
        -   `ScanExecutor`: Interface for running a scan.
        -   `ResultRepository`: Interface for saving data.

-   **Infrastructure Layer:**
    -   **Adapters:**
        -   `PyMoDAQAdapter`: Implements `ScanExecutor`. It translates domain `SpatialScan` objects into PyMoDAQ commands.
        -   `Hdf5ExportAdapter`: Implements `ResultRepository`. Uses PyMoDAQ's `H5Saver` to write the `Study` and its scans to an HDF5 file. This file serves as the persistence mechanism for the external database.

### 2. Technology Stack
-   **Language:** Python 3.10+
-   **Framework:** **PyMoDAQ** (for hardware control and GUI).
-   **Hardware Abstraction:** PyMoDAQ Control Modules (`DAQ_Move`, `DAQ_Viewer`).
-   **Legacy Integration:** Legacy drivers will be wrapped as **PyMoDAQ Plugins** (`pymodaq_plugins_aefi`).

### 3. Flyscan Strategy
Standard PyMoDAQ scans are step-by-step ("Move -> Stop -> Acquire"). To support Flyscan:
-   We will create a **Custom PyMoDAQ Extension** (e.g., `AEFI_Flyscan_Extension`).
-   **Mechanism:**
    -   **Software Flyscan (Initial):** The extension will command the motor to move to the end position (non-blocking) and spawn a thread to continuously poll/trigger the detector and record positions while `is_moving()` is true.
    -   **Hardware Flyscan (Future):** If hardware permits, the extension will configure hardware triggers (Motor Output -> Scope Input).
-   This extension will be invoked by the `PyMoDAQAdapter` when the domain `SpatialScan` is configured for continuous mode.

## Consequences

### Positive
-   **Decoupling:** Domain logic is completely isolated from PyMoDAQ and hardware. This allows running "Virtual Scans" (simulations) using the exact same domain logic by simply swapping the `ScanExecutor` adapter.
-   **Reusability:** Legacy drivers are reused but isolated behind standard PyMoDAQ interfaces.
-   **Testability:** The domain can be unit-tested without any hardware. The `PyMoDAQAdapter` can be integration-tested with mock plugins.
-   **Flexibility:** Flyscan logic is encapsulated in a specific extension, not scattered across the app.

### Negative
-   **Complexity:** Requires mapping domain objects (`SpatialScan`) to PyMoDAQ configurations.
-   **PyMoDAQ Learning Curve:** Developing a custom extension requires deep knowledge of PyMoDAQ's internal signaling and threading.
-   **Performance:** Software flyscan (polling) depends on Python's scheduler and communication latency, which might be less precise than hardware triggering.

## Compliance
-   **SOLID:**
    -   **SRP:** Each layer has a single responsibility.
    -   **DIP:** High-level policy (Domain) does not depend on low-level details (PyMoDAQ).
    -   **OCP:** New hardware can be added via new PyMoDAQ plugins without changing the core.
