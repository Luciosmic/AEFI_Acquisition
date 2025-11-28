# Event Storming: AEFI Acquisition

## 1. Domain Description (User Input)
*   **Technique**: AEFI (Low freq electric field, measure perturbation).
*   **Setup**: Generator + Sensor move together on a column.
*   **Subject**: Objects (buried, different properties) + Background.
*   **Study**: Acquisition of data for a *specific object*.
*   **Scans**:
    *   **Patterns**: S-pattern (Snake), E-pattern.
    *   **Modes**: FlyScan (continuous), StepScan (stop-and-go).
    *   **Repetition**: Multiple scans for statistical average.
*   **Excitation**: X-dir, Y-dir, Circular.
*   **Frequency**: Single frequency usually.
    *   **Pseudo-Sweep**: `Go to Ref -> Change Freq -> Acquire Ref -> Go to Measure -> Acquire`.

## 2. Key Concepts (DDD Analysis)

### Aggregates (The "Things")
*   **`Study`**: The root. Represents the analysis of **one specific object**. It holds all scans and metadata for that object.
*   **`ExperimentObject`**: Value Object describing the physical object (Size, Depth, Properties).
*   **`Scan`**: A single execution of a movement pattern.

### Value Objects (The "Settings")
*   **`ScanPattern`**: Enum (`Snake`, `E_Pattern`).
*   **`ScanMode`**: Enum (`FlyScan`, `StepScan`).
*   **`ExcitationConfig`**: Enum (`X`, `Y`, `Circular`).
*   **`FrequencySequence`**: The complex "Ref -> Measure" workflow logic.

### Commands (User Actions)
*   `CreateStudy(object_name, description)`
*   `ConfigureExcitation(direction, frequency)`
*   `AddScan(pattern, mode, area)`
*   `StartScan(scan_id)`
*   `RunFrequencySequence(frequencies_list)`

### Domain Events (Facts that Happened)
*   `StudyCreated`
*   `ExcitationConfigured`
*   `ScanStarted`
*   `PositionReached` (StepScan) / `BufferFilled` (FlyScan)
*   `DataPointAcquired`
*   `ScanCompleted`
*   `ScanFailed`

## 4. Device & Configuration (Physical Domain)
*   **Configuration**: `OneSide` (Source/Sensor same side) vs `OppositeSide`.
*   **Current Setup**: `4SphereSquared`
    *   **Generator**: 4 spheres on square vertices driven by 2 DDS channels (differential pairs).
        *   `Out1`/`Out2` = DDS1 / DDS1_bar
        *   `Out3`/`Out4` = DDS2 / DDS2_bar
    *   **Sensor**: 3-axial sensor at center.
*   **Reference Frames**:
    *   **Bench Frame**: The absolute reference (Motors). Home = (0,0).
    *   **Sensor Frame**: Rotated relative to Bench Frame.
        *   **Rotation Logic**: Quaternion-based.
        *   **Standard Angles**: $\theta_x = -45^\circ$, $\theta_y \approx 35.26^\circ$ ($\arctan(1/\sqrt{2})$), $\theta_z = 0^\circ$.
        *   **Transformation**: $E_{probe} = R_z R_y R_x E_{bench}$.
*   **Excitation Modes (Phase Logic)**:
    *   `X-Dir`: DDS1=0°, DDS2=0° (In Phase).
    *   `Y-Dir`: DDS1=0°, DDS2=180° (Opposition).
    *   `Circ+`: DDS1=0°, DDS2=90° (Quadrature +).
    *   `Circ-`: DDS1=0°, DDS2=270° (Quadrature -).
*   **Z-Axis**: Currently fixed/manual, potential for future motorization.

## 5. Calibration Process
*   **Goal**: Determine the precise orientation of the sensor relative to the bench.
*   **Workflow**:
    *   `StartCalibration` -> Move to known field configuration -> Measure -> Compute Rotation -> `UpdateFrameRotation`.
*   **Outcome**: Updates the `FrameRotation` configuration (quaternion) used for real-time correction.

## 6. Context Map: AEFI Suite
The Acquisition App is one part of the **AEFI Suite**.
*   **Object Management Context** (External):
    *   Responsible for the **Object Database** (CRUD on objects).
    *   Provides unique `ObjectId` and object properties.
*   **Acquisition Context** (This App):
    *   **Uses** `ObjectId` to link a `Study` to a physical object.
    *   **Port**: `ObjectRepository` (Interface) to fetch object details by ID.
    *   *Constraint*: The Acquisition app does *not* modify the Object Database, it only reads from it.

## 3. The "Frequency Sequence" Challenge
The user described a complex workflow:
> "go to reference position -> change frequency, acquire reference data -> go to measurement point -> acquire data"

This is a **Process Manager** (or Saga) in DDD. It orchestrates multiple smaller steps.
*   It's not just a simple "Scan". It's a **Measurement Protocol**.
