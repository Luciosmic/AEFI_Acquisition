# lidar_distance — Intention

## Rationale

Le LIDAR envoie 0 quand il ne mesure rien : sol hors de portée, décrochage sur la
barre (premier essai au banc, 2026-10-15). Sans objet qui porte cette règle, le 0
circule comme une distance : il entre dans les moyennes, devient le « plateau le
plus proche » et inverse barre et sol (le banc a annoncé des plateaux 0,0 / 95,0 mm).
Si la règle vivait dans un adaptateur, chaque consommateur du LIDAR (calibration
par barre, panneau du capteur inertiel) devrait la redécouvrir ou la refaire, et
un double de test qui l'oublierait laisserait passer des 0 sans qu'aucun test ne
le voie.

## Responsibility

- Représenter un échantillon LIDAR : soit un **retour valide** avec sa distance en
  mm, toujours finie et > 0 ; soit **pas de retour**. Une distance de 0 n'existe pas.
- `from_raw(raw, mm_per_lsb)` : seule traduction de la valeur brute du capteur ;
  0 (et toute valeur ≤ 0) → pas de retour, sinon distance = raw × mm_per_lsb.

## Design

- Value object immuable (`frozen=True`) du noyau partagé : deux contextes
  l'utilisent, la calibration par barre et (à terme) le panneau du capteur
  inertiel.
- `distance_mm` vaut None pour « pas de retour » ; `has_return` le dit.
- Le facteur de conversion (unité non vérifiée) reste à l'adaptateur, qui le
  passe à `from_raw` : seule la sémantique du 0 est une règle de domaine.
- Le « pas de retour » n'est jamais supprimé : hors barre, c'est la signature du
  sol hors de portée.
