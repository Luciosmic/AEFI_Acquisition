
```mermaid
graph TB
    subgraph "Application Layer - AEFI Acquisition System"
        
        subgraph "Acquisition Services"
            StabilityAcq[StabilityAcquisitionService]
            ManualScan[ManualScanService]
            AutoScan[AutomaticScanService]
            CustomScan[CustomScanService]
        end
        
        subgraph "Measurement Management"
            RefMgmt[ReferenceMeasurementService]
            DataAgg[DataAggregationService]
        end
        
        subgraph "Motion Control"
            MotionCtrl[MotionControlService]
        end
        
        subgraph "Configuration"
            ScanConfig[ScanConfigurationService]
            ParamMgmt[ParameterManagementService]
        end
        
        subgraph "Persistence"
            DataPersist[DataPersistenceService]
        end
    end

    %% StabilityAcquisitionService
    StabilityAcq -->|startTimedAcquisition| StabilityAcq
    StabilityAcq -->|stopAcquisition| StabilityAcq
    StabilityAcq -->|acquireForDuration| StabilityAcq
    
    %% ManualScanService
    ManualScan -->|acquireAtCurrentPosition| ManualScan
    ManualScan -->|moveAndAcquire| ManualScan
    ManualScan -->|updateParametersBeforeNext| ManualScan
    ManualScan -->|finalizeManualScan| ManualScan
    
    %% AutomaticScanService
    AutoScan -->|configureScanPattern| AutoScan
    AutoScan -->|executeSerpentineScan| AutoScan
    AutoScan -->|executeCombScan| AutoScan
    AutoScan -->|executeStepScan| AutoScan
    AutoScan -->|executeFlyScan| AutoScan
    
    %% CustomScanService
    CustomScan -->|defineCustomSequence| CustomScan
    CustomScan -->|addScanPoint| CustomScan
    CustomScan -->|executeCustomScan| CustomScan
    
    %% ReferenceMeasurementService
    RefMgmt -->|setAsReference| RefMgmt
    RefMgmt -->|getReferenceMeasurement| RefMgmt
    RefMgmt -->|computeRelativeMeasurement| RefMgmt
    
    %% DataAggregationService
    DataAgg -->|aggregateMeasurements| DataAgg
    DataAgg -->|structureAcquisitionData| DataAgg
    DataAgg -->|linkMeasurementsToPositions| DataAgg
    
    %% MotionControlService
    MotionCtrl -->|moveToPosition| MotionCtrl
    MotionCtrl -->|getCurrentPosition| MotionCtrl
    MotionCtrl -->|calibrateAxes| MotionCtrl
    
    %% ScanConfigurationService
    ScanConfig -->|createScanConfiguration| ScanConfig
    ScanConfig -->|validateScanPattern| ScanConfig
    ScanConfig -->|saveScanTemplate| ScanConfig
    
    %% ParameterManagementService
    ParamMgmt -->|updateFrequency| ParamMgmt
    ParamMgmt -->|updateAcquisitionParams| ParamMgmt
    ParamMgmt -->|snapshotParameters| ParamMgmt
    
    %% DataPersistenceService
    DataPersist -->|persistAcquisition| DataPersist
    DataPersist -->|loadAcquisition| DataPersist
    DataPersist -->|exportToFormat| DataPersist

    %% Relations entre services
    ManualScan -.->|uses| MotionCtrl
    ManualScan -.->|uses| RefMgmt
    ManualScan -.->|uses| DataAgg
    ManualScan -.->|uses| ParamMgmt
    
    AutoScan -.->|uses| MotionCtrl
    AutoScan -.->|uses| ScanConfig
    AutoScan -.->|uses| RefMgmt
    AutoScan -.->|uses| DataAgg
    
    CustomScan -.->|uses| MotionCtrl
    CustomScan -.->|uses| ParamMgmt
    CustomScan -.->|uses| DataAgg
    CustomScan -.->|uses| RefMgmt
    
    StabilityAcq -.->|uses| RefMgmt
    StabilityAcq -.->|uses| DataAgg
    
    DataAgg -.->|uses| DataPersist
    
    style StabilityAcq fill:#e1f5ff
    style ManualScan fill:#e1f5ff
    style AutoScan fill:#e1f5ff
    style CustomScan fill:#e1f5ff
    style RefMgmt fill:#fff4e1
    style DataAgg fill:#fff4e1
    style MotionCtrl fill:#f0e1ff
    style ScanConfig fill:#e1ffe1
    style ParamMgmt fill:#e1ffe1
    style DataPersist fill:#ffe1e1
    ```