---
type: widget::solidai-hexagonal
tldr: "Montrer les objets mesurés du registre, et en ajouter, renommer ou supprimer un, sans attendre le démarrage d'une acquisition."
code: ["[[src/interface/widgets/panels/measured_object_registry_panel.py]]"]
cause_de_changement: interface
---
# measured_object_registry_panel — Intention

## Rationale

Les sélecteurs des panneaux Scan, Continuous Reading et Frequency Sweep ne
savent qu'ajouter un objet. Un objet nommé trop vite (« hexagone_metallique »
pour un cylindre à base hexagonale), ou créé par erreur, restait proposé à
chaque acquisition, sans autre recours que modifier le fichier du registre à
la main.

## Responsibility

- Montrer les objets mesurés du registre, triés par nom.
- Ajouter un objet, renommer l'objet choisi (bouton ou double-clic),
  supprimer l'objet choisi après confirmation.
- Afficher en mots l'issue du dernier geste : fait, ou refusé avec sa raison.

## Design

- N'émet que des demandes (`register_requested`, `rename_requested`,
  `delete_requested`) ; `MeasuredObjectPresenter` les transmet au service.
  Aucune règle d'orthographe ici : elle est dans l'aggregate.
- La liste suit les événements du registre par le presenter : un ajout fait
  depuis un sélecteur y apparaît aussitôt.
- La confirmation de suppression dit ce qui reste : les exports déjà écrits
  gardent le nom et l'identité de l'objet.
- Dialogues injectables (`ask_name`, `confirm_delete`) pour les tests.
- Importe le DTO applicatif, jamais un type du domaine.
