# frequency_sweep_role — Intention

## Rationale

Le protocole d'acquisition en fréquence enchaîne des balayages acquis de la même façon mais qui ne caractérisent pas la même chose : l'instrument seul (table en position basse), le fond à la hauteur de travail, puis l'objet. Sans rôle explicite, ce qu'un balayage caractérise ne vit que dans le nom de son dossier, et un fond ne peut pas être retrouvé pour être réutilisé ou combiné.

## Responsibility

- Nommer ce qu'un balayage caractérise : `INSTRUMENT_REFERENCE` (table en position basse, sans objet), `BACKGROUND` (table à la hauteur de travail, sans objet).

## Design

- `Enum` ; la valeur est l'identifiant stable écrit dans l'export.
- Le rôle ne change pas la façon d'acquérir.
- La mesure objet (`OBJECT_MEASUREMENT`) arrive avec la tranche 2 du plan, en même temps que le choix de l'objet et du fond : pas avant.
