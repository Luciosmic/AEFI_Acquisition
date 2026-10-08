# fake_adc_output_rate_export_port — Intention

## Rationale

L'export réel écrit dans le dossier d'exports de la manip ; les tests ne
doivent pas le remplir, mais doivent pouvoir vérifier ce qui aurait été
exporté et le cas d'échec d'écriture.

## Responsibility

- Garder chaque export (résultat + captures) en mémoire ; rendre un
  emplacement fictif. `fail=True` : écriture impossible, comme le réel.

## Design

- Vérification d'état (`exports`). Testé via les tests du service.
