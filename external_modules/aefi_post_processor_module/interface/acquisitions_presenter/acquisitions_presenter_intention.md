---
type: presenter::solidai-hexagonal
tldr: "Décider ce que le panneau Acquisitions montre (type, objet, état, détail de chaque acquisition) et conduire le traitement à la demande : la sélection, ou tout ce qui est à recalculer, avec un bilan dans le journal."
code: ["[[external_modules/aefi_post_processor_module/interface/acquisitions_presenter/acquisitions_presenter.py]]"]
cause_de_changement: outil
appelle: ["[[external_modules/aefi_post_processor_module/application/acquisition_catalog_service/acquisition_catalog_service_intention^^i-api-acquisition-catalog-service]]", "[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service_intention^^i-api-post-processing-service]]"]
vues: ["[[external_modules/aefi_post_processor_module/interface/acquisitions_panel/acquisitions_panel.py]]"]
---
# acquisitions_presenter — Intention

## Rationale

Le lancement de l'ancienne fenêtre calculait avant d'afficher, dans une boucle sans nom ni test : l'opérateur ne voyait pas quelles acquisitions étaient à jour, ni pourquoi l'une avait échoué, sauf en lisant le journal. Le catalogue sait dire l'état de chaque acquisition sans rien écrire et le service sait traiter un scan, mais personne ne les appelle ensemble : sans ce presenter, le panneau devrait le faire, et son enchaînement (qui traiter, que faire d'un échec, quoi écrire dans le bilan) ne se testerait qu'avec une fenêtre ouverte. Le service de traitement ne peut pas appeler le catalogue (H14) : c'est ici que les deux se rencontrent.

## Responsibility

- Montrer chaque acquisition du dossier d'export : son nom, son type (pas à pas, à la volée), l'objet lu dans le nom du dossier tant que la tranche 2 n'est pas faite, son état (traitée, à recalculer, en échec) et le détail (pourquoi à recalculer, ou l'étape et le message de l'échec).
- Dire aux écouteurs quelle acquisition la sélection désigne, pour que la Carte la montre.
- Traiter à la demande : la sélection (même à jour), ou tout ce qui est à recalculer (tout, si forcé). Une acquisition qui échoue ne stoppe pas les suivantes : son échec, avec l'étape fautive, est rapporté au catalogue.
- Écrire le bilan dans le journal (`sync.finished` : traitées, à jour, en échec, avec l'étape de chaque échec ; avertissement s'il y a un échec), puis réafficher la liste et prévenir les écouteurs.
- Ouvrir le dossier de l'acquisition sélectionnée, ou celui de l'export.

## Design

- Classe Python sans Qt, ni domaine, ni infrastructure. Elle reçoit le catalogue, une fabrique `processor_factory(fichier)` qui rend le service lié au fichier d'étapes de l'acquisition et ce qu'il faut fermer, et un `parameters_provider()` appelé à chaque acquisition : un échec de lecture des paramètres compte comme l'échec de cette acquisition, comme le faisait l'ancienne boucle. Les tests la branchent sur une vue Fake, le vrai catalogue et le vrai service sur des Fakes.
- Le traitement est synchrone, sur le fil de la fenêtre, comme l'ancien traitement au lancement.
- Lister ne calcule ni n'écrit rien. Les messages gardent les noms de l'ancienne boucle (`scan.processing`, `scan.failed`, `sync.finished`).
- Un export sans acquisition donne l'avertissement `acquisitions.none_found` (l'ancienne boucle disait `sync.aborted` quand le dossier manquait).
- La vue est `interface/acquisitions_panel/acquisitions_panel.py`, humble : ni type ni intention (A1), ses tests sont ceux de ce presenter.
