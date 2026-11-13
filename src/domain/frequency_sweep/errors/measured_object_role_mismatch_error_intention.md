# measured_object_role_mismatch_error — Intention

## Rationale

Une mesure objet sans objet nommé ne se rattache à rien : on ne retrouve plus quelles mesures portent sur quel objet. À l'inverse, un fond qui porterait un objet serait faux par construction : le fond se mesure sans objet.

## Responsibility

- Nommer la promesse refusée : « une mesure objet nomme son objet ; une référence instrument ou un fond n'en a pas ».

## Design

- Hérite de `ValueError` (convention des erreurs de l'agrégat) ; porte le rôle et l'identifiant reçu.
