---
statut: to_validate
---

# Récits utilisateurs — le post-traitement

Ces récits proposent des fonctionnalités ; aucun n'est engagé tant qu'il n'est pas retenu.
Chacun dit quel objet produit par AEFI_Acquisition il utilise, pour que sa faisabilité se lise d'emblée.
La colonne « Tranche » renvoie aux tranches de `conception - post-traitement en panneaux.md` ; « à classer » veut dire hors des tranches prévues.

Trois rôles :

- **l'opérateur du banc**, qui lance les acquisitions et veut savoir tout de suite si elles sont bonnes ;
- **le chercheur**, qui exploite les cartes pour la thèse et le problème direct à 4 sphères ;
- **le relecteur**, qui doit retrouver d'où vient une figure sans connaître le code.

## Synthèse

| # | Récit | Rôle | Panneau | Objet de l'acquisition utilisé | Tranche |
|---|---|---|---|---|---|
| R1 | Voir l'état de chaque acquisition sans rien recalculer | opérateur | Acquisitions | dossier d'export, `.h5` | 1 |
| R2 | Recalculer à la demande, avec un bilan | opérateur | Acquisitions, Logs | CSV, paramètres | 1 (point 2) |
| R3 | Retrouver une acquisition par objet, lift-off, type, date, opérateur | chercheur | Acquisitions | `feature_of_interest`, `provenance`, `procedure` | à classer |
| R4 | Savoir si un fichier brut a été modifié après l'acquisition | relecteur | Acquisitions | `data.files` (empreintes) | à classer |
| R5 | Lire la fiche d'une acquisition | chercheur, relecteur | Paramètres d'acquisition | `acquisition-parameters.json` entier | 2 |
| R6 | Être averti, sur la carte même, d'une rotation non calibrée | chercheur | Carte | `rotation_applied.origin`, `warnings` | 2 |
| R7 | Lire la carte en référentiel centré ou des butées | opérateur, chercheur | Carte, Settings | `positioning.state.axes_extent` | 3 |
| R8 | Voir les paramètres qui ont produit l'étape affichée | chercheur | Carte | étapes du `.h5`, `rotation_applied` | 2 |
| R9 | Comparer deux acquisitions côte à côte, même échelle de couleur | chercheur | Carte | deux acquisitions | à classer |
| R10 | Tracer des coupes à X ou Y fixe | chercheur | Profils | étapes du `.h5` | 4 |
| R11 | Superposer la même coupe de plusieurs acquisitions | chercheur | Profils | plusieurs acquisitions, `feature_of_interest` | à classer |
| R12 | Soustraire un scan de référence d'un scan de mesure | chercheur | Différence | deux acquisitions, `procedure.step_scan.grid` | à classer |
| R13 | Exploiter les balayages en fréquence | chercheur | Balayage en fréquence | `frequency_response.csv`, `procedure.frequency_sweep` | à classer |
| R14 | Exporter une figure prête pour le manuscrit, avec sa provenance | chercheur, relecteur | Carte, Profils | `provenance` | à classer |
| R15 | Comparer une carte mesurée à une carte simulée | chercheur | Comparaison | repère des sources, `rotation_applied` | à classer |
| R16 | Afficher une acquisition à la volée sur une ligne | opérateur | Profils | `procedure`, CSV d'une ligne | à classer |
| R17 | Ouvrir le journal et le dossier de l'acquisition depuis la fenêtre | opérateur | Logs, Acquisitions | dossier d'export | 1 |

## Les récits

### R1 — Voir l'état de chaque acquisition sans rien recalculer

**En tant qu'**opérateur du banc, **je veux** voir à l'ouverture chaque acquisition avec son état (traitée, à recalculer, en échec, format non pris en charge), **afin de** savoir ce qui reste à faire sans qu'un calcul parte tout seul.

- Utilise : la liste des dossiers d'export et la présence et la date du `.h5` à côté du CSV.
- Critère : ouvrir la fenêtre ne modifie aucun fichier ; une acquisition en échec garde le message de son dernier échec.

### R2 — Recalculer à la demande, avec un bilan

**En tant qu'**opérateur, **je veux** lancer le traitement d'une acquisition, ou de toutes celles à recalculer, par un bouton, **afin de** décider quand le calcul tourne et d'en voir le résultat.

- Utilise : le CSV et, dès la tranche 2, les angles de `rotation_applied`.
- Critère : le panneau Logs donne le bilan traités, à jour, en échec ; chaque échec nomme l'acquisition et l'étape fautive.

### R3 — Retrouver une acquisition

**En tant que** chercheur, **je veux** filtrer les acquisitions par objet mesuré, lift-off, type (pas à pas, à la volée, balayage en fréquence), date et opérateur, **afin de** retrouver vite la série qui m'intéresse parmi des centaines.

- Utilise : `feature_of_interest` (objet, lift-off), `procedure` (type), `provenance` (opérateur, dates).
- Critère : les filtres s'appliquent sans relire les CSV.

### R4 — Savoir si un fichier brut a été modifié

**En tant que** relecteur, **je veux** voir si le CSV d'une acquisition a changé depuis la fin de l'acquisition, **afin de** savoir si une figure repose sur les données d'origine.

- Utilise : `data.files[].sha256`, calculée par l'acquisition à la fin de l'acquisition.
- Critère : une empreinte différente marque l'acquisition « modifiée depuis l'acquisition », sans bloquer son affichage.

### R5 — Lire la fiche d'une acquisition

**En tant que** chercheur ou relecteur, **je veux** voir pour l'acquisition choisie l'opérateur, l'objet et son lift-off, le capteur et son déploiement, les angles appliqués et leur origine, l'excitation, le référentiel et les avertissements de l'export, **afin de** connaître les conditions de la mesure sans ouvrir le JSON.

