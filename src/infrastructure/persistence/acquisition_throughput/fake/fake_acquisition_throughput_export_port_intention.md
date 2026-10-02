# fake_acquisition_throughput_export_port — Intention

## Rationale

L'export réel écrit dans `~/Desktop/AEFI_Acquisition_Exports`. Les tests
applicatifs ne doivent pas remplir le dossier d'exports de la manip, mais
doivent pouvoir vérifier ce qui aurait été exporté — y compris les
paramètres d'acquisition remis au port, au démarrage puis à la fin — et le
cas d'échec d'écriture.

## Responsibility

- Garder chaque ouverture, chaque export (résultat + échantillons) et
  chaque écriture des paramètres (`AcquisitionParametersDTO`) en mémoire ;
  rendre un emplacement fictif et deux fichiers fictifs (taille, SHA-256).
- `fail=True` : même mode d'échec que le réel (emplacement non créable,
  écriture impossible).

## Design

- Vérification d'état (`opened`, `exports`, `parameters_writes`,
  `last_samples`, `last_parameters`), pas d'interactions.
- Testé via les tests du service (pas de logique propre).
