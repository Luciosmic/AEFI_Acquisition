# git_software_provenance_reader — Intention

## Rationale

Ce qui est figé dans le code (mapping voies ADC → axes I/Q, conversion
codes → volts, règle causale de collecte des échantillons) n'est pas
exporté : le document de paramètres renvoie au commit. Sans commit, ces
faits sont perdus ; sans drapeau « arbre modifié », un balayage fait avec du
code non commité passe pour reproductible. Le 2026-10-02, la version du
logiciel d'un balayage a dû être reconstituée à la main.

## Responsibility

- Implémenter `ISoftwareProvenancePort` : nom du logiciel, version
  (`pyproject.toml`), commit (`git rev-parse HEAD`), branche, arbre modifié
  (`git status --porcelain` non vide, fichiers non suivis compris).

## Design

- `subprocess` + `tomllib` de la bibliothèque standard ; dépôt = racine du
  projet déduite de l'emplacement du module (pas du répertoire courant).
- Délai maximal par commande git (5 s) : un dépôt bloqué ne bloque pas le
  balayage.
- git absent, hors dépôt, délai dépassé → champ `None` et `unknown_reason` ;
  jamais d'exception.
- L'exécution de git est injectable : les tests ne dépendent pas de l'état
  du dépôt.
