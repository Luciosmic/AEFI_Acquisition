---
type: atome::solidai-atome
tldr: "Afficher des panneaux déplaçables avec leur barre de tâches, et garder leur disposition dans un fichier propre au post-traitement."
code: ["[[external_modules/aefi_post_processor_module/interface/shell/post_processor_window.py]]"]
cause_de_changement: outil
---
# post_processor_window — Intention

## Rationale

Le post-traitement était une fenêtre fixe à trois zones : l'opérateur ne pouvait ni cacher la carte pour lire le journal, ni ranger les panneaux comme dans l'acquisition. Une disposition enregistrée au même endroit que celle de l'acquisition ferait de chaque application l'écraseuse de l'autre.

## Responsibility

- Poser les panneaux qu'on lui donne dans le conteneur emprunté à l'acquisition, et les lister dans la barre de tâches par groupe.
- Restaurer la disposition au lancement et l'enregistrer à la fermeture, dans le fichier qu'on lui indique (jamais `~/.aefi_acquisition_layout.dat`).
- Écrire `window.shown` dans le journal à la première ouverture : c'est le signal que le test de lancement attend.

## Design

- Sur le modèle de `src/interface/shell/dashboard.py`, sans rien de l'acquisition : pas de panneau « External Modules », pas de service. La fenêtre reçoit des `PanelSpec` déjà construits par `shell_wiring`.
- Les pièces empruntées (`WindowsCarrier`, `ModernTaskbar`, leurs modèles et le presenter de la barre) viennent de `aefi_acquisition_upstream`, jamais de `src/` directement.
- Une disposition illisible ne bloque pas l'ouverture : l'échec est noté dans le journal et la disposition par défaut s'applique.
