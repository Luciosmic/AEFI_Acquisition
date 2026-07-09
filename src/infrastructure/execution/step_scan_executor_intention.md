# step_scan_executor — Intention

## Rationale

Implémentation concrète de `IScanExecutor` gérant l'exécution asynchrone d'un scan step-by-step avec synchronisation event-based sur les mouvements hardware Arcus (asynchrones par nature). Cette classe résout le problème de synchronisation motion/acquisition dans un thread dédié sans bloquer la UI.

## Responsibility

- Lancer le scan dans un thread daemon séparé (retour immédiat à `ScanApplicationService`).
- Pour chaque point : commander le mouvement → attendre `MotionCompleted` (event) → stabiliser → acquérir N mesures → moyenner → stocker dans l'agrégat → publier les événements.
- Gérer la pause (boucle d'attente sur `PAUSED`) et l'annulation (vérification avant chaque étape).
- S'abonner/désabonner de `motioncompleted`, `motionfailed`, `motionstopped`, `emergencystoptriggered`.

## Design

- **`threading.Event`** (`_motion_completed_event`) : synchronisation propre entre le callback du bus (thread handler) et la boucle principale (thread worker).
- **`_pending_motion_id`** : corrélation entre le mouvement demandé et l'événement `MotionCompleted` reçu — évite les faux positifs.
- **Désabonnement dans `finally`** : garantit le nettoyage même en cas d'exception.
- **Timeout 30s par point** : protection contre un hardware bloqué — configurable en TODO.
