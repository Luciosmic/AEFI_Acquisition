from typing import List, Dict, Any
from application.services.scan_application_service.i_export_port import IExportPort

class MockExportPort(IExportPort):
    def __init__(self):
        self.points: List[Dict[str, Any]] = []
        self.is_open = False
        
    def configure(self, directory: str, filename: str, metadata: Dict[str, Any]) -> None:
        pass
        
    def start(self) -> None:
        self.is_open = True
        
    def write_point(self, data: Dict[str, Any]) -> None:
        if not self.is_open:
            # In a real scenario this might raise, but for simple mock we can just track it
            # or we can enforce start() being called.
            pass 
        self.points.append(data)
        
    def stop(self) -> None:
        self.is_open = False
