from abc import ABC, abstractmethod
from typing import List
from acquisition_sample import AcquisitionSample

class IAcquisitionDataRepository(ABC):
    """
    Interface for persisting acquisition data.
    Follows DDD Repository pattern.
    """
    
    @abstractmethod
    def save(self, scan_id: str, data: List[AcquisitionSample]) -> None:
        """
        Persist a batch of acquisition samples for a specific scan.
        
        Args:
            scan_id: Unique identifier of the scan
            data: List of AcquisitionSample objects to save
        """
        pass
    
    @abstractmethod
    def find_by_scan(self, scan_id: str) -> List[AcquisitionSample]:
        """
        Retrieve all acquisition samples for a specific scan.
        
        Args:
            scan_id: Unique identifier of the scan
            
        Returns:
            List of AcquisitionSample objects
        """
        pass
