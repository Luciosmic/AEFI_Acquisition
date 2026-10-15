# bar_coarse_localization — Intention

## Rationale

Le fly scan de butée à butée produit des centaines de couples (incrément,
distance). L'affinage n'a besoin que de cinq faits : les deux plateaux, le seuil
qui les sépare et la position approximative des deux fronts. Sans objet qui les
porte, ces faits circuleraient en tuple anonyme entre l'analyse du profil et le
service, et l'opérateur ne pourrait pas voir sur quels plateaux et quel seuil
repose la mesure qu'on lui demande d'enregistrer.

## Responsibility

- Porter les plateaux mesurés pendant le fly scan : distance **sur la barre**
  (courte) et **hors barre** (longue), le seuil `s = (d_haut + d_bas) / 2` et le
  bruit des plateaux.
- Porter les deux fronts repérés grossièrement (premier < second, la barre est
  entre les deux) et le nombre de points du profil.

## Design

- Value object immuable produit par `bar_profile_analysis.locate_bar`.
- Les invariants (barre plus proche que le sol, premier front avant le second)
  sont vérifiés à la construction : un profil inversé ne doit jamais atteindre
  l'affinage.
- Les positions sont en incréments moteur, éventuellement fractionnaires (milieu
  entre deux points du profil) : l'arrondi appartient à l'encadrement.
