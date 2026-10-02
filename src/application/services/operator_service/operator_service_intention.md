# operator_service — Intention

## Rationale

Le registre des opérateurs (aggregate `OperatorRegistry`) ne sait ni lire ni
écrire, ni prévenir les panneaux. Sans service, chaque panneau (Scan,
Continuous Reading) relirait le fichier, appliquerait la règle d'orthographe
à sa façon et ignorerait les ajouts faits dans l'autre ; un registre illisible
remonterait en exception brute jusqu'à l'interface.

FA : `_system/thoughts_interface/fa_operator_traceability.md` (N = 1) ;
Promise Model : `_system/promise_model/operator_registry.md`.

## Responsibility

- `list_operators()` : les opérateurs connus, triés par nom.
- `register_operator(name)` : reconstitue le registre, applique la règle
  métier (aggregate), persiste et publie `OperatorRegistered` **seulement si
  l'opérateur est créé** ; une orthographe déjà connue rend l'existant
  (`already_registered`), avec un log, sans événement.
- Union d'erreurs (fermée) : `OperatorNameBlank` (refus domaine I2),
  `OperatorRegistryUnavailable` (échec du dépôt traduit ici — aucune erreur
  d'infrastructure ne sort du service).

## Design

- Commande / requête séparées ; dépôt et bus injectés au constructeur.
- Topic publié : `"operatorregistered"` (nom de classe en minuscules).
- Logs d'intention à l'entrée de chaque commande, avec l'`operator_id`.
