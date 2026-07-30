# Ponytail debt — ledger

Chaque raccourci délibéré marqué `ponytail:` dans le code, avec son plafond
et sa condition de révision. Généré par le skill `ponytail-debt` le
2026-07-29 — à régénérer périodiquement (le grep est dans le skill), pas à
maintenir à la main.

Scan : `grep -rnE '(#|//) ?ponytail:' .`

## Avec trigger de révision

- **[scan_export_service.py:63](../../src/application/services/scan_export_service/scan_export_service.py#L63)** — `ScanExportService` appelle directement `ExcitationConfigurationService.get_current_parameters()`. Ceiling : appel Application→Application, viole la règle d'isolation des services. Upgrade : remplacer par un abonnement événementiel une fois qu'un événement `ExcitationChanged` existe.
- **[fake_electric_field_probe_adapter.py:72](../../src/infrastructure/hardware/narda_ep600/fake/fake_electric_field_probe_adapter.py#L72)** — la valeur de batterie rejouée reste fixe, pas de simulation de décharge. Ceiling : suffisant pour tester le câblage du refresh, pas une valeur qui varie. Upgrade : à enrichir si un test a besoin de voir la valeur affichée changer.

## Sans trigger (`no-trigger` — risque de pourrir silencieusement)

- **[electric_field_probe_post_processor.py:20](../../external_modules/electric_field_probe_post_processor/electric_field_probe_post_processor.py#L20)** — remplissage des trous NaN par moyenne des voisins directs, répété jusqu'à stabilité. Ceiling : heuristique naïve, pas d'interpolation physique.
- **[scan_trajectory_factory.py:63](../../src/domain/step_scan/services/scan_trajectory_factory/scan_trajectory_factory.py#L63)** — pattern COMB toujours Y-first (colonnes), ignore `scan_axis`. Ceiling : comportement legacy figé, incohérent avec RASTER/SERPENTINE qui respectent `scan_axis`.
- **[electric_field_probe_acquisition_executor.py:54](../../src/infrastructure/execution/electric_field_probe_acquisition_executor.py#L54)** — cadence de simulation fixe à 50Hz (`_SAMPLE_INTERVAL_S`), pas configurable. Ceiling : hardcodé plutôt qu'un paramètre de débit.
- **[adapter_mock_i_aefi_acquisition_executor.py:26](../../src/infrastructure/mocks/adapter_mock_i_aefi_acquisition_executor.py#L26)** — cadence de simulation fixe à 1kHz (`_SIMULATION_INTERVAL_S`), pas configurable. Ceiling : hardcodé plutôt qu'un paramètre de débit.

**6 markers, 4 with no trigger.**
