# EFImagingBench - Overall Architecture

## Architecture Overview

The EFImagingBench application follows a **layered architecture** with clear separation of concerns, implementing the pattern:

```
Controller → Manager → MetaManager ↔ UI
```

This design ensures:
- **Separation of concerns** between hardware control, business logic, coordination, and presentation
- **Signal-based communication** using PyQt5 signals/slots for loose coupling
- **Thread-safe operations** for concurrent acquisition and motion control
- **Mode-based behavior** supporting both exploration and export workflows

## Architecture Diagram

![Overall Architecture](overall_architecture.puml)

## Architectural Layers

### 1. Presentation Layer (UI)

**Component:** `EFImagingBench_GUI` (PyQt5)

**Responsibilities:**
- User interaction and input validation
- Real-time visualization of position and acquisition data
- Tab-based organization:
  - Axes Control Tab
  - Motor Parameters Tab
  - Acquisition Tab
  - Advanced Settings Tab
  - Main Tab (experimental combined view)

**Communication:**
- Sends commands and configuration to MetaManager
- Receives status updates and data via PyQt signals

### 2. Coordination Layer

**Component:** `MetaManager`

**Responsibilities:**
- **Central coordinator** for all subsystems
- Manages lifecycle of sub-managers (StageManager, AcquisitionManager)
- Provides unified public API for external clients (UI, scripts)
- Relays important signals from sub-managers to UI
- Coordinates complex workflows (e.g., synchronized scan + acquisition)
- Maintains global application state and mode

**Key Methods:**
- `start_scan_and_acquire()` - Coordinate motion and acquisition
- `move_to()`, `home_lock()` - Motion control delegation
- `start_acquisition()`, `stop_acquisition()` - Acquisition control delegation
- `inject_scan_batch()` - Scan trajectory execution
- `get_latest_position_samples()` - Position data access

### 3. Domain Management Layer

#### StageManager

**Responsibilities:**
- Motion control and trajectory execution
- Scan pattern generation (2D scans, serpentine patterns)
- Position buffering and tracking
- Homing management and monitoring
- Command queue management (normal and priority queues)
- Mode-based operation (IDLE, SCANNING, HOMING)

**Key Features:**
- Thread-safe command queue
- Position buffer with exploration/export modes
- Scan trajectory segmentation
- Wait-for-move synchronization
- Error handling and recovery

**Modules Used:**
- `Scan2D Module` - Scan pattern generation
- `DataBuffer Module` - Position buffering
- `Geometrical Parameters Module` - Coordinate conversions

#### AcquisitionManager

**Responsibilities:**
- Continuous data acquisition in separate thread
- Mode management (exploration vs export)
- Configuration updates with automatic pause/resume
- CSV export coordination
- Data buffering and signal emission
- Hardware synchronization (DDS, ADC, gains)

**Key Features:**
- Adaptive behavior based on mode
- Thread-safe configuration updates
- Automatic pause during parameter changes (exploration mode)
- Sample-based data structure
- Status tracking (STOPPED, RUNNING, PAUSED, ERROR)

**Modules Used:**
- `DataBuffer Module` - Acquisition buffering
- `ADC Converter` - Raw data conversion
- `CSV Exporter` - Data export

### 4. Hardware Control Layer

#### ArcusPerformax4EXStageController

**Hardware:** Arcus Performax 4EX motion controller (X/Y stages)

**Responsibilities:**
- Low-level motion commands via pylablib
- Axis parameter configuration (speed, acceleration)
- Position and status queries
- Homing operations
- Emergency stop handling

**Key Features:**
- Uses pylablib for robust hardware communication
- Homing service integration
- Position tolerance checking
- Wait-for-move with timeout

#### AD9106_ADS131A04_SerialCommunicator

**Hardware:** 
- AD9106 (DDS/DAC for signal generation)
- ADS131A04 (4-channel ADC for acquisition)

**Responsibilities:**
- Serial communication protocol
- DDS configuration (frequency, phase, amplitude)
- ADC configuration (timing, reference, gain)
- Raw data acquisition
- Command/response handling

### 5. Support Modules

| Module | Purpose |
|--------|---------|
| **DataBuffer Module** | Ring buffer for position and acquisition samples |
| **Scan2D Module** | 2D scan pattern generation and configuration |
| **ADC Converter** | Raw ADC value conversion and gain synchronization |
| **CSV Exporter** | Data export to CSV files |
| **Homing Service** | Homing state management and monitoring |
| **Geometrical Parameters Module** | Coordinate system conversions (increments ↔ cm) |

## Communication Patterns

### Signal Flow (PyQt5 Signals)

```
UI → MetaManager → Manager → Controller
                ↓
            [Signals]
                ↓
UI ← MetaManager ← Manager ← Controller
```

**Key Signals:**
- `position_updated` - Real-time position feedback
- `data_ready` - New acquisition sample available
- `status_changed` - Component status updates
- `error_occurred` - Error notifications
- `scan_finished` - Scan completion
- `mode_changed` - Mode transitions

### Command Flow

1. **UI** sends user command to **MetaManager**
2. **MetaManager** delegates to appropriate **Manager**
3. **Manager** translates to low-level commands for **Controller**
4. **Controller** executes hardware operations
5. Feedback flows back up through signals

## Operating Modes

### Exploration Mode
- Interactive parameter tuning
- Automatic pause/resume during configuration changes
- Ring buffer for recent data
- Real-time visualization

### Export Mode
- Fixed configuration
- Continuous data logging
- CSV export
- Production-ready data buffering

## Thread Safety

- **Command Queue:** Thread-safe queue for motion commands
- **Data Buffers:** Protected access to position and acquisition buffers
- **Configuration Updates:** Atomic updates with pause/resume
- **Signal Emission:** Qt signal/slot mechanism ensures thread safety

## Design Principles

1. **Layered Architecture:** Clear separation between UI, coordination, domain logic, and hardware
2. **Dependency Inversion:** Managers depend on abstract interfaces, not concrete hardware
3. **Single Responsibility:** Each component has a well-defined purpose
4. **Signal-Based Communication:** Loose coupling via PyQt signals
5. **Mode-Based Behavior:** Adaptive behavior based on application mode
6. **Thread Safety:** Careful synchronization for concurrent operations

## Key Workflows

### Synchronized Scan + Acquisition

```
UI → MetaManager.start_scan_and_acquire()
        ↓
    MetaManager coordinates:
        ↓                    ↓
   StageManager      AcquisitionManager
   (scan trajectory)  (continuous acquisition)
        ↓                    ↓
   Position samples   Acquisition samples
        ↓                    ↓
    MetaManager (correlation)
        ↓
    UI (visualization)
```

### Homing Workflow

```
UI → MetaManager.home_lock(axis)
        ↓
    StageManager.home_lock(axis)
        ↓
    Controller.home(axis)
        ↓
    HomingService (monitoring)
        ↓
    Signals: homing_complete
```

## Future Considerations

- **Plugin Architecture:** Support for additional hardware modules
- **State Machine:** Formal state management for complex workflows
- **Event Sourcing:** Audit trail for all commands and events
- **Configuration Management:** Persistent configuration profiles
- **Remote Control:** API for external control and monitoring
