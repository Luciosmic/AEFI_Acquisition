"""
Domain: Scan point result value object.

Responsibility:
    Represent the output data at one point in a parametric scan.
    Scan-level concept independent of execution strategy.

Rationale:
    This represents "result at one variation point" in scan abstraction.
    Conceptually different from JobResult (execution-level concept).

    Key distinction:
    - JobResult: output of executing one atomic job
    - ScanPointResult: data at one point in a parametric variation

    Structurally similar, but semantically distinct roles:
    - Scan domain thinks: "result at position (x, y, z)"
    - Execution domain thinks: "result of running job #42"

    This decoupling allows:
    - Scans to be independent of execution strategy (parallel jobs, streaming, etc.)
    - Extension to other scan types (frequency, permittivity, geometry)
    - Clean separation between variation strategy and execution mechanics

Design:
    - Immutable value object (frozen dataclass)
    - Contains computed values and metadata
    - No dependencies on job or execution concepts
    - Convertible to/from JobResult (mapping in application layer)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..job.job_execution_metadata import JobExecutionMetadata
from ..job.job_solver_metadata import SolverMetadata
from ..job.job_mesh_metadata import JobMeshMetadata


@dataclass(frozen=True)
class ScanPointResult:
    """Value object: result data at one point in a parametric scan.

    Represents the output for one set of variation values in a scan.
    Independent of how the computation was executed.

    Attributes
    ----------
    values : Dict[str, float]
        Computed values from the simulation.
        Example: {
            "V_x_pos_real": 1.23,
            "V_x_pos_imag": 0.45,
            "V_x_neg_real": 2.34,
            "V_x_neg_imag": -0.12,
            "V_y_pos_real": 0.56,
            "V_y_pos_imag": 0.78,
            ...
        }
        Naming convention: V_{electrode_identifier}_{real|imag}
        Typically 12 components (6 electrodes × 2 components: real + imag).
    execution_metadata : JobExecutionMetadata
        Execution-related metadata (identifier, date, hour, duration).
        Note: Name reflects current implementation, may be renamed to
        ExecutionMetadata in future to remove "Job" reference.
    solver_metadata : SolverMetadata
        Solver configuration and settings.
    mesh_metadata : JobMeshMetadata
        Mesh configuration and statistics.
        Note: May be renamed to MeshMetadata in future.

    Design
    ------
    Immutable value object. Pure data container for scan point output.
    Structurally similar to JobResult but serves different semantic role.

    Usage Context
    -------------
    - Used by SpatialScanResults (and future FrequencyScanResults, etc.)
    - Created by converting JobResult in application layer
    - Consumed by scan analysis and visualization

    CQS (Command-Query Separation)
    ------------------------------
    Commands: None (immutable value object, no state mutation)
    Queries: None (pure data container, access via attributes)
    """

    values: Dict[str, float]
    execution_metadata: JobExecutionMetadata
    solver_metadata: SolverMetadata
    mesh_metadata: JobMeshMetadata

    @classmethod
    def create(
        cls,
        values: Dict[str, float],
        execution_metadata: JobExecutionMetadata,
        solver_metadata: SolverMetadata,
        mesh_metadata: JobMeshMetadata | None = None
    ) -> ScanPointResult:
        """Factory method to create a ScanPointResult.

        CQS: Command (creates new instance).

        Parameters
        ----------
        values : Dict[str, float]
            Computed values from the simulation.
            Keys follow convention: V_{electrode_identifier}_{real|imag}
        execution_metadata : JobExecutionMetadata
            Execution metadata (identifier, timing).
        solver_metadata : SolverMetadata
            Solver configuration.
        mesh_metadata : JobMeshMetadata | None
            Optional mesh metadata. If None, creates empty JobMeshMetadata.

        Returns
        -------
        ScanPointResult
            New instance with computed values and metadata.
        """
        if mesh_metadata is None:
            mesh_metadata = JobMeshMetadata.create()

        return cls(
            values=values,
            execution_metadata=execution_metadata,
            solver_metadata=solver_metadata,
            mesh_metadata=mesh_metadata
        )

    @classmethod
    def from_job_result(cls, job_result) -> ScanPointResult:
        """Convert JobResult to ScanPointResult.

        Bridge between execution domain (Job) and scan domain (Scan).
        Used in application layer after job execution completes.

        Parameters
        ----------
        job_result : JobResult
            Result from job execution.

        Returns
        -------
        ScanPointResult
            Scan-level representation of the same data.

        Example
        -------
        >>> job_results = executor.run_jobs(...)
        >>> scan_results = [ScanPointResult.from_job_result(jr) for jr in job_results]
        >>> scan.mark_as_completed(scan_results)
        """
        return cls(
            values=job_result.values,
            execution_metadata=job_result.execution_metadata,
            solver_metadata=job_result.solver_metadata,
            mesh_metadata=job_result.mesh_metadata
        )

    def to_job_result(self):
        """Convert ScanPointResult to JobResult.

        Bridge for reconstructing Jobs from scan results.
        Used when Study needs to provide unified access to all simulations.

        Returns
        -------
        JobResult
            Execution-level representation of the same data.

        Example
        -------
        >>> for point_result in scan.results.point_results:
        >>>     job_result = point_result.to_job_result()
        >>>     job = Job.create(parameters=params, result=job_result)
        """
        # Import here to avoid circular dependency
        from ..job.job_result import JobResult

        return JobResult(
            values=self.values,
            execution_metadata=self.execution_metadata,
            solver_metadata=self.solver_metadata,
            mesh_metadata=self.mesh_metadata
        )
