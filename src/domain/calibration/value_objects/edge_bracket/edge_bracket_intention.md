# edge_bracket — Intention

## Rationale

Sans encadrement explicite, l'affinage d'un front de barre se réduit à une boucle
de déplacements dont l'état (quel côté est sur la barre, où sonder ensuite, quand
s'arrêter) vit dans des variables locales du service applicatif. La règle de
dichotomie et le critère d'arrêt deviennent alors invérifiables sans moteur ni
LIDAR, et l'incertitude rendue (δ) n'est plus liée à l'encadrement qui la justifie :
une erreur de signe (côté barre / côté sol inversé) donnerait un N faux sans
qu'aucun test ne le voie.

## Responsibility

- Tenir l'encadrement d'un front `[a, b]` en incréments moteur : `a` est un point
  classé **sur la barre**, `b` un point classé **hors barre** (a peut être plus
  grand ou plus petit que b : l'encadrement est orienté, pas trié).
- Donner le prochain point de sonde (milieu entier, strictement entre a et b).
- Se resserrer selon la classification du point sondé. Un point indécidable
  **n'arrête pas** l'affinage (décision du 2026-10-15, qui corrige la première
  version) : il devient une extrémité de la zone indécidable, puis la dichotomie
  continue séparément sur [a, zone] pour trouver le dernier point « sur la barre »
  et sur [zone, b] pour le premier point « hors barre ».
- Dire quand l'affinage est terminé : encadrement d'un incrément (résolution du
  moteur), ou chaque côté à un incrément de la zone indécidable (résolution du
  bruit LIDAR). Encadrement final = [dernier « sur barre », premier « hors
  barre »], front au milieu : δ ≈ demi-largeur de la zone indécidable, jamais la
  marge de l'encadrement grossier, même si la première sonde tombe dans la zone.
- Donner le centre `n = (a + b) / 2` et la demi-largeur `δ = |b − a| / 2`.
- Construire l'encadrement grossier autour d'un front repéré par le fly scan,
  élargi d'une marge, et l'élargir encore si la vérification à l'arrêt échoue.

## Design

- Value object immuable (`@dataclass(frozen=True)`), entiers : le moteur se pilote
  à l'incrément près.
- Aller-retour libre (décision du 2026-10-15) : l'encadrement ne connaît pas le sens
  d'approche, seulement les côtés.
- Un point « sur la barre » trouvé au-delà de la zone (ou « hors barre » en deçà),
  signe de bruit, recadre l'encadrement sur lui et oublie la zone, qui est alors
  hors de [a, b].
- La classification est un `BarPointClassification` (value object voisin), jamais
  une distance brute : le seuil et le bruit appartiennent à la lecture du point.
