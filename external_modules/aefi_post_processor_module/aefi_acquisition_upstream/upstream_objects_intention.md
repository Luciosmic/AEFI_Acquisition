---
type: atome::solidai-atome
tldr: "Emprunter à l'acquisition les pièces génériques de la fenêtre à panneaux, par un seul paquet, sans recopier ni se mêler aux dossiers de src/."
code: ["[[external_modules/aefi_post_processor_module/aefi_acquisition_upstream/upstream_objects.py]]", "[[external_modules/aefi_post_processor_module/aefi_acquisition_upstream/__init__.py]]", "[[external_modules/aefi_post_processor_module/aefi_acquisition_upstream/upstream_calibration.py]]"]
---
# upstream_objects — Intention

## Rationale

Le post-traitement est en aval de l'acquisition, dans une relation conformiste : un concept garde un seul nom et une seule implémentation. Recopier le dock, la barre de tâches et leurs modèles les ferait diverger au premier correctif. Les importer au hasard fait pire : le module a ses propres dossiers `domain`, `application`, `infrastructure` et `interface`, et lancé comme script il place son dossier en tête de `sys.path`, donc `import interface` chargerait le dossier du module au lieu de celui de `src/`, sans erreur visible.

## Responsibility

- Réexporter les objets empruntés, et seulement eux. Rien n'est emprunté avant d'être utilisé.
- Régler `sys.path` à un seul endroit : retirer le dossier du module, ajouter `src/` en dernier s'il n'y est pas.

## Design

Objets empruntés (tous sans dépendance vers un service, un port ou un adaptateur de l'acquisition) :

| Objet | Source dans `src/` | Pourquoi |
|---|---|---|
| `WindowsCarrier` | `interface/widgets/carrier/windows_carrier.py` | les panneaux déplaçables (QtAds) |
| `CarrierPresentationModel` | `interface/presentation/carrier_model.py` | son modèle de présentation |
| `ModernTaskbar` | `interface/widgets/taskbar/modern_taskbar.py` | la barre de tâches |
| `TaskbarPresenter` | `interface/presenters/taskbar_presenter.py` | son presenter |
| `TaskbarPresentationModel` | `interface/presentation/taskbar_model.py` | son modèle de présentation |

- Seuls l'infrastructure et l'interface du module importent ce paquet. Le domaine et l'application ne l'importent jamais, sinon l'acquisition importerait du code de sa propre interface à travers le post-traitement : `_tests/architecture_test.py` le vérifie, car `solidai verify` ne voit pas ce paquet, hors des quatre couches.
- `RotationConvention` entre en tranche 2, `BenchReferential` en tranche 3, `ScanVisualizationPanel` en tranche 4.
- Un test lance un processus neuf et vérifie que `interface` vient de `src/`.
- La cause de changement n'est pas déclarée : A15 range la cause `outil` sous `infrastructure/` ou `interface/`, et ce paquet est hors des quatre couches. Il change quand `src/` déplace une pièce empruntée.
