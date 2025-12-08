MOC :
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation :
Tags : #NoteAtomique
Date : 2025-05-22
***

# Paramètre Oversampling Ratio

## Description

Le paramètre `Oversampling_ratio` est un facteur de suréchantillonnage utilisé dans le convertisseur analogique-numérique ADS131. Ce paramètre est essentiel car il définit le rapport entre la fréquence d'échantillonnage interne du modulateur sigma-delta et la fréquence de sortie des données.

## Valeurs possibles

Les valeurs disponibles pour l'Oversampling ratio sont :
- 4096
- 2048
- 1024
- 800
- 768
- 512
- 400
- 384
- 256
- 200
- 192
- 128
- 96
- 64
- 48
- 32

## Fonctionnement

### Principe du suréchantillonnage

Le suréchantillonnage est une technique qui consiste à échantillonner un signal à une fréquence beaucoup plus élevée que le strict minimum requis par le théorème de Nyquist (deux fois la fréquence maximale du signal), puis à moyenner ou filtrer ces échantillons pour obtenir une résolution effective plus élevée.

### Dans l'ADS131

- **Adresse** : 4
- **Valeur par défaut** : Souvent 256 ou 512
- **Impact** : Plus le ratio est élevé, meilleure est la résolution mais plus faible est la fréquence d'échantillonnage effective.

## Relation avec la fréquence d'échantillonnage

La fréquence d'échantillonnage effective (Fe) est calculée selon la formule :

```
Fe = Fréquence_base / (CLKIN_divider_ratio * ICLK_divider_ratio * Oversampling_ratio)
```

Où `Fréquence_base` est la fréquence de l'oscillateur principal du système.

## Avantages et inconvénients des différentes valeurs

### Valeurs élevées (1024-4096)
- ✅ **Avantages** : 
  - Meilleure résolution effective
  - Meilleur rapport signal/bruit (SNR)
  - Réduction du bruit de quantification
- ❌ **Inconvénients** :
  - Fréquence d'échantillonnage plus basse
  - Temps de réponse plus long
  - Consommation d'énergie potentiellement plus élevée

### Valeurs moyennes (128-768)
- ✅ **Avantages** : 
  - Bon compromis entre résolution et vitesse
  - Adapté à la plupart des applications

### Valeurs basses (32-96)
- ✅ **Avantages** : 
  - Fréquence d'échantillonnage plus élevée
  - Meilleure réponse aux signaux transitoires
- ❌ **Inconvénients** :
  - Résolution effective réduite
  - SNR plus faible

## Relation avec la résolution

Pour un convertisseur sigma-delta, chaque quadruplement de l'Oversampling ratio augmente théoriquement la résolution effective d'environ 1 bit. Par exemple :
- OSR = 32 → Résolution de base
- OSR = 128 (4x) → +1 bit de résolution
- OSR = 512 (4x) → +1 bit supplémentaire
- OSR = 2048 (4x) → +1 bit supplémentaire

## Considérations pour le choix de la valeur

- **Type de signal** : Pour des signaux lents ou DC, privilégiez des valeurs élevées. Pour des signaux rapides, des valeurs plus basses.
- **Bruit ambiant** : Dans un environnement bruité, un ratio plus élevé aide à réduire l'impact du bruit.
- **Bande passante** : La bande passante utile est directement affectée par ce paramètre.
- **Résolution nécessaire** : Choisissez en fonction de la précision requise pour votre application.

## Utilisation dans le code

Dans le fichier JSON de configuration, ce paramètre est défini comme suit :

```json
"Oversampling_ratio": { 
  "adresse": 4, 
  "valeur": 32, 
  "options": [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32] 
}
```

Pour calculer la fréquence d'échantillonnage effective, vous pouvez utiliser une fonction comme :

```python
def calculer_fe(freq_base, clkin_div, iclk_div, oversampling):
    return freq_base / (clkin_div * iclk_div * oversampling)
``` 