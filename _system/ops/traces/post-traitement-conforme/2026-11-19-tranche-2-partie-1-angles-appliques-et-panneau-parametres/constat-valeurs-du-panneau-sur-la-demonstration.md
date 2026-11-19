---
doc_type: constat-de-verification
type: constat::sh-agent-os
genere_par: "[[tache - tranche 2 partie 1 angles appliques et panneau parametres]]"
---

# Valeurs du panneau « Paramètres d'acquisition » sur l'export de démonstration

Les trois acquisitions de démonstration (`exports-demo/`, hors repo, en lecture seule) n'ont pas de fichier de paramètres. Une copie des seuls CSV (`exports-demo-parametres/`, hors repo) a reçu deux fichiers fabriqués, d'après le schéma 1.4 : angles de la bouteille d'eau du 13 novembre (34,9° ; 45,7° ; −5,3°, calibrés) pour `scan_004_rotation_z45`, convention `intrinsic` (refusée) pour `scan_002_phase_offset`, aucun fichier pour `scan_001_baseline` (comme les scans de l'étalon).

Fenêtre lancée hors écran par `build_shell` (même assemblage que `composition_root.py`), sélection de chaque ligne :

| Acquisition | Objet mesuré | Angles | Convention | Utilisés au traitement |
|---|---|---|---|---|
| `scan_001_baseline` (sans fichier) | non renseigné | non renseignés | — | angles idéaux du gabarit |
| `scan_004_rotation_z45` | bouteille_cristalline | 34,9 ° ; 45,7 ° ; −5,3 ° (calibrés, `cal-2026-11-13`) | extrinsic · ZYX · sources_to_sensor | ceux de l'acquisition |
| `scan_002_phase_offset` (convention refusée) | cylindre_metallique | rotation inutilisable : convention non prise en charge (intrinsic, ZYX, sources_to_sensor) | — | angles idéaux du gabarit (repli) |

Après « Traiter la sélection » sur `scan_004_rotation_z45` : l'étape `rotated_frame` du `.h5` porte `rotation_angles = [34.9, 45.7, -5.3]` (les angles idéaux du gabarit étaient 35,3 ; 45 ; 0), le journal dit `rotation_source=acquisition_parameters`.

Pièces : `capture-panneau-sur-la-demonstration.log` (sortie brute), `journal-de-la-capture-du-panneau.log` (lignes du journal), `fenetre-panneau-parametres.png` (capture de la fenêtre).

Constat de présentation : dans la disposition par défaut du porteur de panneaux, le panneau n'a qu'une hauteur d'environ 90 pixels : seules les premières lignes se voient, le reste défile (barre de défilement du panneau). L'opérateur peut agrandir le panneau ; la disposition par défaut appartient au porteur emprunté à l'acquisition.
