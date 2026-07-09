# Architecture Diagrams - Index

This directory contains PlantUML diagrams documenting the Scan System architecture.

## Overview

### [architecture_overview.puml](file:///Users/luis/Library/CloudStorage/Dropbox/Luis/1%20PROJETS/1%20-%20THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/Legacy_AEFI_Acquisition/EFImagingBench_App/docs/diagrams/architecture_overview.puml)

**High-level architecture overview** showing:
- All layers (Presentation, Application, Domain, Infrastructure)
- Key components and their relationships
- Data flow and event flow
- Design patterns used (Hexagonal, DDD, Event-Driven)

**Use this diagram** to get a bird's-eye view of the system.

---

## Domain Layer

### [domain/domain_model_complete.puml](file:///Users/luis/Library/CloudStorage/Dropbox/Luis/1%20PROJETS/1%20-%20THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/Legacy_AEFI_Acquisition/EFImagingBench_App/docs/diagrams/domain/domain_model_complete.puml)

**Complete domain model** showing:
- Aggregates: `StepScan`
- Value Objects: `VoltageMeasurement`, `ScanPointResult`, `Position2D`, `StepScanConfig`, etc.
- Domain Services: `MeasurementStatisticsService`, `ScanTrajectoryFactory`
- Domain Events: `ScanStarted`, `ScanPointAcquired`, `ScanCompleted`, etc.
- **Statistical fields** in `VoltageMeasurement` (std_dev_*)
- **Auto-completion logic** in `StepScan`

**Use this diagram** to understand the domain model and business logic.

### [domain/domain_model.puml](file:///Users/luis/Library/CloudStorage/Dropbox/Luis/1%20PROJETS/1%20-%20THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/Legacy_AEFI_Acquisition/EFImagingBench_App/docs/diagrams/domain/domain_model.puml)

**Simplified domain model** (older version, less detailed).

---

## Application Layer

### [application/scan_execution_event_driven.puml](file:///Users/luis/Library/CloudStorage/Dropbox/Luis/1%20PROJETS/1%20-%20THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/Legacy_AEFI_Acquisition/EFImagingBench_App/docs/diagrams/application/scan_execution_event_driven.puml)

**Sequence diagram** showing the complete scan execution flow:
- Initialization and configuration
- Trajectory generation
- Execution loop (Motion → Acquisition → Statistics → Domain Update)
- **Event dispatching** to subscribers (Export, UI)
- **Domain auto-completion** logic
- Finalization

**Use this diagram** to understand the runtime behavior and event flow.

### [application/export_architecture.puml](file:///Users/luis/Library/CloudStorage/Dropbox/Luis/1%20PROJETS/1%20-%20THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/Legacy_AEFI_Acquisition/EFImagingBench_App/docs/diagrams/application/export_architecture.puml)

**Class diagram** showing the export architecture:
- `ExportEventSubscriber` pattern
- `IExportPort` interface
- Infrastructure implementations: `HDF5Exporter`, `CSVExporter`
- Event handling logic
- Decoupling between scan and export

**Use this diagram** to understand how export is integrated via events.

### [application/scan_application_service_sequence.puml](file:///Users/luis/Library/CloudStorage/Dropbox/Luis/1%20PROJETS/1%20-%20THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/Legacy_AEFI_Acquisition/EFImagingBench_App/docs/diagrams/application/scan_application_service_sequence.puml)

**Sequence diagram** (older version, without export subscriber).

### [application/application_layer.puml](file:///Users/luis/Library/CloudStorage/Dropbox/Luis/1%20PROJETS/1%20-%20THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/Legacy_AEFI_Acquisition/EFImagingBench_App/docs/diagrams/application/application_layer.puml)

**Application layer overview** showing services and migration strategy from legacy `MetaManager`.

---

## Key Architectural Decisions

### Domain State Management

- **`StepScan` aggregate** manages its own state
- **Auto-completion**: When `len(_points) >= _expected_points`, the aggregate automatically calls `complete()` and emits `ScanCompleted`
- **Application layer** does NOT decide completion, it just orchestrates

### Statistics Calculation

- **`MeasurementStatisticsService`** (Domain Service) calculates mean and std_dev
- **`VoltageMeasurement`** has optional `std_dev_*` fields:
  - `None` for raw measurements
  - `0.0` when N=1 (single measurement, no variability)
  - `> 0.0` when N>1 (multiple measurements averaged)

### Event-Driven Export

- **`ExportEventSubscriber`** listens to domain events
- Reacts to `ScanStarted` → configure and start export
- Reacts to `ScanPointAcquired` → write data point
- Reacts to `ScanCompleted` → close file
- **Decoupled**: Export is a side-effect, not part of scan logic
- **Extensible**: Easy to add more subscribers (UI, logging, etc.)

### Hexagonal Architecture

- **Ports** (`IMotionPort`, `IAcquisitionPort`, `IExportPort`) define interfaces
- **Adapters** (infrastructure) implement ports
- **Domain** is isolated from infrastructure
- **Application** orchestrates domain + infrastructure via ports

---

## Diagram Conventions

- **Blue boxes**: Application Layer
- **Green boxes**: Domain Layer
- **Yellow boxes**: Infrastructure Layer
- **Dashed arrows**: Event flow or dependency
- **Solid arrows**: Direct calls or composition
- **`<<Aggregate Root>>`**: DDD Aggregate
- **`<<Value Object>>`**: DDD Value Object
- **`<<Domain Service>>`**: DDD Domain Service
- **`<<Domain Event>>`**: DDD Domain Event

---

## Viewing Diagrams

To view PlantUML diagrams:

1. **VS Code**: Install "PlantUML" extension
2. **IntelliJ**: Built-in support
3. **Online**: [PlantUML Web Server](http://www.plantuml.com/plantuml/uml/)
4. **Command line**: `plantuml diagram.puml` (generates PNG/SVG)

---

## Maintenance

When updating the code, remember to update the corresponding diagrams to keep documentation in sync.
