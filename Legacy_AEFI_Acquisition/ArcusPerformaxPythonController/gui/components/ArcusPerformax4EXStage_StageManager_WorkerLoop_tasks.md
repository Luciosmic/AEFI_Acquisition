# Product Requirement Document (PRD) — Refonte du worker StageManager avec gestion des priorités
2025-07-24

## Contexte & Objectifs

Le worker du StageManager pilote le contrôleur matériel via une file de commandes. Il doit :
- Acquérir la position en continu (get_position), aussi souvent que possible, mais sans priorité.
- Permettre l'ajout de toute commande de l'API publique du contrôleur.
- Garantir une priorité absolue pour les commandes critiques (Stop --> l'argument immediate est interne à la méthode stop, donc invisible pour le worker).
- Gérer des séquences complexes (ex : scan 2D) nécessitant d'attendre la fin d'un mouvement avant d'en lancer un autre, sans bloquer la lecture de position.
- Être robuste, simple à maintenir, et compatible avec l'architecture Qt/thread unique.

## Cas d'usage principaux
- Lecture de position en continu (fond)
- Mouvement simple (move_to, home, etc.)
- Scan 2D séquencé (enchaînement de mouvements avec wait_move_manager)
- Interruption immédiate d'un mouvement ou d'un scan par Stop
- Ajout de commandes concurrentes (UI, scripts, etc.)

## Cas d'usage secondaires ou limites (et comportements attendus)
- **Plusieurs Stop à la suite** : Non bloquant, la file prioritaire se vide aussi vite que possible, aucun effet secondaire.
- **Commande Move pendant un scan** : Non prise en compte, la file normale est verrouillée en mode Scanning, commande ignorée ou rejetée (log possible).
- **Stop alors qu’aucun mouvement n’est en cours** : Même comportement que plusieurs Stop, aucun effet si déjà à l’arrêt.
- **Commande Home pendant un mouvement** : Acceptée, le worker envoie d'abord Stop (immediate=False), puis Home.
- **File de commandes qui grossit très vite** : Peu probable en manuel, en batch (scan) le volume n'est pas critique, traitement séquentiel.
- **Commande qui échoue (erreur matérielle, timeout)** : Message d'erreur remonté (signal Qt, log), arrêt du scan si en cours.
- **Lecture de position qui échoue ou prend trop de temps** : Pas critique, info remontée, le système continue.
- **Commande prioritaire (Stop) pendant exécution normale ou scan** : Stop vide la file normale, puis est exécutée immédiatement.
- **Batch de scan** : En mode Scanning, commandes injectées en batch, file normale verrouillée. Plusieurs scans à la suite = plusieurs batchs traités séquentiellement. **Avant d'injecter un batch, la file normale doit être purgée pour garantir l'absence de commandes parasites après le scan.**

## Choix d'architecture (solution retenue)
- **Double file** :
    - File prioritaire (Stop) : traitée en premier si non vide.
    - File normale : toutes les autres commandes (Move, Home, batch de scan, etc.).
    - **En mode batch/scan** : la file normale est verrouillée, seules les commandes du batch sont présentes et traitées séquentiellement. Les commandes extérieures sont ignorées/rejetées tant que le scan n'est pas terminé. **Avant d'injecter un batch, la file normale est systématiquement purgée.**
    - **Commande de fond get_position** : n'est jamais stockée, mais exécutée automatiquement dès que les deux files sont vides (lecture continue de la position).
- **Logique du worker** :
    1. Si file prioritaire non vide → traiter la commande prioritaire (Stop)
    2. Sinon si file normale non vide → traiter la commande normale (ou le batch en mode Scanning)
    3. Sinon → exécuter get_position (lecture continue)
- **Robustesse** : un Stop peut toujours interrompre un scan ou un mouvement, la file normale est vidée si besoin.

## États du worker
- Idle : aucune commande en cours
- Moving : mouvement en cours
- Scanning : séquence de scan en cours (file normale verrouillée)
- Emergency/Stopped : interruption immédiate

## TODO détaillée (découpage production)

- [x] PRD validé et cas d'usage listés *2/10*
    - [x] Relire et valider le PRD avec les cas d'usage principaux *1/10*
    - [x] Lister les cas d'usage secondaires ou limites (ex : Stop pendant scan, ajout concurrent) *1/10*
- [ ] Définir la structure des files de commandes *3/10*
    - [] Implémenter la double file (prioritaire + normale) *1/10*
        - Utilisation de deux objets `queue.Queue` (thread-safe) :
            - `queue_prioritaire` pour les commandes Stop (toujours traitée en premier)
            - `queue_normale` pour toutes les autres commandes (Move, Home, batch, etc.)
        - En mode batch/scan, la file normale est verrouillée et purgée avant injection du batch.
    - [ ] Définir la structure d'une commande (attributs, priorité, etc.) *1/10*
        - Une commande est un objet (ex : `StageCommand`) avec :
            - `cmd_type` (enum StageCommandType)
            - `args` (liste d'arguments)
            - `kwargs` (dictionnaire d'arguments optionnels)
            - `callback` (optionnel, pour retour asynchrone)
            - `is_batch` (booléen, True si la commande fait partie d'un batch)
    - [ ] Adapter la classe StageCommand et StageCommandType pour le batch *1/10*
        - Ajout d'un type de commande spécifique pour le batch (ex : `SCAN_BATCH`)
        - Les commandes du batch sont injectées dans la file normale en mode Scanning, la file est verrouillée jusqu'à la fin du batch.
- [ ] Implémenter la gestion des priorités dans le worker *4/10*
    - [ ] Ajouter la logique d'injection et de traitement des files *1/10*
    - [ ] Modifier la boucle du worker pour respecter la logique (Stop > normale > get_position) *1/10*
    - [ ] Gérer le verrouillage/déverrouillage de la file normale en mode batch/scan *1/10*
    - [ ] Gérer la purge/annulation des commandes non prioritaires si besoin (purge systématique avant batch) *1/10*
- [ ] Implémenter la lecture de position en continu *2/10*
    - [ ] Définir la fréquence/stratégie d'appel de get_position *1/10*
    - [ ] S'assurer que la lecture ne bloque jamais une commande prioritaire *1/10*
- [ ] Implémenter la gestion des séquences/scans *3/10*
    - [ ] Définir l'état Scanning et la logique d'enchaînement *1/10*
    - [ ] Adapter wait_move_manager pour la nouvelle logique *1/10*
    - [ ] Permettre l'interruption d'un scan par Stop *1/10*
- [ ] Ajouter les tests unitaires/scénarios critiques *2/10*
    - [ ] Tester Stop pendant scan *1/10*
    - [ ] Tester ajout concurrent de commandes *1/10*
- [ ] Documenter la logique et les états dans le code *1/10*
    - [ ] Ajouter des commentaires clairs sur la gestion des priorités, du batch, de la purge et de la lecture continue *1/10*

---

*Ce découpage doit être validé avant toute implémentation. Chaque sous-tâche doit être réalisée et cochée individuellement.*
