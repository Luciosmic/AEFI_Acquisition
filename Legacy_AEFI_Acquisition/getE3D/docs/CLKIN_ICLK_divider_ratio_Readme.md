MOC :
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation :
Tags : #NoteAtomique
Date : 2025-05-22
***

# Paramètres CLKIN et ICLK Divider Ratio

## Description

Les paramètres `CLKIN_divider_ratio` et `ICLK_divider_ratio` sont des diviseurs d'horloge utilisés pour configurer l'ADS131, le convertisseur analogique-numérique du banc de test. Ces paramètres influencent directement la fréquence d'échantillonnage et les performances du système.

## Valeurs possibles

Les deux paramètres acceptent uniquement les valeurs suivantes :
- `/2` (division par 2)
- `/4` (division par 4)
- `/6` (division par 6)
- `/8` (division par 8)
- `/10` (division par 10)
- `/12` (division par 12)
- `/14` (division par 14)

## Fonctionnement

### CLKIN_divider_ratio

Ce paramètre divise l'horloge d'entrée principale (CLKIN) avant son utilisation interne. Il permet d'adapter la fréquence d'horloge externe aux besoins du convertisseur.

- **Adresse** : 2
- **Valeur par défaut** : 2 (division par 2)
- **Impact** : Une valeur plus élevée réduit la fréquence d'horloge interne, ce qui peut réduire la consommation d'énergie mais aussi le taux d'échantillonnage maximum.

### ICLK_divider_ratio

Ce paramètre divise l'horloge interne (ICLK) utilisée pour le fonctionnement des circuits internes de l'ADS131.

- **Adresse** : 3
- **Valeur par défaut** : 2 (division par 2)
- **Impact** : Influence la fréquence de fonctionnement des modulateurs sigma-delta et d'autres circuits internes.

## Relation avec le taux d'échantillonnage

Le taux d'échantillonnage effectif (Fe) est lié à ces paramètres selon la relation :

```
Fe = Fréquence_base / (CLKIN_divider_ratio * ICLK_divider_ratio * Oversampling_ratio)
```

Où `Oversampling_ratio` est un autre paramètre configuré dans le système.

## Considérations pour le choix des valeurs

- **Performance** : Des valeurs plus petites permettent des taux d'échantillonnage plus élevés
- **Précision** : Des valeurs plus grandes peuvent améliorer la précision dans certaines configurations
- **Bruit** : Le choix de ces paramètres peut influencer le niveau de bruit dans les mesures
- **Aliasing** : Un échantillonnage trop lent peut provoquer de l'aliasing pour les signaux haute fréquence

## Utilisation dans le code

Dans le fichier JSON de configuration, ces paramètres sont définis comme suit :

```json
"CLKIN_divider_ratio": { "adresse": 2, "valeur": 2, "options": [2, 4, 6, 8, 10, 12, 14] },
"ICLK_divider_ratio": { "adresse": 3, "valeur": 2, "options": [2, 4, 6, 8, 10, 12, 14] }
```

Lors de l'envoi de commandes à l'appareil, la valeur numérique choisie est transmise à l'adresse correspondante.