- Utilise : `acquisition-parameters.json`, sections `provenance`, `feature_of_interest`, `components`, `measurement_chain`, `warnings`.
- Critère : chaque grandeur s'affiche avec l'unité que porte le fichier.

### R6 — Être averti d'une rotation non calibrée

**En tant que** chercheur, **je veux** un avertissement sur la carte même quand la rotation du capteur n'est pas calibrée, ou quand le retraitement a dû prendre les angles idéaux, **afin de** ne pas interpréter une carte dans un repère faux.

- Utilise : `rotation_applied.origin` et `warnings` de l'export ; l'origine des angles enregistrée avec l'étape.
- Critère : l'avertissement est visible sans ouvrir de panneau supplémentaire.

### R7 — Lire la carte en référentiel centré ou des butées

**En tant qu'**opérateur ou chercheur, **je veux** lire les axes et le curseur de la carte dans le référentiel centré (0,0 au milieu du banc) ou celui des butées, comme dans l'application, **afin de** retrouver une position du banc sans calcul de tête.

- Utilise : `positioning.state.axes_extent` de chaque acquisition, et `BenchReferential` emprunté à l'application.
- Critère : les fichiers et le calcul restent dans le référentiel des butées ; seul l'affichage change.

### R8 — Voir les paramètres de l'étape affichée

**En tant que** chercheur, **je veux** voir les paramètres qui ont produit l'étape affichée (angles et leur origine, point de référence, largeur du bord, méthode d'interpolation), **afin de** savoir ce qu'une carte a subi.

- Utilise : les métadonnées de chaque étape du `.h5`.
- Critère : chaque étape montre ses propres paramètres, pas seulement ceux de la dernière.

### R9 — Comparer deux acquisitions côte à côte

**En tant que** chercheur, **je veux** afficher deux acquisitions côte à côte à la même échelle de couleur, **afin de** comparer un même objet à deux lift-offs ou deux jours.

- Utilise : deux acquisitions et leur fiche.
- Critère : un écart de grille ou de référentiel entre les deux est dit, pas masqué.

### R10 — Tracer des coupes

**En tant que** chercheur, **je veux** tracer des coupes à X ou Y fixe et choisir lesquelles, **afin de** lire un profil de champ comme dans l'application.

- Utilise : les étapes du `.h5` ; `ScanVisualizationPanel` emprunté à l'application.
- Critère : même comportement que le panneau Profils de l'application.

### R11 — Superposer la même coupe de plusieurs acquisitions

**En tant que** chercheur, **je veux** superposer la même coupe tirée de plusieurs acquisitions, légendées par leur lift-off, **afin de** voir l'évolution du signal avec la distance à l'objet.

- Utilise : plusieurs acquisitions, `feature_of_interest` (lift-off).
- Critère : seules des acquisitions sur la même coupe physique se superposent ; sinon la raison est dite.

### R12 — Soustraire un scan de référence

**En tant que** chercheur, **je veux** soustraire point à point un scan de référence, sans objet, d'un scan de mesure, **afin d'**isoler la contribution de l'objet sans compter sur la correction par le bord de la carte.

- Utilise : deux acquisitions et leur grille (`procedure.step_scan.grid`, zone).
- Critère : la soustraction est refusée, avec sa raison, quand les grilles, le capteur ou l'excitation diffèrent.

### R13 — Exploiter les balayages en fréquence

**En tant que** chercheur, **je veux** ouvrir les balayages en fréquence, tracer amplitude et phase, calculer « objet − fond » et vérifier que deux fonds sont compatibles, **afin de** suivre la méthode du plan « Acquisition en fréquence » sans tableur.

- Utilise : `frequency_response.csv`, `samples.csv` et `procedure.frequency_sweep` (rôle, hauteur de table, grille).
- Critère : la règle de compatibilité est celle du plan « Acquisition en fréquence ».

### R14 — Exporter une figure avec sa provenance

**En tant que** chercheur, **je veux** exporter une carte ou un profil prêt pour le manuscrit, avec unités, référentiel et une mention de provenance (identifiant de l'acquisition, étape, version du logiciel), **afin qu'**un relecteur retrouve la donnée derrière la figure.

- Utilise : `provenance.activity.id`, `provenance.software`, l'étape affichée.
- Critère : la figure seule suffit à retrouver son acquisition.

### R15 — Comparer à une carte simulée

**En tant que** chercheur, **je veux** comparer une carte mesurée à la carte simulée du problème direct à 4 sphères, sur la même grille et dans le repère des sources, **afin de** confronter mesure et modèle.

- Utilise : l'étape changée de repère et `rotation_applied` ; une carte simulée fournie par le chercheur.
- Critère : l'écart s'affiche comme une carte, avec ses statistiques.

### R16 — Afficher une acquisition sur une ligne

**En tant qu'**opérateur, **je veux** voir une acquisition à la volée faite sur une seule ligne comme un profil le long de cette ligne, **afin de** l'exploiter alors que la mise en grille actuelle suppose une carte.

- Utilise : `procedure` (type de balayage) et le CSV d'une ligne.
- Critère : une acquisition sur une ligne n'échoue plus au traitement.

### R17 — Ouvrir le journal et le dossier depuis la fenêtre

**En tant qu'**opérateur, **je veux** ouvrir le fichier journal depuis le panneau Logs et le dossier d'une acquisition depuis le panneau Acquisitions, **afin de** lire le détail d'une erreur ou les fichiers bruts en un clic.

- Utilise : `.aefi_acquisition/logs/post_processor.log`, le dossier d'export.
- Critère : un clic, sans chemin à recopier.
