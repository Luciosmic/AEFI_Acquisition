# logging_setup — Intention

## Rationale

Le tableau de bord lance le post-traitement comme un processus séparé, dont personne ne lit la console. Le traitement par lot tourne avant l'ouverture de la fenêtre. Sans journal, un scan qui échoue au retraitement ne laisse aucune trace, et l'opérateur ne sait ni quels scans ont été recalculés, ni avec quels angles du capteur.

## Responsibility

- Configurer une seule fois le journal du processus : chaque module écrit par `logging.getLogger(__name__)`, jamais par `print`.
- Écrire chaque lancement dans `.aefi_acquisition/logs/post_processor.log`, réécrit à chaque lancement, lisible sans la fenêtre.
- Alimenter le cadre « System Feedback » de la fenêtre, y compris avec les messages émis par le traitement par lot avant son ouverture.

## Design

- Niveau réglé par `AEFI_LOG_LEVEL`, comme l'application principale (INFO par défaut ; DEBUG montre chaque étape du pipeline et chaque scan à jour laissé tel quel).
- Le fichier ne suit pas `AEFI_LOG_FILE` : le processus hérite de l'environnement de l'application, et la même variable tronquerait le journal de l'application.
- Messages au format `evenement cle=valeur`, qui portent toujours le nom du scan (son dossier d'acquisition) pour corréler les lignes.
- `FeedbackLogHandler` garde les messages tant que la fenêtre n'existe pas, puis les rejoue à son branchement. Il ne transmet que le message : la trace d'erreur complète va au fichier.
- Le cadre et le gestionnaire vivent sur le fil de la fenêtre : le traitement par lot et le présentateur tournent tous deux sur ce fil.
