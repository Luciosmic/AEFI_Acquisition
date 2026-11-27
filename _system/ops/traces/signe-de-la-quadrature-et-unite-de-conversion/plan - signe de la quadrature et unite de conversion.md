# Plan : signe de la quadrature et unité de conversion

**Prochaine action :** l'humain essaie les tranches 1 et 1 bis dans l'application (panneau « Configuration du banc » > Électronique) et y déclare −1 pour la carte de conditionnement montée ; puis tranche 2, appliquer le signe à la lecture de l'ADC.

**Fait (2026-11-27, tranche 1 bis) :** deux panneaux. « Configuration du banc » (`bench_configuration`) tient le catalogue et le montage, groupés en Capteur, Électronique (dont l'unité de conversion) et Mouvement ; « Calibration » tient la calibration du capteur, la géométrie des sources, la transmission et les deux mesures de l'unité de conversion (débit d'acquisition du microcontrôleur, cadence de sortie de l'ADC), qui pré-remplissent les formulaires du catalogue. Tests de l'interface verts (210), tableau de bord construit.

**Fait (2026-11-27) :** tranche 1 codée, tests localisés verts (260). Le DDS, l'ADC et le microcontrôleur forment l'assemblage `digital_analog_signals_processing_unit` du domaine, montré sous un onglet « Unité de conversion entre signaux numériques et analogiques » dans « Électronique ». La carte de conditionnement porte la grandeur `quadrature_output_sign` (−1 ou +1, sinon non renseignée), exportée sans dimension. `solidai verify` ne se construit pas sur le PC du labo (paquet `solid-verify-core` absent) : non joué.

## Pourquoi

Le 2026-11-27, l'humain constate que toutes les données acquises jusqu'ici ont la voie en quadrature inversée : l'ADC lit −Q au lieu de Q.
La liaison entre la carte de conditionnement et l'unité de conversion passe par des connecteurs droits ; c'est la carte de conditionnement qui sort ses voies en quadrature broches P et N échangées, pour éviter un croisement de pistes.
Le signe est donc une propriété de la carte de conditionnement.
La thèse garde la convention $e^{+j\omega t}$ partout et corrige le signe de la quadrature mesurée à l'entrée des données (GRAPHE-THESE, décision du 2026-11-26).

L'humain demande aussi de regrouper dans l'application, avec le langage du graphe, ce qui forme l'unité de conversion entre signaux numériques et analogiques (clé `digital-analog-signals-processing-unit`) : l'ADC, le DDS et le microcontrôleur.

## Décisions validées (2026-11-27)

- Le signe de la voie en quadrature se déclare sur la carte de conditionnement, dans son onglet du catalogue : −1 pour la carte montée aujourd'hui, « non renseigné » pour la V4 tant qu'elle n'est pas vérifiée.
- La correction s'applique une seule fois, à la lecture de l'ADC ; affichage, corrections de phase et export suivent alors la convention de la thèse.
- Chaque export enregistre le signe appliqué ; un fichier sans ce champ est ancien, à quadrature inversée.
- Sans signe renseigné pour la carte montée, l'application l'affiche en avertissement et ne corrige rien en silence.

## Tranches

1. Regroupement « Unité de conversion » et déclaration du signe dans le catalogue.
1 bis. Séparer la configuration et la calibration en deux panneaux (demande de l'humain du 2026-11-27 : « ne plus mélanger les contextes »). « Configuration du banc » tient le catalogue des composants et leur montage (contexte `test_bench_configuration`) ; « Calibration » tient la calibration du capteur, la géométrie des sources, la transmission et les mesures de caractérisation de l'unité de conversion (contexte `test_bench_calibration`).
2. Application du signe à la lecture de l'ADC, avertissement si non renseigné, signe dans l'export.
3. Post-traitement : corriger les fichiers anciens (worktree `dev_post_processor`).
