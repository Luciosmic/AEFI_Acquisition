---
type: atome::solidai-atome
tldr: "Dessiner une étape du traitement en six cartes de couleur (en phase et en quadrature, sur x, y et z), sans Qt."
code: ["[[external_modules/aefi_post_processor_module/interface/figure_factory/figure_factory.py]]"]
cause_de_changement: outil
---
# figure_factory — Intention

## Rationale

L'opérateur lit un traitement dans ses cartes : sans elles, une étape calculée reste un tableau de chiffres. Le tracé existait dans l'ancienne fenêtre, collé à sa vue ; le panneau Carte en a besoin sans reprendre cette fenêtre.

## Responsibility

- Rendre une `Figure` matplotlib de deux lignes (en phase, quadrature) et trois colonnes (x, y, z) pour les grilles, l'étendue et le titre donnés.
- Écrire « No Data » dans une case dont le canal manque.

## Design

- Déplacé tel quel de l'ancienne fenêtre : le panneau Carte garde son tracé en tranche 1. Il passe au panneau emprunté `ScanVisualizationPanel` en tranche 4, avec les Profils.
- Aucun import de Qt : le tracé se teste sur une `Figure` seule, et le panneau l'embarque dans son canvas.
