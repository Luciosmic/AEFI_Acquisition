---
type: atome::solidai-atome
tldr: "Module `column_stabilization` : Garder en mémoire les accélérations publiées par l'acquisition du capteur inertiel (`InertialProbeSampleAcquired`)."
code: ["[[src/application/scan/scan_application_service/column_stabilization/column_stabilization.py]]"]
cause_de_changement: orchestration
---
# column_stabilization — Intention

## Rationale

Le scan attendait un délai fixe après chaque déplacement (`stabilization_delay_ms`).
Les campagnes du Banc-test-II ont montré que la colonne vibre encore après 1 s, et qu'un accéléromètre dit quand elle est revenue au repos.
L'accéléromètre de la carte LSM9DS1 est fragile (trois pannes, une soudure lâche) : un capteur muet ne doit ni bloquer le scan ni le faire attendre le délai maximal à chaque point, comme au run du Banc-test-II du 2026-11-06 (30 s par lecture après la panne).

## Responsibility

- Garder en mémoire les accélérations publiées par l'acquisition du capteur inertiel (`InertialProbeSampleAcquired`).
- Mesurer le niveau de repos de la colonne au début du scan, avant le premier déplacement.
- Après un déplacement, attendre au moins le délai fixe, puis jusqu'au repos selon `ColumnRestCriterion`, au plus son délai maximal.
- Se replier sur le délai fixe seul quand l'accéléromètre ne peut pas juger : acquisition non démarrée, capteur muet pendant la mesure du repos ou pendant la fenêtre d'un point.

## Design

- Le scan ne démarre pas l'accéléromètre : l'application l'ouvre et lance son flux à son démarrage, le panneau du capteur inertiel le montre et l'opérateur peut l'arrêter. Acquisition arrêtée = délai fixe, et le journal le dit.
- Le repli se décide point par point : un capteur qui revient en cours de scan sert de nouveau.
- Horloge et attente injectées (`clock`, `sleep`) pour tester sans attendre ; l'horloge doit être celle des `timestamp_s` des échantillons (`perf_counter` à la réception).
- Chaque attente rend un `StabilizationOutcome` (accéléromètre, délai fixe, délai maximal dépassé, scan interrompu) et se journalise avec l'identifiant du scan.
- Un délai fixe à 0 garde son sens « pas de stabilisation » : la boucle de scan n'appelle alors pas ce composant.
