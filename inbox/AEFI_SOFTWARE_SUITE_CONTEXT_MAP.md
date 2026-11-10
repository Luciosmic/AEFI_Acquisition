---
source_type: manual
research_prompt: "cartographier les dépendances et contrats entre les modules logiciels AEFI pour suivre les développements parallèles"
source_reference: "session Claude Code 2026-09-19 — SCRIPT_aefi_object_pipeline.py"
generated: 2026-09-19
axes: [python-acquisition-software, numerical-simulation, forward-problem]
status: seed — à traiter avec /reduce
---

# AEFI Software Suite — Context Map

> Document de référence architecturale pour les 5 bounded contexts du système AEFI.
> Objectif : rendre explicites les contrats d'intégration et les dettes, pour que
> les développements parallèles (FEM, MCI, Post-Processing, Acquisition) ne dérivent pas
> silencieusement les uns par rapport aux autres.

---

## Vue d'ensemble — flux de données

```
AEFI_Acquisition  ──[Published Language : JSON enrichi DGP]──►  AEFI_Forward_Problem_Simulator
        │                                                          │  (MCI Adapter + FEM Adapter)
        │                                                          │  port IForwardSolver
        └──────────[Conformist]──────────────────────────►  AEFI_Post_Processor
                                                                 ▲
                              AEFI_Forward_Problem_Simulator ───┘
                                                    │
                                                    ▼  (futur)
                                          AEFI_Inverse_Problem
```

---

## Bounded Contexts

### 1. AEFI_Acquisition [UPSTREAM — Published Language]

