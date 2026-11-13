# column_rest_measured — Intention

## Rationale

La stabilisation sur l'accéléromètre compare chaque point au niveau de repos mesuré au début du scan.
Sans ce fait publié, l'export ne peut dire ni à quel niveau la colonne était jugée au repos, ni pourquoi un scan s'est replié sur le délai fixe.

## Responsibility

- Dire, une fois par scan et avant le premier déplacement, le niveau de vibration de la colonne au repos (`[g]`) et le nombre d'échantillons qui l'ont donné.
- Dire pourquoi il manque quand il manque (accéléromètre non en acquisition, muet pendant la mesure, scan arrêté).
- Porter le critère appliqué (durée du repos, fenêtre, facteur, délai maximal, délai minimal), pour que le fait se lise seul.

## Design

- `@dataclass(frozen=True)`, publié par la boucle de scan sur le topic `columnrestmeasured`.
- Pas émis quand le délai de stabilisation est nul : il n'y a alors aucune stabilisation.
