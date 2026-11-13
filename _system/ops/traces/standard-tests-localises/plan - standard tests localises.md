# Plan — Standard SolidAI des tests localisés

**État :** standard et mise à jour de commande rédigés le 2026-11-13 sur le PC du labo, rien n'est soumis à Packmind (le tunnel vers le serveur était fermé).
**Prochaine action :** sur le Mac, faire choisir à l'humain entre appliquer les deux changements ou seulement le premier ; puis ouvrir le tunnel Packmind, soumettre et réinstaller les règles dans les repos.

## Pourquoi

Le 2026-11-13, après un changement confiné au balayage en fréquence, l'agent a lancé toute la suite de tests : 1871 tests en 4 à 6 minutes. Les tests du seul contexte touché donnaient le même verdict : 74 tests en 7 secondes.

L'humain : « on est trop agressifs sur les tests alors qu'on a des couches découplées normalement pour ne pouvoir tester que des régions localisées ». Il a demandé une règle SolidAI injectée au démarrage de chaque session.

Les standards SolidAI installés dans `.claude/rules/packmind/` sont injectés au démarrage, sur le PC comme sur le Mac : c'est le canal retenu.

## Changement 1 — nouveau standard

**Nom :** SolidAI — Tests localisés : modules modifiés, importeurs directs, parcours opérateur

**Description :** des couches découplées par des ports permettent de vérifier localement un changement localisé. L'agent lance les tests des modules modifiés et de leurs importeurs directs. Il ajoute le test du parcours de l'opérateur quand l'interface change, et ne contrôle les types que des fichiers modifiés. La suite complète est réservée au passage sur main, quand l'écart est large.

**Règles :**

1. Après un changement localisé, lancer `pytest` sur les dossiers `_tests/` des modules modifiés, jamais sur `src/` entier.
2. Trouver les importeurs directs en cherchant dans `src/` le chemin d'import du module modifié (par exemple `domain.frequency_sweep.value_objects.frequency_grid`), et lancer aussi leurs `_tests/`.
3. S'arrêter aux importeurs directs : le découplage par ports rend ce premier cercle suffisant.
4. Quand le changement touche `src/interface/`, lancer aussi le test de câblage du panneau concerné : vraie fonction de câblage, `gc.collect()`, clic jusqu'au service.
5. Lancer la suite complète (`pytest src/`) seulement avant de mettre à jour `main`, et seulement quand l'écart depuis `main` est large.
6. L'écart est large quand `git diff --stat main...HEAD` touche deux contextes bornés ou plus, `domain/shared_kernel/`, `application/shared/` ou `infrastructure/persistence/acquisition_parameters/`.
7. Contrôler les types des seuls fichiers modifiés, comparés à leur version au commit précédent ; ne signaler que les erreurs nouvelles, jamais le total du dépôt.

**Portée :** aucune, pour que le standard s'applique toujours (`alwaysApply: true`). Les 21 standards installés n'ont pas de portée. Une portée par chemin risquerait de ne charger la règle qu'à l'ouverture d'un fichier correspondant. Si Packmind exige une portée, mettre `src/**/*.py` et vérifier que la copie installée garde `alwaysApply: true`.

**Réserve :** Packmind conçoit ses standards pour des règles vérifiables à la lecture du code. Celle-ci porte sur la façon de travailler de l'agent. Elle ne se vérifie qu'après coup, sur les commandes lancées et sur le `git diff --stat`. Cela ne gêne pas son injection.

## Changement 2 — mise à jour de la commande de vérification avant pull request

`.packmind/commands/pre-pr-quality-check.md` (installée dans `.claude/commands/`) est la seule commande qui dit quels tests lancer, et elle contredit la règle :

- étape 3 « Type check » : `uv run mypy src/domain/ src/application/ --ignore-missing-imports`, sur tout le code ;
- étape 4 « Run tests » : `uv run pytest src/ -v --ignore=src/infrastructure/hardware`, avant chaque pull request, y compris vers `develop`.

Proposition :
- Les étapes 3 et 4 renvoient au nouveau standard par son nom, sans recopier ses règles, pour ne pas vieillir avec lui.
- La suite complète de l'étape 4 n'est gardée que pour le cas de la règle 5.
- La phrase finale de l'étape 5 (« All five steps must pass ») devient : les cinq étapes, à la portée choisie aux étapes 3 et 4.

Aucun skill local ne contredit la règle. Ont été vérifiés : la création de service, de présentateur, de port et d'événement, le lancement de l'application, la synchronisation des standards et l'onboarding Packmind. Les skills présents seulement sur le serveur Packmind n'ont pas pu être vérifiés : relancer `packmind-cli skills list` une fois le tunnel ouvert.

## Décision à prendre

Appliquer les deux changements, ou seulement le standard. Recommandation : les deux. Sans le second, la commande continue de pousser à la suite complète.

## Comment appliquer

1. Ouvrir le tunnel vers le serveur Packmind (skill `get-solidai-standards`, qui l'ouvre avant de synchroniser).
2. Lancer le skill `packmind-update-playbook` avec ce plan en entrée. Reprendre le rapport de changements ci-dessus sans refaire l'analyse, et suivre sa procédure d'application selon la version du CLI Packmind du Mac (0.23.0 sur le PC).
3. Réinstaller les règles dans les repos qui reçoivent les standards SolidAI, et vérifier que la copie installée du nouveau standard est bien dans `.claude/rules/packmind/` avec `alwaysApply: true`.
4. Le standard ne s'applique qu'aux sessions ouvertes après l'installation.

## Points ouverts

- Pas de nombre de commits dans le critère « écart large » : l'humain n'en a pas donné, et les critères de la règle 6 se vérifient mécaniquement. N'en ajouter un que s'il le demande.
- Une règle possible, propre au PC du labo et donc hors de ce standard commun : lancer la suite complète d'avant main dans une copie temporaire, jamais dans `C:\Users\manip\AEFI_Acquisition`, car pytest y écrase les configurations locales non suivies.
