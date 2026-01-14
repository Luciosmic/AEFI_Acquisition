from datetime import datetime
import random
from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement

class MockAcquisitionPort(IAcquisitionPort):
    def __init__(self):
        self.acquire_count = 0
        
    def acquire_sample(self) -> VoltageMeasurement:
        self.acquire_count += 1
        print(f"[MockAcquisitionPort] Acquiring sample #{self.acquire_count}")
        # Return synthetic data based on count
        return VoltageMeasurement(
            voltage_x_in_phase=0.1 * self.acquire_count,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.2 * self.acquire_count,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now(),
            uncertainty_estimate_volts=None
        )
        
    def get_quantification_noise(self) -> float:
        # Return a simulated noise floor of 10 microvolts
        return 10e-6
        
    def is_ready(self) -> bool:
        return True

class RandomNoiseAcquisitionPort(IAcquisitionPort):
    """
    Mock d'acquisition continue générant un signal aléatoire.

    - Chaque appel à acquire_sample() retourne un VoltageMeasurement
      avec bruit gaussien (mu=0, sigma configurable) sur Ex In-Phase.
    - Les autres composantes sont laissées à 0 pour rester simples.
    """

    def __init__(self, noise_std: float = 0.1, seed: int | None = None) -> None:
        self.noise_std = noise_std
        self._rng = random.Random(seed)
        self.acquire_count = 0

    def acquire_sample(self) -> VoltageMeasurement:
        self.acquire_count += 1
        # Génère un bruit gaussien indépendant pour chaque composante
        vx_i = self._rng.gauss(0.0, self.noise_std)
        vx_q = self._rng.gauss(0.0, self.noise_std)
        vy_i = self._rng.gauss(0.0, self.noise_std)
        vy_q = self._rng.gauss(0.0, self.noise_std)
        vz_i = self._rng.gauss(0.0, self.noise_std)
        vz_q = self._rng.gauss(0.0, self.noise_std)
        print(
            f"[RandomNoiseAcquisitionPort] Sample #{self.acquire_count}: " # Use self.acquire_count as it's the existing counter
            f"Ux=({vx_i:.3f},{vx_q:.3f}) Uy=({vy_i:.3f},{vy_q:.3f}) Uz=({vz_i:.3f},{vz_q:.3f})"
        )
        return VoltageMeasurement(
            voltage_x_in_phase=vx_i,
            voltage_x_quadrature=vx_q,
            voltage_y_in_phase=vy_i,
            voltage_y_quadrature=vy_q,
            voltage_z_in_phase=vz_i,
            voltage_z_quadrature=vz_q,
            timestamp=datetime.now(),
            uncertainty_estimate_volts=None,
        )

    def get_quantification_noise(self) -> float:
        # Return the configured noise standard deviation
        return self.noise_std

    def is_ready(self) -> bool:
        return True
