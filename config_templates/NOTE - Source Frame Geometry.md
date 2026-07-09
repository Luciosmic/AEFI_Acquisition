# NOTE — Géométrie du référentiel source AEFI 4 sphères

Source : [[Luis Saluden]]

PROJET : [[PROJET THESE]] [[PROJET ASSOCE]]
Tags : #Géométrie #RéférentielSource #Config #NoteAtomique
Date : 2026-06-18

---

## 1. Problème posé

Les 4 sphères excitatrices de l'AEFI définissent leur propre géométrie intrinsèque. En pratique, ce que l'on peut mesurer directement sur le dispositif physique, ce sont des **distances relatives** entre les centres des sphères — et non leurs coordonnées dans un référentiel global.

L'enjeu est double :

1. **Caractériser** la géométrie du dispositif par un ensemble minimal de distances mesurables.
2. **Reconstruire** un jeu de coordonnées cartésiennes cohérent, défini dans un *référentiel source canonique*, que l'on pourra ensuite transformer vers tout autre référentiel (scan, labo, simulation).

---

## 2. Notation

Les 4 sphères sont étiquetées selon leur rôle :

| Étiquette | Symbole | Rôle                   |
| ---------- | ------- | ----------------------- |
| S₁        | x+      | Sphère positive axe X  |
| S₂        | x−     | Sphère négative axe X |
| S₃        | y+      | Sphère positive axe Y  |
| S₄        | y−     | Sphère négative axe Y |

Les distances pairwise sont notées $d_{ij} = \|S_i - S_j\|$. Il y en a $\binom{4}{2} = 6$ :

$$
d_{12},\; d_{13},\; d_{14},\; d_{23},\; d_{24},\; d_{34}
$$

Pour un dispositif **idéalement symétrique** en croix :

- $d_{12} = d_{34} = d_{\text{source}}$ (distances entre sphères opposées)
- $d_{13} = d_{14} = d_{23} = d_{24} = d_{\text{source}} / \sqrt{2}$ (distances croisées)

En pratique, un éventuel défaut d'alignement mécanique brise cette symétrie → on garde les 6 distances comme paramètres indépendants.

---

## 3. Reconstruction de coordonnées — Distance Geometry Problem (DGP)

Étant donné les 6 distances $d_{ij}$, on reconstruit des coordonnées cartésiennes $(P_1, P_2, P_3, P_4)$ par la procédure suivante (solution analytique exacte).

### Étape 1 — Ancrage de S₁ à l'origine

$$
P_1 = (0,\; 0,\; 0)
$$

### Étape 2 — Placement de S₂ sur l'axe x

$$
P_2 = (d_{12},\; 0,\; 0)
$$

### Étape 3 — Placement de S₃ dans le plan xy

On pose $P_3 = (x_3, y_3, 0)$ et on résout :

$$
x_3 = \frac{d_{12}^2 + d_{13}^2 - d_{23}^2}{2\,d_{12}},
\qquad
y_3 = \sqrt{d_{13}^2 - x_3^2}
$$

> **Condition** : $d_{13}^2 \geq x_3^2$ (triangle non dégénéré).

### Étape 4 — Placement de S₄ en 3D

On pose $P_4 = (x_4, y_4, z_4)$ et on résout le système linéaire :

$$
x_4 = \frac{d_{12}^2 + d_{14}^2 - d_{24}^2}{2\,d_{12}}
$$

$$
y_4 = \frac{d_{13}^2 + d_{14}^2 - d_{34}^2 - 2\,x_3\,x_4}{2\,y_3}
$$

$$
z_4 = \pm\sqrt{d_{14}^2 - x_4^2 - y_4^2}
$$

> **Ambiguïté de signe** : le signe de $z_4$ correspond aux deux configurations miroir. On choisit $z_4 \geq 0$ par convention (ou $z_4 = 0$ si les 4 sphères sont coplanaires, ce qui est le cas nominal).

### Cas nominal AEFI : 4 sphères coplanaires

Pour le dispositif actuel, les 4 sphères sont dans le **plan horizontal** du dispositif. On impose $z_4 = 0$ et l'on vérifie $z_4^2 \approx 0$ comme test de coplanarité.

---

## 4. Définition du référentiel source canonique

Le référentiel source $\mathcal{F}_{\text{src}}$ est défini par convention à partir des positions reconstruites :

### Origine

$$
O_{\text{src}} = \frac{P_1 + P_2 + P_3 + P_4}{4} \quad \text{(centroïde des 4 sphères)}
$$

