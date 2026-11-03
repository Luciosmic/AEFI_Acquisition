# lsm9ds1_stream_protocol — Intention

## Rationale

Sans module pur pour le protocole de flux, ses règles (ordre des champs,
commandes, lignes de transitoire) se mélangeraient à la lecture série : elles
ne seraient testables qu'avec une liaison simulée, et une erreur d'ordre des
champs attribuerait l'accélération au magnétomètre sans qu'aucun test ne le
voie. Le protocole (établi par 14 expériences sur la carte, 2026-10-12) est de
la logique pure : on la sépare de l'I/O pour la tester sans matériel.

## Responsibility

- `start_commands(sensors)` : `A9*`, `G9*`, `M9*`, `L9*` (ajout cumulatif au
  flux) ; arrêt `S*`.
- Ordre fixe des champs d'une ligne : **magnétomètre, accéléromètre,
  gyroscope, lidar** (3, 3, 3, 1 entiers).
- `parse_stream_line(line, sensors)` : dictionnaire de tuples d'entiers, ou
  `None` si la ligne n'a pas la forme du régime (transitoire, tronquée).
- `LineSplitter` : accumule les octets, rend les lignes complètes.

## Design

- Noms de capteurs explicites (`accelerometer`, `gyroscope`, `magnetometer`,
  `lidar`) : pas d'abréviation opaque aux frontières.
- Jamais de LF ni CRLF envoyé : il invalide la trame suivante.
- Ordre des champs observé avec les quatre capteurs actifs ; pour les
  sous-ensembles sans accéléromètre (magnétomètre+lidar, gyroscope+lidar,
  magnétomètre+gyroscope), l'ordre fixe est une **supposition** non vérifiée.
- Le lidar est un canal du même flux : voir la dette `ponytail:` du module.
