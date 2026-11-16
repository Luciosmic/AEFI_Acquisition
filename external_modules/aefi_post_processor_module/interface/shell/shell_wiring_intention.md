---
type: atome::solidai-atome
tldr: "Assembler la fenêtre : créer ses panneaux et leurs presenters, brancher le journal sur le panneau Logs, et rendre la fenêtre prête à s'afficher."
code: ["[[external_modules/aefi_post_processor_module/interface/shell/shell_wiring.py]]"]
cause_de_changement: outil
---
# shell_wiring — Intention

## Rationale

Le point d'entrée `composition_root.py` doit rester mince : lire les arguments, régler les chemins, lancer. Si l'assemblage des panneaux et des presenters y vivait, il ne se testerait qu'en lançant tout le processus, et chaque nouveau panneau l'alourdirait.

## Responsibility

- Construire chaque panneau et son presenter (Acquisitions, Carte, Logs), les passer à la fenêtre avec leur groupe de barre de tâches : Données, Visualisation, Système.
- Brancher les presenters entre eux : choisir une acquisition fait montrer ses étapes par la Carte, et la fin d'un traitement la fait relire.
- Attacher le puits du journal au presenter des Logs, pour que les messages émis avant l'ouverture s'y rejouent.
- Rendre la fenêtre et les presenters : l'appelant les garde en vie.

## Design

- Aucun import d'infrastructure : les services viennent de `headless_wiring`, le journal arrive déjà configuré par `composition_root.py`. Il rend un `Shell` (la fenêtre et les presenters) ; l'appelant lui demande de lister ou de traiter.
- Ne crée pas la `QApplication` : c'est le point d'entrée qui la possède.
