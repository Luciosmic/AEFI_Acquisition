---
type: constat::sh-agent-os
genere_par: "[[tache - migrer la memoire native vers les repos]]"
doc_type: constat
---

# Où est passée chaque mémoire native du PC du labo

La mémoire native de Claude Code (`~/.claude/projects/*/memory/`) est coupée le 2026-11-16 par `autoMemoryEnabled: false` dans `~/.claude/settings.json`.
Ses fichiers restent sur le disque, mais aucune session ne les charge plus.
Son contenu utile est désormais dans les repos :

| Contenu | Où |
|---|---|
| 15 règles de travail (tests hors du checkout réel, délégation suivie, vue en direct au banc…) | Inject `contexte-du-repo-aefi-acquisition` de ce repo, section « Règles apprises au banc » |
| Décision du 2026-10-15 sur la mesure différentielle | `_system/ops/tasks.md`, section « Mesure différentielle » |
| Question du rangement de la détection synchrone, tableau périmé de `goals.md`, POC n8n archivé | `_system/ops/tasks.md`, section « Reprise sur une autre machine » |
| Objectif et structure des skills d'instrument globaux | `_system/ops/tasks.md`, section « Skills d'instrument globaux » |
| Compte rendu de mesure en tableaux équilibrés | Repo `Hardware - Caracterisation`, inject `compte-rendu-de-mesure` de son profil de session |
| Port COM11 muet | Banc-test-II, `src/infrastructure/hardware/CLAUDE.md` |
| `python3` mène au raccourci du Microsoft Store | `~/arsumbris/arsumbris`, `windows/README.md` (branche `windows-port`) |
| Plan de synchro git continue | Ce dossier, en attendant d'être porté dans sh-agent-os depuis le Mac |

Écarts avec la proposition : les compléments prévus dans `goals.md` et `goals_dev_hardware.md` sont allés dans `tasks.md`.
`goals_dev_hardware.md` ne traite que la compensation en fréquence de la sonde Narda, et `tasks.md` a déjà une section sur le différentiel.
Les points ouverts du refactoring du scan y étaient déjà tous : rien à ajouter.

Abandonnés, car déjà écrits ailleurs ou périmés : pas d'import du domaine dans un widget, worktree par contexte, graphique local plutôt qu'Artifact (outil désactivé), journal de progression dans le scratchpad (remplacé par le `trace.log`), pont n8n, état du retrait de StepScan, scan comme contexte cohésif, état du domaine scan d'octobre, journal d'événements, restructuration du Banc-test-II, LIDAR sur COM9.
