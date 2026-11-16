---
type: atome::solidai-atome
tldr: "Décider ce que le panneau Logs affiche (une ligne par message, couleur selon la gravité) et ouvrir le fichier journal à la demande, sans Qt."
code: ["[[external_modules/aefi_post_processor_module/interface/logs_presenter/logs_presenter.py]]"]
cause_de_changement: outil
---
# logs_presenter — Intention

## Rationale

Le journal est le seul endroit où l'opérateur lit ce que le post-traitement a fait : le bilan d'un traitement, l'étape qui a échoué, les avertissements. Si le panneau décidait seul de la couleur d'une ligne et de l'ouverture du fichier, cette logique ne se testerait qu'avec une fenêtre ouverte, et le panneau cesserait d'être humble.

## Responsibility

- Recevoir chaque message du journal (niveau et texte) et le donner à la vue avec sa couleur : rouge pour une erreur, orange pour un avertissement.
- Ouvrir le fichier journal quand l'opérateur le demande (récit R17), en le notant dans le journal.
- Dire à la vue où est le fichier.

## Design

- Classe Python sans Qt : elle ne connaît de la vue que `set_location`, `append_line(text, color)`, `open_file(path)` et le signal `open_log_requested`. Les tests la branchent sur une vue Fake.
- Le puits du `FeedbackLogHandler` est `append_feedback` ; c'est `interface/shell` qui l'y attache, le presenter n'importe pas l'infrastructure.
- La vue est `interface/logs_panel/logs_panel.py`, humble : ni type ni intention (A1), ses tests sont ceux de ce presenter.
