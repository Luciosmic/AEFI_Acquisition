from abc import ABC, abstractmethod
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters

class IExcitationPort(ABC):
    """
    Port for controlling the excitation generation.

    Responsibility:
        - `apply_excitation(params)` : appliquer mode/niveaux/fréquence.
        - `set_gain(level_s1_s2, level_s3_s4)` : écrire uniquement le gain, sans publier d'event — pour
          le cycle mute/unmute transitoire des scans différentiels (ne doit pas resynchroniser le
          panel Hardware Config à chaque point de scan).
        - `set_link_dds1_dds2(linked)` : persister et publier le changement du lien de gain
          DDS1/DDS2 (S1-S2 = S3-S4), partagé avec le paramètre `link_dds1_dds2` du panel Hardware
          Advanced Config.

    Rationale:
        Port outbound du `ExcitationConfigurationService` vers le hardware DDS (AD9106). Abstraire le protocole SPI/série de la logique applicative de configuration d'excitation.

    Design:
        - **Port outbound** co-localisé dans `excitation_configuration_service/`.
        - Implémenté par `AdapterExcitationConfigurationAD9106` (Real) et `MockExcitationPort` (Mock,
          `infrastructure/hardware/ad9106/adapter_excitation_configuration_ad9106/fake/fake_adapter_excitation_configuration_ad9106.py`).
    """

    @abstractmethod
    def apply_excitation(self, params: ExcitationParameters) -> None:
        """
        Apply the requested excitation parameters (Mode and Level) to the hardware.
        """
        raise NotImplementedError

    @abstractmethod
    def set_gain(self, level_s1_s2_percent: float, level_s3_s4_percent: float) -> None:
        """
        Write only the gain, leaving mode/phase/frequency untouched and
        without publishing a config-changed event — for the
        differential-scan mute/unmute cycle, a transient per-point toggle
        that shouldn't sync the Hardware Config tab on every point.
        """
        raise NotImplementedError

    @abstractmethod
    def set_link_dds1_dds2(self, linked: bool) -> None:
        """
        Persist and publish the DDS1/DDS2 gain link preference (Excitation
        panel's "Link S1-S2 = S3-S4") so the Hardware Advanced Config tab's
        own link_dds1_dds2 parameter stays in sync with it, and vice versa.
        """
        raise NotImplementedError
