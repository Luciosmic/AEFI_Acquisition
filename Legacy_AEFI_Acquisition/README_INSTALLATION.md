# Guide d'installation EFImagingBench

Ce guide explique comment installer et lancer facilement l'application EFImagingBench sans avoir besoin de connaissances en programmation.

## Installation pour le technicien

1. Double-cliquez sur le fichier `create_desktop_shortcut.bat`
2. Un raccourci nommé "EFImagingBench" sera créé sur votre bureau
3. Vous pouvez maintenant lancer l'application en double-cliquant sur ce raccourci

## En cas de problème

Si l'application ne démarre pas correctement :

1. Vérifiez que l'environnement virtuel Python (dossier `venv64`) est correctement installé
2. Assurez-vous que tous les fichiers sont au bon emplacement
3. Contactez le responsable du développement

## Structure des fichiers

- `start_EFImagingBench.bat` : Script qui lance l'application
- `create_desktop_shortcut.bat` : Script qui crée le raccourci sur le bureau
- `EFImagingBench_App/` : Dossier contenant l'application

## Notes techniques (pour le développeur)

Le script de lancement effectue les opérations suivantes :
1. Active l'environnement virtuel Python (`venv64`)
2. Lance l'interface graphique EFImagingBench
3. Affiche les erreurs éventuelles et attend une action de l'utilisateur en cas de problème
