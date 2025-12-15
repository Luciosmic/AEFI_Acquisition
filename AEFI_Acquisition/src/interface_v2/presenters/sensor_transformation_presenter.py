from PySide6.QtCore import QObject, Slot
from interface_v2.widgets.panels.sensor_transformation_panel import SensorTransformationPanel
from application.services.transformation_service.transformation_service import TransformationService

class SensorTransformationPresenter(QObject):
    """
    Connects SensorTransformationPanel to TransformationService.
    - Updates service state (angles)
    - Computes test vector transformation for preview.
    """
    
    def __init__(self, panel: SensorTransformationPanel, service: TransformationService):
        super().__init__()
        self._panel = panel
        self._service = service
        
        # Connect Panel -> Presenter
        self._panel.angles_changed.connect(self._on_angles_changed)
        self._panel.test_vector_changed.connect(self._on_test_vector_changed)
        
        # Initial wiring
        # We might want to set panel values to match service values here
        # But for now, let's assume panel drives the service on startup/change.
        self._panel._on_inputs_changed()

    @Slot(float, float, float)
    def _on_angles_changed(self, theta_x, theta_y, theta_z):
        """Update service angles."""
        self._service.set_rotation_angles(theta_x, theta_y, theta_z)

    @Slot(float, float, float)
    def _on_test_vector_changed(self, vx, vy, vz):
        """Calculate transform preview using service logic (forced)."""
        v_in = (vx, vy, vz)
        # Use force_transform so we can see result even if global processing is disabled
        v_out = self._service.force_transform_sensor_to_source(v_in)
        
        self._panel.update_output_vector(v_out)

