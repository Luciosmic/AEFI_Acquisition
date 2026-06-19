# AD9106 — Adaptateur DDS (Excitation)

## Rationale
Ce module implémente la configuration du générateur de signal DDS AD9106 qui produit les signaux d'excitation électromagnétique du capteur AEFI. Il traduit les modes d'excitation domaine (X_DIR, Y_DIR, CIRCULAR_PLUS/MINUS) en valeurs de phase, gain et fréquence pour les quatre canaux DDS hardware.

## Responsibility
- `AD9106Controller` (`ad9106_controller.py`) : contrôleur bas-niveau. Gère les adresses de registres hardware (fréquence, mode, gain, phase, offset, constante pour chaque canal DDS 1–4) via `MCU_SerialCommunicator`. Maintient un `memory_state` pour éviter les lectures hardware.
- `AdapterExcitationConfigurationAD9106` (`adapter_excitation_configuration_ad9106.py`) : implémenter `IExcitationPort`. Traduit `ExcitationParameters` (mode, niveau %, fréquence Hz) en commandes DDS. Optimise la communication en ne mettant à jour que les paramètres modifiés (fréquence, gains, phases).

## Design
- Le mapping mode → phases DDS : X_DIR (DDS1=0°, DDS2=180°), Y_DIR (DDS1=0°, DDS2=0°), CIRCULAR_PLUS (DDS2=90°), CIRCULAR_MINUS (DDS2=270°).
- DDS3 et DDS4 sont réservés à la détection synchrone et ne sont jamais modifiés par ce module.
- Le gain matériel maximum pratique est 5500 (limité par la saturation du board d'excitation), ce qui correspond à 100 % du niveau.
