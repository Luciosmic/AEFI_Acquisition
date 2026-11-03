# fly_scan_line_projector — Intention

## Rationale

Avant un step-scan de mesure (lent : arrêt, stabilisation, moyennage à chaque point), l'opérateur a besoin de savoir où regarder. Sans exploration rapide, la zone et le pas du step-scan sont choisis à l'aveugle, ce qui signifie qu'on découvre après une heure d'acquisition que la zone était mal cadrée, ce qui force à relancer le scan de mesure.

Le fly-scan répond à ça : le moteur balaie chaque ligne d'une traite pendant que l'ADC acquiert en continu. Mais une mesure prise en vol n'a pas d'abscisse — seulement un instant. Deux tentatives précédentes l'ont montré :
- placer les mesures en fin de ligne (durée de ligne normalisée) envoyait tous les points d'un coup : l'application a planté sous la rafale ;
- les placer en direct par un modèle « vitesse constante, départ décalé d'une demi-rampe » courait devant le moteur réel : sur le banc en fast, la ligne durait 3,80 s pour 3,31 s prévues (vitesse réelle et retard au départ tous deux différents de la consigne), soit jusqu'à ~30 mm d'erreur en bout de ligne.

Le contrôleur, lui, sait où est le moteur : son compteur d'impulsions, publié en `PositionUpdated` toutes les ~150 ms pendant le mouvement. Sans règle qui s'appuie sur ces positions, chaque calage (vitesse, retard, rampe) serait à refaire par mode et par banc.

## Responsibility

- Construire la **trace** de la ligne : couples (instant, abscisse le long de la ligne) reçus pendant le balayage (`add_position`).
- Pour chaque point de grille `k` (abscisse `k × pas`), trouver l'instant où la trace le franchit (interpolation linéaire entre deux positions), puis la valeur des échantillons à cet instant (interpolation linéaire entre les deux échantillons qui l'encadrent).
- Émettre chaque point **en direct**, dès que la trace l'a dépassé et qu'un échantillon postérieur à son instant est arrivé (`add_position` / `add_sample` rendent les points prêts).
- En fin de ligne (`finish()`), rendre les points restants : instant de franchissement si la trace l'a, sinon le dernier instant de la trace ; valeur au plus proche si aucun échantillon ne suit.

## Design

- **Synchronisation logicielle, assumée imparfaite** — c'est un scan d'exploration :
  - positions et échantillons sont horodatés à leur réception côté Python (latence USB de la lecture de position, latence de l'ADC, ordonnancement des threads) : biais de quelques dizaines de ms, quelques mm en fast ;
  - une position tous les ~150 ms (période de surveillance de l'adaptateur moteur) : entre deux, la trace est supposée linéaire — c'est là que la rampe d'accélération est approchée.
- Sur un banc sans perte de pas, le compteur d'impulsions *est* la position du moteur ; un encodeur ne changerait que la source de ce compteur, pas cette règle.
- Abscisse le long de la ligne fournie par l'appelant (projection de la position sur la direction de la ligne) : le service ne connaît pas la géométrie 2D. Trace supposée croissante (un balayage va dans un seul sens) ; une abscisse qui recule est ignorée pour le franchissement.
- Sortie sur la grille du step-scan : une mesure par point, dans l'ordre de parcours — agrégat, visualisation et export existants servent tels quels.
- Objet à état, une instance par ligne ; calcul pur, stdlib ; mêmes secondes pour positions et échantillons. Paramètres non physiques ou fin de ligne sans échantillon : `ValueError` (erreur d'appel).
