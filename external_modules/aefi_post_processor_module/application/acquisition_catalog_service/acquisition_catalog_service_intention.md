---
type: service-applicatif::solidai-hexagonal
tldr: "Lister les acquisitions d'un export avec leur état (traitée, à recalculer, en échec) sans rien calculer ni écrire."
code: ["[[external_modules/aefi_post_processor_module/application/acquisition_catalog_service/acquisition_catalog_service.py]]"]
cause_de_changement: orchestration
ports: 
  - ^: i-api-acquisition-catalog-service
    type: port::solidai-hexagonal
    tldr: "list_acquisitions et report_outcome : les acquisitions avec leur état, et l'issue d'un traitement."
    sens: entrant
    code: "[[external_modules/aefi_post_processor_module/application/acquisition_catalog_service/i_api_acquisition_catalog_service.py]]"
---
# acquisition_catalog_service — Intention

## Rationale

Le lancement de l'ancienne fenêtre calculait avant d'afficher : pour savoir quelles acquisitions étaient à jour, il fallait les traiter. Sans catalogue, la fenêtre ne peut montrer l'état de chacune à l'ouverture sans modifier de fichier, ni garder le message d'un échec pour la session.

## Responsibility

- `list_acquisitions(ListAcquisitionsDTO)` : chaque acquisition du dossier d'export avec son état `processed`, `to_recompute` (et pourquoi : `new`, `incomplete`, `forced`, `source_newer`) ou `failed` (et son message).
  Chaque état porte aussi ce qui reconnaît l'acquisition : le dossier où elle est rangée, sa date de début, l'objet mesuré et le lift-off, tels que les donne le dépôt.
  Il porte aussi la version du schéma du fichier de paramètres, la rotation que l'acquisition a appliquée (`AppliedRotationDTO` : angles en degrés, convention en trois chaînes, origine) ou la raison pour laquelle le fichier en décrit une qu'on ne peut pas utiliser. Le catalogue ne décide rien de ces angles : il les donne à qui traite ou affiche.
- `report_outcome(AcquisitionOutcomeDTO)` : retenir l'échec d'un traitement avec son message, ou l'oublier après un succès.
- Ne créer ni modifier aucun fichier.

## Design

- La règle « à recalculer » est celle de `AcquisitionRecord` ; le dépôt `IAcquisitionRepository` est un port du domaine.
- Les échecs vivent en mémoire pour la session : celui qui traite les acquisitions (le presenter du panneau Acquisitions, tranche 1.7) les rapporte, ce service n'appelle pas le service de traitement.
