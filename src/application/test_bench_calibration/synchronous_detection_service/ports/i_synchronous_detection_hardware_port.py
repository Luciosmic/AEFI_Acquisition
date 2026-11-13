from abc import ABC, abstractmethod
from typing import Dict


class ISynchronousDetectionHardwarePort(ABC):
    """
    Port outbound du `SynchronousDetectionService` vers le hardware DDS
    (AD9106) — canaux ch3/ch4, dédiés à la référence de démodulation de la
    détection synchrone (ch1/ch2 restent le port de l'excitation, voir
    `IExcitationPort`).

    Responsibility:
        - `get_all_channel_phase_registers()` : snapshot mémoire logicielle des 4 registres de phase (ch1-4) — pas de lecture matérielle réelle, limitation assumée et documentée.
        - `set_ch3_phase_register(value)` : écrit uniquement le registre de phase ch3, via l'écrivain unique `AD9106AdvancedConfigurator.apply_config`.
        - `is_quadrature_enforcement_enabled()` : lecture seule du flag hardware config `enforce_dds3_dds4_quadrature` — pas de commande de toggle ici (l'enforcement est un invariant électronique, pas une décision applicative de ce service).

    Rationale:
        Port outbound du `SynchronousDetectionService` vers le hardware DDS (AD9106). Abstrait le protocole SPI/série pour les canaux ch3/ch4 (référence de démodulation de la détection synchrone), séparé de `IExcitationPort` qui pilote ch1/ch2 (excitation).

    Design:
        - **Port outbound** co-localisé dans `synchronous_detection_service/`.
        - Implémenté par `AdapterSynchronousDetectionAD9106` (Real, infrastructure) et `MockSynchronousDetectionHardwarePort` (Fake, `infrastructure/hardware/ad9106/adapter_synchronous_detection_ad9106/fake/fake_adapter_synchronous_detection_ad9106.py`).
    """

    @abstractmethod
    def get_all_channel_phase_registers(self) -> Dict[int, int]:
        """
        Snapshot des registres de phase (valeurs brutes 16 bits, 0-65535)
        des 4 canaux DDS, tel que tenu en mémoire logicielle par le
        configurateur AD9106.

        Limitation assumée : ce n'est PAS une relecture matérielle réelle
        du registre (l'AD9106 ne fournit pas ce readback sur ce banc) —
        seulement l'état logiciel du dernier `apply_config` appliqué.
        """
        raise NotImplementedError

    @abstractmethod
    def set_ch3_phase_register(self, value: int, persist: bool = False) -> None:
        """
        Écrit le registre de phase du canal 3 (valeur brute 16 bits,
        0-65535), en passant par l'écrivain unique du configurateur AD9106
        (`AD9106AdvancedConfigurator.apply_config`).

        persist=False (défaut) : écriture transitoire/programmatique
        (correction de compensation) — ne persiste jamais dans
        `ad9106_last_config.json`.
        persist=True : réglage manuel explicite de l'utilisateur (ex.
        "Lock-in Detection Phase Offset" édité depuis le panneau Excitation)
        — devient la nouvelle référence manuelle persistée.
        """
        raise NotImplementedError

    @abstractmethod
    def restore_manual_configuration(self) -> None:
        """
        Recharge et réapplique la dernière configuration persistée
        manuellement (ad9106_last_config.json), écrasant toute écriture
        transitoire de compensation (`set_ch3_phase_register`, jamais
        persistée). Appelé quand la compensation est désactivée.
        """
        raise NotImplementedError

    @abstractmethod
    def is_quadrature_enforcement_enabled(self) -> bool:
        """
        Lecture seule de l'état courant du flag hardware config
        `enforce_dds3_dds4_quadrature` (ch4 = ch3 - 90°). Pas de toggle
        exposé ici — c'est un invariant électronique configuré côté
        hardware config, pas une commande de ce service.
        """
        raise NotImplementedError

    @abstractmethod
    def get_lock_in_gain(self) -> int:
        """
        Gain courant des canaux de détection synchrone (ch3/ch4, maintenus
        égaux par le lien de gain hardware) — valeur brute de registre.
        """
        raise NotImplementedError

    @abstractmethod
    def get_default_lock_in_gain(self) -> int:
        """
        Gain recommandé par défaut pour ch3/ch4, tel que déclaré dans le
        template de configuration hardware — sert de référence pour
        détecter un gain sous-dimensionné (avertissement UI).
        """
        raise NotImplementedError

    @abstractmethod
    def reset_lock_in_gain_to_default(self) -> None:
        """
        Réapplique le gain par défaut sur ch3 (ch4 suit via le lien de
        gain). Action manuelle explicite ("Enable Lock-In Detection") —
        persiste normalement dans `ad9106_last_config.json`.
        """
        raise NotImplementedError

    @abstractmethod
    def zero_lock_in_gain(self) -> None:
        """
        Met le gain de ch3 à 0 (ch4 suit via le lien de gain) — désactive
        effectivement la détection synchrone. Action manuelle explicite
        ("Disable Lock-In Detection") — persiste normalement.
        """
        raise NotImplementedError
