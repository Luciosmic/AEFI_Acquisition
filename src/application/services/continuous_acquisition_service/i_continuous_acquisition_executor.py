# Compatibility shim — canonical definition has moved to ports/
from .ports.i_continuous_acquisition_executor import IContinuousAcquisitionExecutor, ContinuousAcquisitionConfig
__all__ = ["IContinuousAcquisitionExecutor", "ContinuousAcquisitionConfig"]
