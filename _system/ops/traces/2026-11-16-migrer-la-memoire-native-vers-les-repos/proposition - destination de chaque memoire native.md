---
statut: to_validate
---
# Destination de chaque mémoire native de ce PC

La mémoire native de Claude Code tient 36 fichiers sur ce PC : 31 pour `AEFI_Acquisition_dev`, 2 pour `Hardware - Caracterisation`, 3 pour `GRAPHE-THESE` (index compris).
Sur les 33 souvenirs, 16 deviennent des règles, 9 complètent un fichier qui existe déjà, et 8 sont périmés ou déjà écrits ailleurs.
Une fois tout porté, la mémoire native se coupe par `autoMemoryEnabled: false` dans `~/.claude/settings.json`. Les fichiers restent sur le disque, mais aucune session ne les charge plus.

## 1. Règles de travail : une section de l'inject de ce repo

L'inject `contexte-du-repo-aefi-acquisition` est chargé à chaque session : une règle n'agit que si elle y est.
Section proposée, « Règles apprises au banc », une ligne par règle :

1. **Tests hors du checkout réel.** Jamais de `pytest` dans `C:\Users\manip\AEFI_Acquisition` : les tests y réécrivent `.aefi_acquisition/configs/`, que git ne restaure pas. On vérifie ce qui part sur `main` dans une copie jetable, avant le push.
2. **Mise à jour du checkout réel.** Fermer l'application et le post-processeur avant. Après, comparer la casse des dossiers de `git ls-files` à celle du disque : Windows ne renomme pas un dossier dont seule la casse change, et Python échoue à l'import. Corriger par un renommage en deux temps.
3. **Tests localisés.** Lancer les tests des modules modifiés et de leurs importeurs directs ; la suite complète seulement avant `main`, quand l'écart est large. Cette ligne tient jusqu'à l'installation du standard du plan « standard tests localisés ».
4. **Parcours de l'opérateur.** Une fonction d'interface marche quand le clic atteint le service dans la composition de `main.py`, après `gc.collect()`. Un presenter est gardé vivant par un parent Qt, jamais par son service.
5. **Tranche testable d'abord.** Le premier livrable se lance au banc, puis un point, un commit, un retour de l'humain.
6. **Délégation suivie.** Un sous-agent fait au plus un commit ou un petit lot borné, puis rend compte. La session résume et attend l'accord avant le point suivant, et suit le `trace.log` du sous-agent en direct.
7. **Prompt d'un sous-agent.** Il nomme le mécanisme existant à réutiliser (`ExclusiveControl` / `take_all` pour l'exclusion, les actions de l'application comme « to-center » pour le mouvement) et les standards qui s'appliquent, même pour un outil de banc. « Minimal » borne le périmètre, jamais la structure.
8. **Pas d'automatisme caché.** Le labo change souvent de personnes : un état visible et une action que l'humain déclenche, avec confirmation.
9. **Un nom par concept.** Une seule clé par grandeur dans les configs, l'interface et le code, en unité physique. Un code de registre n'existe que dans l'adaptateur qui écrit le registre.
10. **Code présent n'est pas fonction validée.** Demander à l'humain avant de marquer une fonction matérielle comme faite dans `goals.md` ou `tasks.md`.
11. **Sigles développés.** Chaque sigle est développé à sa première occurrence : intention, commentaire, commit, réponse.
12. **Vue en direct au banc.** Un script qui pilote le matériel montre en direct sa phase, ses signaux, ses résultats et un bouton d'arrêt, jamais un journal seul.
13. **Sorties de caractérisation.** Elles vont dans `C:\Users\manip\Desktop\AEFI_Acquisition_Exports\HARDWARE-CHARACTERIZATION\` seulement. Rien n'est copié dans `0_inbox/data-a-interpreter/` du vault : l'humain décide. Un dossier temporaire créé dans le repo est retiré avant de rendre la main.
14. **Repos de thèse sur ce PC.** On travaille dans les clones de `C:\Users\manip\Desktop\THESE-LUIS-EXPERIMENTAL\`, poussés sur GitHub. Les repos Dropbox sont en lecture seule pour git, et le hook `refuser-git-dans-dropbox` le garantit. Si uv bute sur un lien Dropbox, `UV_LINK_MODE=copy`.
15. **Compte rendu de mesure.** Une phrase de verdict, un tableau court attendu contre mesuré, une ou deux phrases d'interprétation ; les branchements en petit tableau. Pas de tableaux empilés sans phrase entre eux.

## 2. Compléments à un fichier existant

| Souvenir | Destination | Ce qui s'ajoute |
|---|---|---|
| Mesure différentielle | `_system/self/goals.md`, section du différentiel | La décision du 2026-10-15 : champ primaire seulement, piste « scan de référence puis scan de mesure » non décidée, compromis sur la dérive lente |
| Refonte des agrégats du scan | `_system/ops/tasks.md` | Les points ouverts absents de `tasks.md` : états terminaux du `Scan`, commande de réconciliation, événement d'échec d'une source facultative, unités de `Position2D`, mesure du temps par point |
| Carte des contextes du domaine | `_system/ops/tasks.md` | La question ouverte « détection synchrone et débit de l'ADC vers `aefi_device` ? » et le tableau « Migrations réalisées » de `goals.md`, périmé |
| Skills d'instrument globaux | `_system/self/goals_dev_hardware.md` | L'objectif et l'ordre : oscilloscope fait, puis mouvement de la colonne, puis système AEFI ; la structure du skill de l'oscilloscope à reproduire ; un venv dédié, car `uv run` d'un script PEP 723 échoue ici |
| POC n8n | `_system/ops/tasks.md` | Une ligne : archivé sur `origin/feature/n8n-ddd-workflow-viz`, avec ses deux pannes connues à la reprise |
| Ports série du banc | `src/infrastructure/hardware/CLAUDE.md` du Banc-test-II, si absent | COM5 = carte LSM9DS1 et ancien LIDAR, COM11 = port natif de la carte mère, muet |
| Résultats en tableaux | `Hardware - Caracterisation`, consigne de session à la racine | La règle 15, pour les sessions ouvertes depuis ce repo |
| Portage Windows d'Ars Umbris | `windows/README.md` de `~/arsumbris/arsumbris`, branche `windows-port` | Le seul point absent : `python3` mène au raccourci du Microsoft Store, donc un hook Python s'appelle par le chemin complet de l'interpréteur |
| Plan de synchro git continue | Ce dossier de tâche, en attendant le Mac | Le texte du plan, versionné ici, à porter dans sh-agent-os depuis le Mac : ses repos Dropbox sont en lecture seule pour git sur ce PC |

## 3. Abandonnés

| Souvenir | Raison |
|---|---|
| Pas d'import du domaine dans un widget | Couvert par le standard SolidAI du presenter, qui n'importe jamais le domaine |
| Worktree par contexte | Couvert par l'inject du repo, section « Branches et worktrees » |
| Graphique local plutôt qu'Artifact | L'outil Artifact est désactivé |
| Journal de progression d'un sous-agent dans le scratchpad | Remplacé par le `trace.log` versionné de sh-agent-os ; le suivi en direct passe dans la règle 6 |
| Pont n8n par serveur HTTP | Vit avec le POC sur sa branche archivée |
| État du retrait de StepScan | Déjà dans `tasks.md`, § « Reprise sur une autre machine » |
| Scan comme contexte cohésif, état du domaine scan d'octobre | Appliqués dans le code ou périmés : scan Z supprimé (`ab6db22`), agrégat FlyScan remplacé par l'ADR-004 |
| Journal d'événements comme filet de sécurité | Déjà dans `_system/ops/event_store.md` |
| Restructuration du Banc-test-II, LIDAR sur COM9 | Déjà dans le plan et l'`index.md` du Banc-test-II, et dans le `CLAUDE.md` et les notes du pilote LIDAR |

## Ce qui demande ton accord

- Ajouter la section des 15 règles à l'inject : elle prend effet à la session suivante.
- Écrire dans deux autres repos de ce PC (Banc-test-II, `Hardware - Caracterisation`) et dans `~/arsumbris/arsumbris`, avec un commit local dans chacun, sans push.
- Couper la mémoire native une fois tout porté.
