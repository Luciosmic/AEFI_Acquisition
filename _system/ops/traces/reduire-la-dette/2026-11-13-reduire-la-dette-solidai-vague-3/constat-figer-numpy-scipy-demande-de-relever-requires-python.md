---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 3]]"
doc_type: constat
date: 2026-11-13
---

# Figer numpy et scipy demande de relever requires-python

**Étape sautée, rien n'est écrit dans `pyproject.toml`.**

Le venv d'ACQ tient numpy 2.3.5 et scipy 1.17.0, donc les contraintes visées sont `numpy~=2.3` et `scipy~=1.17`.
`pyproject.toml` déclare `requires-python = ">=3.10"`, et `uv.lock` résout aussi pour Python 3.10 (une fourche numpy 2.2.6, scipy 1.15.3).
numpy 2.3 et scipy 1.17 n'existent que pour Python 3.11 et plus.

Essai sur une copie de `pyproject.toml` et `uv.lock` hors du repo : `uv lock` échoue (« only supports >=3.11 ; consider using a more restrictive requires-python »).
Sans verrou résolu, `uv run pytest` ne part plus : la règle « les tests restent identiques » ne peut pas tenir.

## Ce qui reste à l'humain

1. Relever `requires-python` à `>=3.11` puis figer `numpy~=2.3` et `scipy~=1.17` (recommandé si le PC du banc tourne en 3.11 ou plus : le venv local est en 3.13).
2. Ou figer sur la plus haute version qui sert encore Python 3.10 (`numpy~=2.2`, `scipy~=1.15`) : A9 passe aussi, mais le verrou descend sous la version installée.

A9 accepte `==` ou `~=` (paramètre `autorises_si_figes` de solidai-atome) : l'un ou l'autre retire les 14 erreurs attendues.
