# i_api_synchronous_detection_service — Intention

## Rationale

Frontière inbound (Adapters/Presenter -> Application) du use case de calibration de phase de détection synchrone. Distinct des ports outbound (`i_synchronous_detection_hardware_port.py`), qui vont dans le sens Application -> Infrastructure.

## Responsibility

- `get_sphere_phases()` : query — phases dérivées S1-S4 + Delta_Phi corrigé + état quadrature, pour affichage lecture seule.
- `save_calibration_point()` : commande — enregistre un point de calibration (fréquence courante, Delta_Phi mesuré ch3-ch1) dans le registre append-only.
- `is_compensation_enabled()` / `set_compensation_enabled(enabled)` : query/commande du flag domaine de compensation.

## Design

- Pure ABC, aucun état.
- Implémentée par `SynchronousDetectionService`.
- Seul `SpherePhasesDTO` traverse cette frontière — jamais de VO `domain/`.
