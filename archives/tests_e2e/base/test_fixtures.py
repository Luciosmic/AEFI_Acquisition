"""
Test Fixtures - Réutilisables pour tous les tests E2E

Responsabilité:
- Fournir des factories pour créer des objets de test
- Standardiser la configuration des mocks
- Réduire la duplication de code dans les tests
"""

from uuid import uuid4
from domain.models.scan.value_objects import ScanConfig, StepAcquisitionPlan
from domain.models.scan.value_objects import ScanZone
from domain.models.scan.value_objects import ScanPattern
from domain.models.scan.value_objects import MeasurementUncertainty
from domain.models.scan.aggregate.scan import Scan
from domain.shared.value_objects.position_2d import Position2D
from domain.models.motion.value_objects.motion_profile import MotionProfile
from domain.models.motion.services.motion_profile_selector import MotionProfileSelector

from infrastructure.internal.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.external.hardware.arcus_performax_4EX._mock.mock_motion_port import MockMotionPort
from infrastructure.external.hardware.micro_controller._mock.mock_acquisition_port import FakeAcquisitionPort


def create_scan_config(
    x_min=0.0,
    x_max=10.0,
    y_min=0.0,
    y_max=10.0,
    x_points: int = 3,
    y_points: int = 3,
    pattern: ScanPattern = ScanPattern.RASTER,
    stabilization_delay_ms: int = 100,
    avg_per_pos: int = 1,
    uncertainty_volts: float = 1e-6,
    zone: ScanZone = None,
    averaging: int = None  # Deprecated, use avg_per_pos
) -> tuple[ScanConfig, StepAcquisitionPlan]:
    """
    Factory pour créer une ScanConfig + StepAcquisitionPlan de test.
    
    Args:
        x_min, x_max, y_min, y_max: Limites de la zone de scan (cm)
        x_points: Nombre de points en X
        y_points: Nombre de points en Y
        pattern: Pattern de scan (par défaut: RASTER)
        stabilization_delay_ms: Délai de stabilisation
        avg_per_pos: Nombre de moyennes par position
        uncertainty_volts: Incertitude maximale
        zone: Zone de scan (alternative, ignore x_min/x_max/y_min/y_max si fourni)
        averaging: Deprecated, utilise avg_per_pos
        
    Returns:
        tuple[ScanConfig, StepAcquisitionPlan] configurés
    """
    if zone is None:
        zone = ScanZone(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
    
    # Support deprecated 'averaging' parameter
    if averaging is not None:
        avg_per_pos = averaging
    
    scan_config = ScanConfig(
        scan_zone=zone,
        x_nb_points=x_points,
        y_nb_points=y_points,
        scan_pattern=pattern
    )
    
    acquisition_plan = StepAcquisitionPlan(
        stabilization_delay_ms=stabilization_delay_ms,
        samples_per_position=avg_per_pos,
        measurement_uncertainty_requirement=MeasurementUncertainty(max_uncertainty_volts=uncertainty_volts)
    )
    
    return scan_config, acquisition_plan


def create_mock_motion_port(
    event_bus: InMemoryEventBus = None,
    delay_ms: float = 50.0,
    motion_profile: MotionProfile = None,
    failure_next: bool = False,
    failure_reason: str = "Simulated error"
) -> MockMotionPort:
    """
    Factory pour créer un FakeMotionPort configuré.
    
    Args:
        event_bus: Event bus (créé si None)
        delay_ms: Délai de mouvement en ms
        motion_profile: Profil de mouvement (si None, utilise delay_ms)
        failure_next: Si True, le prochain mouvement échouera
        failure_reason: Raison de l'échec
        
    Returns:
        FakeMotionPort configuré
    """
    if event_bus is None:
        event_bus = InMemoryEventBus()
    
    # MockMotionPort accepts event_bus
    port = MockMotionPort(event_bus=event_bus)
    
    # Configure failure if requested (if supported by MockMotionPort)
    if failure_next and hasattr(port, 'set_failure_next_move'):
        port.set_failure_next_move(failure_reason)
    
    return port


def create_mock_acquisition_port() -> FakeAcquisitionPort:
    """
    Factory pour créer un FakeAcquisitionPort.
    
    Returns:
        FakeAcquisitionPort
    """
    return FakeAcquisitionPort()


def create_event_bus() -> InMemoryEventBus:
    """
    Factory pour créer un InMemoryEventBus.
    
    Returns:
        InMemoryEventBus
    """
    return InMemoryEventBus()


def create_step_scan(scan_id=None) -> StepScan:
    """
    Factory pour créer un StepScan.
    
    Args:
        scan_id: UUID du scan (généré si None)
        
    Returns:
        StepScan
    """
    if scan_id is None:
        scan_id = uuid4()
    return StepScan(id=scan_id)


def create_motion_profile_selector(
    threshold_cm: float = 0.5,
    slow_profile: MotionProfile = None,
    fast_profile: MotionProfile = None
) -> MotionProfileSelector:
    """
    Factory pour créer un MotionProfileSelector.
    
    Args:
        threshold_cm: Seuil de distance (cm)
        slow_profile: Profil pour petites distances
        fast_profile: Profil pour grandes distances
        
    Returns:
        MotionProfileSelector configuré
    """
    return MotionProfileSelector(
        small_distance_threshold_cm=threshold_cm,
        slow_profile=slow_profile,
        fast_profile=fast_profile
    )


def create_simple_trajectory() -> list[Position2D]:
    """
    Factory pour créer une trajectoire simple de test.
    
    Returns:
        Liste de Position2D
    """
    return [
        Position2D(x=0.0, y=0.0),
        Position2D(x=5.0, y=0.0),
        Position2D(x=10.0, y=0.0),
    ]

