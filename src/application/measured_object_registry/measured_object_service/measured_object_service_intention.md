---
type: service-applicatif::solidai-hexagonal
tldr: "Service applicatif `measured_object_service` : `list_measured_objects()` : les objets mesurés connus, triés par nom."
code: ["[[src/application/measured_object_registry/measured_object_service/measured_object_service.py]]"]
cause_de_changement: orchestration
---
# measured_object_service — Intention

## Rationale

Le registre des objets mesurés (aggregate `MeasuredObjectRegistry`) ne sait ni lire ni
écrire, ni prévenir les panneaux. Sans service, chaque panneau (Scan,
Continuous Reading) relirait le fichier, appliquerait la règle d'orthographe
à sa façon et ignorerait les ajouts faits dans l'autre ; un registre illisible
remonterait en exception brute jusqu'à l'interface.

Calqué sur le registre des opérateurs (`domain/operator_registry/`), même invariants.

## Responsibility

- `list_measured_objects()` : les objets mesurés connus, triés par nom.
- `register_measured_object(name)` : reconstitue le registre, applique la règle
  métier (aggregate), persiste et publie `MeasuredObjectRegistered` **seulement si
  l'objet mesuré est créé** ; une orthographe déjà connue rend l'existant
  (`already_registered`), avec un log, sans événement.
- Union d'erreurs (fermée) : `MeasuredObjectNameBlank` (refus domaine I2),
  `MeasuredObjectRegistryUnavailable` (échec du dépôt traduit ici — aucune erreur
  d'infrastructure ne sort du service).

## Design

- Commande / requête séparées ; dépôt et bus injectés au constructeur.
- Topic publié : `"measuredobjectregistered"` (nom de classe en minuscules).
- Logs d'intention à l'entrée de chaque commande, avec l'`measured_object_id`.
