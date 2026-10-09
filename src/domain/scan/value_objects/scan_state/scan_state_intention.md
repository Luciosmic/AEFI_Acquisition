# scan_state — Intention

## Rationale

Sans état PENDING explicite, un scan créé et un scan démarré sont indiscernables, ce qui signifie qu'on ne peut pas observer « prêt mais pas lancé », ce qui force à déduire l'état depuis l'existence de points.

## Responsibility

- Énumérer le cycle de vie minimal du `Scan` : PENDING, STARTED, COMPLETED.

## Design

- Distinct de `step_scan.ScanStatus` (non migré : pause, cancel, failed restent là-bas).
