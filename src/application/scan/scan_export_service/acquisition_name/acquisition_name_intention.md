# acquisition_name — Intention

## Rationale

Le nom d'une acquisition exportée était une « base » libre, tapée par l'opérateur : selon les jours elle portait l'objet et le lift-off (`water_in_bottle_8mm_…`), un mot générique (`scan`) ou rien (`2026-11-12_194400_flyScan_`).
Un dossier d'exports ne se lisait donc pas de façon homogène, et le nom pouvait contredire le fichier de paramètres.
Le contenu des fichiers est fixé par le schéma versionné du fichier de paramètres ; le nom, lui, doit seulement dire d'un coup d'œil ce qui a été mesuré.

## Responsibility

- Composer la partie du nom qui suit `<horodatage>_<stepScan|flyScan|timeSeries>_` : `<objet mesuré>_liftoff-<valeur>mm`.
- Écrire `objet-non-saisi` ou `liftoff-non-saisi` quand la valeur manque, pour que chaque nom ait les mêmes champs.

## Design

- Fonction pure : l'objet et le lift-off sont ceux que l'opérateur a choisis au démarrage, les mêmes qui partent dans `feature_of_interest` du fichier de paramètres.
- Le type de scan et l'horodatage restent ajoutés par les ports d'export, qui fixent aussi le suffixe de chaque fichier (`_aefi.csv`, `.h5`, `_acquisition-parameters.json`…).
- Le commentaire de l'opérateur n'entre jamais dans le nom : il va dans le fichier de paramètres (`provenance.activity.operator_comment`).
- Les espaces deviennent des tirets ; un caractère qu'un nom de fichier ne porte pas est retiré. Le point est gardé, pour un lift-off décimal (`liftoff-2.5mm`).
