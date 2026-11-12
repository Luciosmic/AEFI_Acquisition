# measured_object_selector — Intention

## Rationale

Un champ texte libre fait retaper l'objet mesuré à chaque
acquisition, avec ses coquilles : les exports finissent avec plusieurs
orthographes d'un même objet. Une liste des objets mesurés connus supprime
la ressaisie ; « Nouvel objet mesuré… » est le seul chemin pour ajouter un nom,
et il passe par le registre, qui refuse la seconde orthographe.

## Responsibility

- Afficher les objets mesurés connus (entrée vide « — objet mesuré — » en tête,
  « Nouvel objet mesuré… » en fin).
- « Nouvel objet mesuré… » : demander un nom, émettre `register_requested(name)` ;
  à la réponse, sélectionner l'objet mesuré rendu et dire s'il existait déjà.
- `current_measured_object()` : l'objet mesuré choisi (`MeasuredObjectDTO`) ou `None`.

## Design

- `QComboBox` ; DTO applicatifs seulement (aucun import `domain/`).
- Plusieurs sélecteurs partagent le même presenter : seul celui qui a fait la
  demande (`_pending`) sélectionne l'objet mesuré rendu ; les autres mettent
  seulement leur liste à jour, en gardant leur sélection.
- La saisie du nom est injectable (`ask_name`) pour les tests ; par défaut
  `QInputDialog`.
- La sélection reste pendant la session, n'est pas sauvegardée.