**Rôle** : racine de toute la suite. Pilote le banc physique, orchestre le scan,
exporte les données brutes ET la configuration complète du dispositif (géométrie
reconstruite par le DGP, paramètres d'excitation, identité matérielle).

**Repo** : `Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/`

**Exports (Published Language)** :
- JSON `*_acquisition-parameters.json` — configuration complète du run :
  - `aefi_device_hardware_identity.excitation.sources_geometry` : mesures caliper brutes (phi_Si, D_ext_ij)
  - `aefi_device_hardware_identity.excitation.sources_geometry.dgp` : **positions reconstruites DGP** (positions_m, radii_m, potentials_V)
  - `excitation.mode` (X_DIR / Y_DIR / Z_DIR), fréquence, niveaux
  - `sensor` : calibration, rotation lab frame
- CSV/HDF5 `*_data` — mesures électriques brutes (champ E ou potentiels Uk)

**Le DGP est un enrichissement d'Acquisition** : la reconstruction de positions
(DGP = Device Geometry Parameters) est calculée en amont, injectée dans le JSON.
Les consumers ne recalculent pas le DGP — ils consomment directement `dgp.positions_m`.

**Invariant de convention** (2026-07-24) :
Ordre canonique des sphères : S1=x_neg_y_pos, S2=x_pos_y_neg, S3=x_pos_y_pos, S4=x_neg_y_neg.

---

### 2. AEFI_Forward_Problem_Simulator [Conformist d'Acquisition — fusion MCI + FEM]

**Rôle** : résout le problème direct AEFI — champ primaire analytique (MCI) ET champ complet
avec objet (FEM Firedrake). Les deux implémentent le même port `IForwardSolver`.
Du point de vue des consumers (Post_Processor, Inverse_Problem), il n'y a qu'un seul bounded context
qui expose une interface unifiée, quelle que soit l'implémentation sous-jacente.

**Décision architecturale (2026-09-19)** : MCI et FEM sont deux adaptateurs d'un même contexte.
Ils ne sont pas des bounded contexts séparés — ils partagent le même langage de domaine
(source_geometry, primary_field, secondary_field, object_permittivity) et répondent au
même contrat consommateur.

**Repo** :
- MCI : `Simulations Numeriques/AEFI_Forward_Problem/AEFI_Mirror_Charges_Primary_Field_Calculator/`
- FEM : `Simulations Numeriques/AEFI_Forward_Problem/AEFI_4Sphere/AEFI_4Sphere_firedrake/`
- Cible : fusionner sous `AEFI_Forward_Problem_Simulator/` (ou `AEFI_Simulator_App/` renommé)

**Port IForwardSolver** (interface unifiée) :
```
eval_primary_field(pts: ndarray(N,3)) → u: ndarray(N,)   # MCI ou FEM primaire
eval_full_field(pts, object_cfg) → u: ndarray(N,)         # FEM complet avec objet
```

**Adaptateur MCI** :
- Oracle analytique exact du champ primaire, cache par hash de configuration
- Callable `mci_eval(pts) → u`, invariant par V0 (linéarité)
- Utilisé aussi pour piloter le maillage FEM a priori (`export_mci_size_field_pos`)

**Adaptateur FEM** :
- Résout −∇·(ε∇u)=0 avec contraste d'objet enfoui
- Consomme le .pos MCI comme champ de taille a priori
- Pipeline : `AEFIObjectConfig.from_dgp_json()` → mesh → solve → u_aefi, u_primary, u_secondary

**Consomme d'Acquisition** (Conformist) :
- JSON enrichi DGP via `AEFIObjectConfig.from_dgp_json(json_path)` → `dgp.positions_m`, `dgp.radii_m`, `dgp.potentials_V`

**Exporte vers Post_Processor** :
- Interface `IForwardSolver` — format de sortie unifié indépendant de l'adaptateur
- Résolution D2 : le contrat est défini au niveau du port, pas de l'implémentation

**Pattern** : Conformist d'Acquisition. MCI et FEM sont deux adaptateurs du même port.

---

### 3. AEFI_Post_Processor [Conformist d'Acquisition + Agrégateur]

**Rôle** : agrège toutes les sources de données (mesures, MCI, FEM) pour visualisation et analyse.
Point d'entrée unique pour la comparaison modèle/mesure.

**Repo** : à définir (notebooks actuels dans `AEFI_4Sphere_notebook_repository/`)

**Consomme** :
- AEFI_Acquisition : données brutes CSV/HDF5 + JSON configuration (Conformist)
- AEFI_Forward_Problem_Simulator : champ primaire + champ complet via `IForwardSolver`

**Exporte vers** :
- Visualisations comparatives (champ mesuré vs MCI vs FEM)
- À terme : données pré-traitées pour AEFI_Inverse_Problem

**Pattern** : Conformist d'Acquisition pour le modèle de données ; agrégateur open-host
pour les autres consumers.

---

### 4. AEFI_Inverse_Problem [Consumer futur de Post_Processor]

**Rôle** : reconstruire la position, forme, permittivité d'un objet enfoui à partir
du champ secondaire mesuré.

**Repo** : `Simulations Numeriques/AEFI_Inverse_Problem/` (en initialisation)

**Consomme** :
- AEFI_Post_Processor : champ secondaire pré-traité (mesuré − primaire calculé)

**Pattern** : Customer-Supplier de Post_Processor — l'Inverse Problem *commande* le
format de sortie dont il a besoin (cartes de champ normalisées, grilles régulières, etc.)

---

## Contrats d'intégration critiques

| Contrat | Producteur | Consommateur | Format | Stabilité |
|---|---|---|---|---|
| JSON acquisition enrichi DGP | AEFI_Acquisition | Forward_Problem_Simulator, Post_Processor | JSON (schema v0.1-agile) | **Instable** — schema_version 0.1 |
| `IForwardSolver.eval_*` | Forward_Problem_Simulator | Post_Processor | Interface Python (à formaliser) | **À définir — résout D2** |
| MCI → FEM size field (.pos) | MCI adapter | FEM adapter | gmsh ASCII ScalarPoint | Stable (interne au contexte) |
| Champ secondaire pré-traité | Post_Processor | Inverse_Problem | À définir | Non défini |

---

## Dettes d'intégration connues

### [D1] `potentials_V` → `potential_sign` (DETTE ACTIVE)

**Localisation** : JSON `dgp.potentials_V` dans AEFI_Acquisition
**Problème** : le champ contient des flottants `+1.0/-1.0` qui représentent un signe,
pas une tension en volts. Le nom est trompeur.
**Impact** : AEFI_MCI_Calculator et AEFI_FEM_Simulator doivent lire `potentials_V`
et le traiter comme un signe (cast en int).
**Résolution** : renommer en `potential_sign: int` côté Acquisition, puis mettre à jour
tous les consommateurs (tag de recherche : `[potentials_V → potential_sign]`).
**Fichiers touchés** :
- `SCRIPT_aefi_object_pipeline.py` → `load_sphere_sources_from_dgp_json()`
- Module MCI → consommateur du JSON

### [D2] Contrat IForwardSolver non encore formalisé

**Problème** : MCI et FEM sont reconnus comme adaptateurs du même port, mais le port
`IForwardSolver` n'existe pas encore en code — il est implicite.
**Impact** : Post_Processor ne peut pas consommer Forward_Problem_Simulator de manière
uniforme ; chaque adaptation est ad hoc.
**Résolution** : définir `IForwardSolver` comme interface Python abstraite dans le domaine
de `AEFI_Forward_Problem_Simulator`, avec `MCIAdapter` et `FEMAdapter` comme implémentations.
Le format de sortie (numpy ndarray sur grille ?) se définit en même temps.

### [D3] `schema_version: "0.1-agile"` dans le JSON Acquisition

**Problème** : le JSON est déclaré "agile" — il peut changer sans versioning formel.
Les consumers Conformists (FEM, Post_Processor) n'ont pas de protection contre les
changements silencieux.
**Impact** : un changement de structure JSON Acquisition casse les consumers sans avertissement.
**Résolution** : passer à un schema versionné (v1.0) avant la campagne de mesure suivante,
avec validation par jsonschema côté consumer.

---

## Évolution architecturale visée

```
Étape courante (2026-09-19) :
  Acquisition → [JSON DGP] → MCI (champ primaire OK)
  Acquisition → [JSON DGP] → FEM (geometry chargée, pipeline en cours)

Étape suivante :
  MCI → [mci_eval + pos cache] → FEM (maillage a priori MCI)
  FEM → [u_secondary] → Post_Processor (format à définir)

Cible :
  Post_Processor agrège Acquisition + MCI + FEM
  Post_Processor → Inverse_Problem
```

---

## Claims extractibles pour /reduce

- La transformation linéaire du problème AEFI (u → V0·u) rend le maillage optimal invariant par V0 — le .pos MCI calculé sur le problème normalisé est valide pour toute amplitude d'excitation
- MCI et FEM sont deux adaptateurs du même port IForwardSolver dans le bounded context AEFI_Forward_Problem_Simulator — les fusionner élimine la duplication de contrat vers Post_Processor
- Le pattern Conformist FEM/Acquisition implique que tout changement du JSON Acquisition doit être répercuté immédiatement sur SCRIPT_aefi_object_pipeline.py
- Le DGP est un enrichissement d'Acquisition, pas un module séparé — les consumers ne recalculent jamais les positions DGP
- L'absence d'interface IForwardSolver formalisée est la dette structurelle principale qui bloque l'intégration Post_Processor
