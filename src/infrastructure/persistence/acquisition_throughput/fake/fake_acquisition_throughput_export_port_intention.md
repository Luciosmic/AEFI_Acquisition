# fake_acquisition_throughput_export_port — Intention

## Rationale

L'export réel écrit dans `~/Desktop/AEFI_Acquisition_Exports`. Les tests
applicatifs ne doivent pas remplir le dossier d'exports de la manip, mais
doivent pouvoir vérifier ce qui aurait été exporté et le cas d'échec
d'écriture.

## Responsibility

- Garder chaque export (résultat + échantillons) en mémoire ; rendre un
  emplacement fictif.
- `fail=True` : même mode d'échec que le réel (écriture impossible).

## Design

- Vérification d'état (`exports`, `last_samples`), pas d'interactions.
- Testé via les tests du service (pas de logique propre).