### Axes

| Axe                      | Définition                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------- |
| $\hat{x}_{\text{src}}$ | $\displaystyle\frac{P_1 - P_2}{\|P_1 - P_2\|}$ (de S₂ vers S₁, i.e. de x− vers x+)                 |
| $\hat{y}_{\text{src}}$ | $\displaystyle\frac{P_3 - P_4}{\|P_3 - P_4\|}$ (de S₄ vers S₃, i.e. de y− vers y+)                 |
| $\hat{z}_{\text{src}}$ | $\hat{x}_{\text{src}} \times \hat{y}_{\text{src}}$ (règle de la main droite, pointe vers le capteur) |

> En configuration symétrique idéale, $\hat{x}_{\text{src}} \perp \hat{y}_{\text{src}}$. En cas de défaut mécanique, les deux vecteurs ne sont pas orthogonaux. On peut alors orthonormaliser par Gram-Schmidt (avec $\hat{x}_{\text{src}}$ comme référence) si l'on veut un repère orthonormé strict, ou conserver les axes bruts comme indicateurs du défaut d'alignement.

### Coordonnées des sphères dans $\mathcal{F}_{\text{src}}$

Dans le référentiel canonique symétrique, les positions attendues sont :

$$
S_1^{\text{src}} = (+d/2,\; 0,\; 0), \quad S_2^{\text{src}} = (-d/2,\; 0,\; 0)
$$

$$
S_3^{\text{src}} = (0,\; +d/2,\; 0), \quad S_4^{\text{src}} = (0,\; -d/2,\; 0)
$$

avec $d = d_{\text{source}}$.

---

## 5. Transformation vers un référentiel global

Un point $P^{\text{src}}$ exprimé dans $\mathcal{F}_{\text{src}}$ se transforme dans le référentiel du scan $\mathcal{F}_{\text{scan}}$ par :

$$
P^{\text{scan}} = R \cdot P^{\text{src}} + T
$$

où :

- $R \in SO(3)$ : matrice de rotation $3\times3$ (colonnes = axes de $\mathcal{F}_{\text{src}}$ exprimés dans $\mathcal{F}_{\text{scan}}$)
- $T \in \mathbb{R}^3$ : vecteur de translation (position de $O_{\text{src}}$ dans $\mathcal{F}_{\text{scan}}$)

La rotation $R$ est définie par le montage physique (orientation du dispositif sur le banc). Dans le cas nominal où les axes src et scan sont alignés, $R = I_3$.

---

## 6. Ce qui est à définir dans les fichiers de configuration

Pour un dispositif donné, on a besoin de :

### Dans `aefi_device_config.json` (géométrie intrinsèque du dispositif)

```
excitation.sources_geometry.pairwise_distances :
  d_s1_s2  (x+ ↔ x−)
  d_s1_s3  (x+ ↔ y+)
  d_s1_s4  (x+ ↔ y−)
  d_s2_s3  (x− ↔ y+)
  d_s2_s4  (x− ↔ y−)
  d_s3_s4  (y+ ↔ y−)
```

### Dans `bench_config.json` (montage sur le banc, référentiel scan)

```
source_frame_in_scan :
  origin    : [x, y, z]   — position du centroïde des sphères dans le référentiel scan
  rotation  : [rx, ry, rz] — angles d'Euler ou matrice R (3×3)
```

---

## 7. Plan d'implémentation

1. **Étendre `aefi_device_config.json`** : remplacer `d_source` scalaire par le dictionnaire `pairwise_distances` à 6 entrées (avec valeurs par défaut pour le cas symétrique).
2. **Module Python `source_frame.py`** : classe `SourceFrameGeometry` qui :

   - prend les 6 distances en entrée
   - calcule les 4 positions par l'algorithme DGP (§3)
   - expose le centroïde, les axes, et la matrice de rotation $R$ vers $\mathcal{F}_{\text{src}}$
   - valide la coplanarité et l'orthogonalité des axes (avec seuils de tolérance)
3. **Tests unitaires** : cas symétrique ($d_{ij}$ calculés analytiquement), vérification des positions reconstruites, test de la transformation $\mathcal{F}_{\text{src}} \leftrightarrow \mathcal{F}_{\text{scan}}$.

---

## Références

- [[aefi_device_config.json]]
- [[bench_config.json]]
- Liberti, L. & Maculan, N. (Eds.), *Distance Geometry: Theory, Methods, and Applications*, Springer, 2013.
