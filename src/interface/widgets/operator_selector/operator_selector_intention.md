# operator_selector — Intention

## Rationale

Un champ texte libre laisse chaque opérateur retaper son nom à chaque
acquisition, avec ses coquilles : les exports finissent avec plusieurs
orthographes d'une même personne. Une liste des opérateurs connus supprime
la ressaisie ; « Nouvel opérateur… » est le seul chemin pour ajouter un nom,
et il passe par le registre, qui refuse la seconde orthographe.

## Responsibility

- Afficher les opérateurs connus (entrée vide « — opérateur — » en tête,
  « Nouvel opérateur… » en fin).
- « Nouvel opérateur… » : demander un nom, émettre `register_requested(name)` ;
  à la réponse, sélectionner l'opérateur rendu et dire s'il existait déjà.
- `current_operator()` : l'opérateur choisi (`OperatorDTO`) ou `None`.

## Design

- `QComboBox` ; DTO applicatifs seulement (aucun import `domain/`).
- Plusieurs sélecteurs partagent le même presenter : seul celui qui a fait la
  demande (`_pending`) sélectionne l'opérateur rendu ; les autres mettent
  seulement leur liste à jour, en gardant leur sélection.
- La saisie du nom est injectable (`ask_name`) pour les tests ; par défaut
  `QInputDialog`.
- La sélection reste pendant la session, n'est pas sauvegardée.
