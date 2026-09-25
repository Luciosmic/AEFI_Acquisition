# flow_layout — Intention

## Rationale

Sans lui, une rangée de groupes de contrôles posée dans un `QHBoxLayout` impose au panneau une largeur minimale égale à la somme de tous les groupes. Le `CDockWidget` QtAds enveloppe alors le panneau dans une zone de défilement, et la barre horizontale apparaît : pour voir le signal en entier, il faut élargir le dock bien au-delà de ce que le tracé demande. Qt ne fournit pas de layout qui passe à la ligne.

## Responsibility

- Disposer des widgets de gauche à droite et les renvoyer à la ligne quand la largeur disponible est dépassée.
- Déclarer une largeur minimale égale au plus large de ses éléments seulement, jamais à leur somme.
- Déclarer sa hauteur selon la largeur (`heightForWidth`), pour que le layout parent lui réserve exactement le nombre de lignes nécessaire.

## Design

- Reprise allégée de l'exemple officiel Qt « Flow Layout ».
- Chaque élément reçoit sa taille de `sizeHint()` : pas d'étirement horizontal, les groupes gardent leur taille compacte.
- Les widgets masqués (`isEmpty()`) ne prennent aucune place.
