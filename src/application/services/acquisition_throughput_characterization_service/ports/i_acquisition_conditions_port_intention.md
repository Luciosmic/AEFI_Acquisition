# i_acquisition_conditions_port — Intention

## Rationale

Le débit et le bruit mesurés dépendent de conditions dispersées : catalogue
des composants (registre domaine), mémoire des contrôleurs ADS131A04 et
AD9106, fichiers de configuration résolus, service de calibration du
capteur, service de détection synchrone, port moteurs, communicateur série.
Sans ce port, le service de caractérisation dépendrait de chacun d'eux et
de leur stockage ; ses tests devraient monter tout le banc pour vérifier un
document ; et un fait illisible ferait échouer le balayage au lieu d'être
déclaré inconnu.

## Responsibility

- `read_conditions()` : toutes les conditions matérielles connues du
  système, en un `AcquisitionConditionsDTO` ; chaque fait illisible vaut
  `None` avec sa raison dans `unknown`.
- `read_bench_position()` : position X/Y du banc (mm), ou un échec lisible
  (moteurs non connectés).

## Design

- ABC pure, port sortant (Application → Infrastructure), déclaré dans le
  dossier du service qui le consomme.
- Implémentations : `AcquisitionConditionsReader` (réutilise
  `AcquisitionSnapshotReader` pour le catalogue), `FakeAcquisitionConditionsPort`.
- Jamais d'exception pour un fait illisible : c'est une condition attendue
  (moteurs déconnectés, transport simulé, fichier absent).
- Appelé pendant le balayage, après la coupure de l'excitation : les
  réglages AD9106 rendus sont ceux appliqués pendant la mesure.
