---
type: atome::solidai-atome
tldr: "Décider ce que le panneau Paramètres d'acquisition montre de l'acquisition choisie (objet mesuré, angles appliqués, convention, version du schéma, repli sur les angles idéaux), en lecture seule et sans Qt."
code: ["[[external_modules/aefi_post_processor_module/interface/acquisition_parameters_presenter/acquisition_parameters_presenter.py]]"]
cause_de_changement: outil
---
# acquisition_parameters_presenter — Intention

## Rationale

Le fichier des paramètres d'acquisition est le contrat entre l'acquisition et le post-traitement : il dit quel objet a été mesuré et avec quels angles de rotation. Sans panneau, l'opérateur ne voit pas avec quels angles une acquisition sera retraitée, ni pourquoi un scan retraité retombe sur les angles idéaux (fichier muet, convention refusée) : il lit le journal ou le JSON. Si le panneau composait seul les libellés et les cas (angles présents, absents, refusés), cette logique ne se testerait qu'avec une fenêtre ouverte, et le panneau cesserait d'être humble.

## Responsibility

- Recevoir le statut de l'acquisition choisie (celui que le catalogue a déjà lu) et donner à la vue un titre et des lignes libellé/valeur : l'objet mesuré, la version du schéma, les trois angles appliqués avec leur unité, la convention de rotation, l'origine des angles et la calibration quand le fichier les donne.
- Dire ce que le traitement utilisera : les angles de l'acquisition, les angles idéaux du gabarit quand le fichier ne dit rien, ou ces mêmes angles en repli quand le fichier décrit une rotation inutilisable, avec la raison.
- Afficher « non renseigné » pour ce que le fichier ne dit pas ; « Aucune acquisition sélectionnée » sans sélection.
- Ne lire ni n'écrire aucun fichier.

## Design

- Classe Python sans Qt, ni domaine, ni infrastructure : elle ne connaît de la vue que `set_title(texte)` et `set_rows([(libellé, valeur), ...])`, et du catalogue que le `AcquisitionStatusDTO` qu'on lui donne. Elle n'appelle aucun service : le presenter des Acquisitions lui passe le statut déjà lu, ce qui évite de relire le disque à chaque sélection. Les tests la branchent sur une vue Fake.
- La vue est `interface/acquisition_parameters_panel/acquisition_parameters_panel.py`, humble : ni type ni intention (A1), sans bouton ni champ éditable ; ses tests sont dans le `_tests/` de ce presenter.
