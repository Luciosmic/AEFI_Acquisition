# runtime_data_guard — Intention

## Rationale

Des tests ouvrent `.aefi_acquisition/` (calibrations, derniers réglages, configurations) relativement au dossier où ils tournent. Sans garde-fou, lancer la suite dans le dossier où l'application tourne sur le banc écrase ces fichiers, qui ne sont pas versionnés : aucun git ne les restitue, et une calibration qui a pris une journée de mesure se perd sans message. Le 2026-11-12, trois fichiers de réglages ont ainsi été réécrits par un lancement de tests fait sur `main`.

## Responsibility

- Refuser de lancer les tests dans un dossier dont la branche est `main` (celui de l'exécution réelle), sauf `AEFI_ALLOW_TESTS_ON_MAIN=1`.
- Copier les données du banc avant la session de tests, les comparer après, remettre en place ce que les tests ont modifié ou supprimé, et dire à voix haute ce qui a changé.
- Garder la copie d'avant les tests quand quelque chose a changé : rien n'est perdu même si la restauration surprend.

## Design

- Branche `main`, pas nom de dossier : un dossier renommé reste protégé. Sans git, ou en HEAD détaché, on ne refuse pas (on ne bloque pas ce qu'on ne sait pas lire).
- Les fichiers créés par les tests sont signalés, pas supprimés : supprimer à l'aveugle est plus risqué que laisser.
- `logs/` est exclu : lourd, et ce n'est pas un réglage.
- La restauration ramène aussi les écritures d'une application qui tournerait en même temps : c'est dit dans le rapport, et c'est préférable à laisser les tests gagner.
- Ce garde-fou répare, il ne corrige pas : un test qui écrit dans les données du banc doit viser un dossier temporaire. Le rapport nomme les fichiers pour les trouver.
- Branché depuis `conftest.py` à la racine (`pytest_sessionstart` / `pytest_sessionfinish`).
