"""
Tests for HDF5AcquisitionRepository (Diagram-Friendly)
"""
import shutil
from pathlib import Path
from datetime import datetime
import numpy as np

from infrastructure.persistence.hdf5_acquisition_repository import HDF5AcquisitionRepository
from domain.value_objects.acquisition.acquisition_sample import AcquisitionSample
from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest

class TestHDF5AcquisitionRepository(DiagramFriendlyTest):
    """Test HDF5 persistence with diagram generation."""
    
    def setUp(self):
        super().setUp()
        # Use a directory relative to this test file to avoid dispersion
        self.test_dir = Path(__file__).parent / "test_data"
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            
        # Calculate path relative to infrastructure for clearer logging
        # src/infrastructure/persistence/tests/test_data -> persistence/tests/test_data
        try:
            # Assuming structure src/infrastructure/...
            # We want to find the 'infrastructure' part in the path
            parts = self.test_dir.parts
            if 'infrastructure' in parts:
                idx = parts.index('infrastructure')
                rel_path = Path(*parts[idx+1:])
            else:
                rel_path = self.test_dir.name
        except Exception:
            rel_path = self.test_dir.name
        
        self.log_interaction("Test", "CREATE", "HDF5Repository", f"Initialize repository at {rel_path}", {"path": str(self.test_dir)})
        self.repo = HDF5AcquisitionRepository(base_path=str(self.test_dir))
        
    def tearDown(self):
        super().tearDown()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_save_and_find(self):
        """Test saving and retrieving samples."""
        scan_id = "scan_test_123"
        
        # Create sample
        sample = AcquisitionSample(
            timestamp=datetime.now(),
            voltage_x_in_phase=1.0, voltage_x_quadrature=0.1,
            voltage_y_in_phase=2.0, voltage_y_quadrature=0.2,
            voltage_z_in_phase=3.0, voltage_z_quadrature=0.3
        )
        
        self.log_interaction("Test", "CALL", "HDF5Repository", "Save sample", {"scan_id": scan_id})
        self.repo.save(scan_id, [sample])
        
        self.log_interaction("Test", "QUERY", "HDF5Repository", "Find by scan", {"scan_id": scan_id})
        retrieved = self.repo.find_by_scan(scan_id)
        
        self.log_interaction("Test", "ASSERT", "HDF5Repository", "Verify retrieved count", expect=1, got=len(retrieved))
        self.assertEqual(len(retrieved), 1)
        
        r_sample = retrieved[0]
        self.log_interaction("Test", "ASSERT", "HDF5Repository", "Verify X in-phase", expect=1.0, got=r_sample.voltage_x_in_phase)
        self.assertEqual(r_sample.voltage_x_in_phase, 1.0)
