# aefi_acquisition_executor — Intention

## Rationale

Implémentation concrète de `IAefiAcquisitionExecutor` qui gère le streaming d'acquisition en boucle continue best-effort (thread). Séparé de `StepScanExecutor` car la logique temporelle est différente : ici c'est un polling back-to-back, pas une synchronisation event-based.

Note : ce fichier n'est actuellement câblé nulle part en production (le canal
AEFI réel utilise `AdapterAefiAcquisitionAds131a04`) — seul son propre test
l'instancie.

## Responsibility

- Démarrer une boucle d'acquisition best-effort dans un thread séparé.
- Appeler `IAcquisitionPort.acquire_sample()` en boucle et publier/callback le résultat.
- Arrêter proprement la boucle sur `stop()`.

## Design

- **Thread daemon + flag d'arrêt** : stopper proprement sans join bloquant.
- **Pas de rate configurable** : le round-trip du port d'acquisition (matériel
  ou simulé) domine le timing ; aucun pacing logiciel n'est ajouté ici.
