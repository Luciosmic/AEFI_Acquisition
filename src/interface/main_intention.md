---
type: point-de-composition::solidai-hexagonal
tldr: "Construit les adaptateurs réels, services et presenters de l'application et les relie, pour le poste d'acquisition réel (main.py) ; le mode simulation vit dans main_mock.py."
code: ["[[src/interface/main.py]]"]
cause_de_changement: outil
cable:
  - "[[src/infrastructure/git_software_provenance_reader/git_software_provenance_reader_intention]]"
  - "[[src/infrastructure/persistence/operator_registry/real_operator_repository_intention]]"
  - "[[src/infrastructure/persistence/measured_object_registry/real_measured_object_repository_intention]]"
---
# main — Intention

## Rationale

Sans un module qui construit les adaptateurs et les injecte, chaque service applicatif irait chercher lui-même son dépôt, son bus ou son pilote, et la règle de dépendance (le volatil connaît le stable, jamais l'inverse) ne tiendrait plus. Le poste d'acquisition a besoin d'un seul endroit où l'on voit quel matériel et quels fichiers sont réellement branchés, et où l'on peut en changer.

## Responsibility

- Construire les adaptateurs réels (matériel, persistance, journal), le bus d'événements et les services applicatifs, puis les presenters, et les relier.
- Démarrer l'interface graphique avec ce câblage.
- Rester le seul module qui construit les adaptateurs réels : les services reçoivent leurs ports par leur constructeur.

## Design

- Source : Martin, *Clean Architecture* (2017), ch. 26 « The Main Component » : Main est le composant le plus sale, il crée et injecte tout. Seemann, *Dependency Injection in .NET* (2011), « Composition Root ».
- `cable` nomme les adaptateurs déjà typés que `main.py` construit : le journal de provenance logicielle et les dépôts d'opérateurs et d'objets mesurés. Les adaptateurs matériels et de persistance restants n'y entrent qu'à mesure que leurs intentions sont typées (type `adaptateur`, lien `implements` vers un port typé).
- Le mode simulation est câblé à part dans `main_mock.py`.
