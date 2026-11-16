---
doc_type: constat
---

# Le journal passe sous `infrastructure/logging/` dès 1.2, pas en 1.6

Le découpage demande en 1.2 de typer `logging_setup_intention.md` (`atome`, cause `outil`) en laissant son déplacement à 1.6, et exige `V2` = 0 erreur.
Les deux ne tiennent pas ensemble : sur place, `solidai verify` renvoie `solidai-cause-contredit-la-couche` (A15 : la cause `outil` appartient à `infrastructure/` ou `interface/`).

Décision : avancer le déplacement. `logging_setup.py` et son intention vivent dans `infrastructure/logging/`, imports qualifiés mis à jour (`composition_root.py`, `visualisation/app.py`, `visualisation/composition_root_visualisation.py`).
Conséquence : A1 exige un `_tests/` à l'atome ; les deux tests du journal (`FeedbackLogHandler`, `configure_logging`) quittent `_tests/observability_test.py` pour `infrastructure/logging/_tests/logging_setup_test.py`.
L'étape 1.6 n'a plus à déplacer ce fichier ; elle garde le panneau Logs et son presenter.

Autre écart constaté : les sept scripts déplacés vers `tool/` importaient des chemins morts (`tools.aefi_post_processor_modules…`, `tests`, `processing`). Ils importent maintenant `aefi_post_processor_module…` après un raccord de `sys.path` en tête de script (`external_modules/`), ce qui permet le test d'import par `runpy` depuis la racine du worktree.
