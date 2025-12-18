from typing import List
from domain.models.aefi_device.repositories.i_acquisition_data_repository import IAcquisitionDataRepository
from domain.models.scan.events.scan_events import ScanPointAcquired
from domain.shared.events.domain_event import DomainEvent
import logging

logger = logging.getLogger(__name__)

class AcquisitionDataHandler:
    """
    Application Handler responsible for persisting acquisition data.
    Listens to domain events and uses the repository to save data.
    """
    
    def __init__(self, repository: IAcquisitionDataRepository):
        self.repository = repository
        
    def handle(self, event: DomainEvent) -> None:
        """
        Handle domain events.
        Specifically interested in ScanPointAcquired events.
        """
        if isinstance(event, ScanPointAcquired):
            self._handle_scan_point_acquired(event)
            
    def _handle_scan_point_acquired(self, event: ScanPointAcquired) -> None:
        try:
            # Extract sample from event
            # Assuming event.measurement corresponds to AcquisitionSample structure
            # or we map it here.
            
            # The event has 'measurement' which is 'VoltageMeasurement' (aliased as AcquisitionSample)
            # The event also needs a scan_id. 
            # Currently ScanPointAcquired might not have scan_id if it's just point data.
            # We might need to enrich the event or context.
            # For now, let's assume the event has what we need or we use a placeholder/context.
            
            # TODO: Ensure ScanPointAcquired has scan_id
            scan_id = str(getattr(event, 'scan_id', 'unknown_scan'))
            
            sample = event.measurement
            
            logger.debug(f"Persisting sample for scan {scan_id}")
            self.repository.save(scan_id, [sample])
            
        except Exception as e:
            logger.error(f"Error handling acquisition data persistence: {e}")
