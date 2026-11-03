# acquisition_snapshot_reader — Intention

## Rationale

La description matérielle d'un export doit être ce que le système sait (registres
domaine) et ce qui est réellement appliqué aux puces — pas la copie d'un modèle
édité à la main, ni le seul dernier fichier enregistré. Avant le 2026-10-02,
l'export ne contenait ni `n_avg` (moyennage MCU) ni la config de l'ADC (OSR,
diviseurs d'horloge, gains, Vref) : le débit et le bruit d'une série temporelle
ne pouvaient pas être reproduits. Et il recopiait `ad9106_last_config.json`
seul, alors que le matériel applique la fusion `default + last` : une valeur
absente du dernier fichier n'apparaissait pas, bien qu'appliquée.

## Responsibility

Implémenter `IAcquisitionSnapshotPort` :

- `hardware_configuration` — depuis les registres domaine : pour chaque type de
  composant, le composant monté et sa caractérisation courante ; la dernière
  calibration capteur et géométrie source, avec la reconstruction des positions
  des sphères ; les avertissements d'une configuration incomplète.
- `hardware_settings` — les réglages appliqués à l'AD9106, l'ADS131A04 et le MCU :
  `default + last` résolus par `resolve_config` (la même fonction que le
  démarrage du matériel), un avertissement par réglage inconnu ou fichier
  illisible.
- La dernière config moteur et les défauts de connexion de la sonde, lus tels
  quels depuis leurs fichiers.

## Design

- Ne lève jamais : fichier absent → réglage `null` + avertissement ; fichier
  illisible → couche ignorée + avertissement (la valeur exportée peut alors
  différer de l'appliquée, et le document le dit).
- `ponytail:` la compensation de la détection synchrone écrit les phases DDS
  sans les persister : pendant qu'elle est active, `hardware_settings.ad9106`
  montre les phases non compensées. Le schéma 1.0 prévoit de lire l'état mémoire
  du contrôleur.
- Depuis le 2026-10-02, ce dict n'est plus écrit tel quel dans les exports :
  `AcquisitionConditionsReader` le traduit en `AcquisitionConditionsDTO`, que
  les sérialiseurs 1.0 (scan, série temporelle, balayage de débit) mettent en
  page selon `application/services/scan_export_service/acquisition_parameters/acquisition_parameters_intention.md`.
  Sa forme (`hardware_configuration`, `hardware_settings`) est donc un contrat
  interne entre ces deux adaptateurs.
- Tests : `_tests/acquisition_snapshot_reader_test.py`.
