MOC : [[MOC ACQUISITION]] [[MOC INSTRUMENTATION]]
Source : 
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Tags : #Readme 
Date : 2025-06-10
Liens : [[Gestion Asynchrone-Thread de la Communication Série]]
***
## 1. Introduction

Ce document présente la méthodologie et les résultats de la caractérisation des performances de communication série pour le banc d'acquisition DDS/ADC. Cette caractérisation est une étape fondamentale dans l'optimisation globale du système, car elle permet d'identifier les limitations potentielles de la communication et d'établir des bases de référence pour les performances.

## 2. Contexte et Objectifs

### 2.1 Contexte
Le banc d'acquisition DDS/ADC utilise une communication série pour :
- Configurer les paramètres des générateurs DDS (fréquence, amplitude, phase)
- Contrôler les paramètres d'acquisition ADC
- Acquérir les données de mesure

### 2.2 Objectifs
La caractérisation vise à :
1. Mesurer la latence de communication
2. Évaluer le débit maximum
3. Analyser la stabilité temporelle
4. Identifier les goulots d'étranglement potentiels

## 3. Méthodologie

### 3.1 Protocole Expérimental

#### 3.1.1 Test de Latence
- Envoi de 100 commandes simples (`a13*`)
- Mesure du temps entre l'envoi et la réception de la réponse
- Calcul des statistiques (moyenne, min, max, écart-type)

#### 3.1.2 Test de Débit
- Envoi continu de commandes pendant 10 secondes
- Calcul du nombre de commandes par seconde
- Évaluation de la stabilité du débit

#### 3.1.3 Test de Stabilité
- Mode rapide : 1 minute de mesures
- Mode complet : 1 heure de mesures
- Échantillonnage toutes les 100ms
- Analyse de la dérive temporelle

### 3.2 Paramètres de Communication
- Baudrate : 1 500 000 bauds
- Format : 8 bits de données, 1 bit de stop, pas de parité
- Timeout : 2 secondes

### 3.3 Métriques d'Évaluation
1. **Latence**
   - Temps moyen de réponse
   - Distribution des latences
   - Jitter (écart-type)

2. **Débit**
   - Commandes par seconde
   - Efficacité de la communication

3. **Stabilité**
   - Dérive temporelle
   - Robustesse sur longue durée

## 4. Outils de Mesure

### 4.1 Script de Benchmark
Le script `benchmark_communication.py` implémente la méthodologie décrite ci-dessus avec :
- Mesures précises avec `time.perf_counter()`
- Génération automatique de graphiques
- Mode test rapide et complet

### 4.2 Visualisation
- Histogrammes de distribution de latence
- Graphiques temporels de stabilité
- Export des données brutes

## 5. Interprétation des Résultats

### 5.1 Critères de Performance
- Latence cible : < 1ms
- Débit minimum : > 1000 commandes/seconde
- Stabilité : écart-type < 10% de la moyenne

### 5.2 Analyse des Résultats
Les résultats sont analysés selon trois axes :
1. Performance absolue (valeurs mesurées)
2. Stabilité (variations temporelles)
3. Robustesse (comportement sur longue durée)

## 6. Recommandations

### 6.1 Optimisations Potentielles
- Ajustement du baudrate
- Optimisation du protocole de communication
- Gestion des buffers

### 6.2 Bonnes Pratiques
- Validation des commandes critiques
- Gestion des timeouts
- Monitoring continu des performances

## 7. Conclusion

Cette caractérisation permet d'établir une base de référence pour les performances de communication du système. Les résultats obtenus serviront de point de départ pour les optimisations futures et permettront d'identifier les limitations potentielles du système.

## 8. Perspectives

### 8.1 Améliorations Futures
- Implémentation de commandes groupées
- Optimisation du protocole
- Monitoring en temps réel

### 8.2 Intégration
- Interface avec le système de sweep
- Optimisation des acquisitions
- Calibration automatique

## 9. Résultats Préliminaires et Analyse

### 9.1 Résultats du Test Rapide

Les premiers tests réalisés en mode rapide (10 minutes de stabilité, 100 mesures de latence, 10 secondes de débit) ont permis d'obtenir les résultats suivants :

- **Latence moyenne (commande simple)** : 15,95 ms
- **Latence minimale** : 13,69 ms
- **Écart-type de la latence** : 0,30 ms
- **Débit maximum observé** : 62,64 commandes/seconde
- **Nombre de mesures de stabilité** : 536 (sur 10 minutes)
- **Latence moyenne (stabilité)** : 10,04 ms
- **Écart-type (stabilité)** : 2,71 ms

Les graphiques suivants illustrent la distribution de la latence et la stabilité temporelle :

- ![Distribution de la Latence](results/latency_hist_quick_20250610_135646.png)
- ![Stabilité de la Latence](results/stability_plot_quick_20250610_135646.png)

### 9.2 Analyse et Interprétation

#### 9.2.1 Latence
La latence correspond au temps nécessaire pour qu'une commande envoyée à la carte soit traitée et qu'une réponse soit reçue. Elle est un indicateur direct de la réactivité du système. Une latence faible et stable est essentielle pour garantir un contrôle précis et rapide des instruments.

#### 9.2.2 Débit
Le débit mesure le nombre de commandes pouvant être traitées par seconde. Il dépend directement de la latence moyenne :

$$
Débit_{max} \approx \frac{1}{Latence_{moyenne}}
$$

Dans notre cas, avec une latence moyenne de ~16 ms, le débit théorique maximal serait d'environ 62,5 commandes/seconde, ce qui est cohérent avec la valeur mesurée (62,64 commandes/s).

#### 9.2.3 Stabilité
La stabilité de la latence (jitter) est évaluée par l'écart-type des mesures sur la durée. Un système stable présente une faible dispersion des temps de réponse. Dans nos mesures, l'écart-type de la latence sur 10 minutes est de 2,71 ms, ce qui indique une variabilité non négligeable, probablement liée à la gestion des buffers, interruptions système ou limitations du port série.

#### 9.2.4 Lien entre latence, débit et stabilité
- **Latence** : détermine le temps de réponse minimal pour chaque commande.
- **Débit** : limité par la latence, il ne peut excéder $1/Latence$.
- **Stabilité** : des variations importantes de latence (jitter) peuvent entraîner des irrégularités dans le flux de commandes, affectant la synchronisation et la fiabilité des acquisitions.

Ainsi, pour maximiser le débit et garantir la fiabilité du système, il est crucial de minimiser à la fois la latence moyenne et sa variabilité.

### 9.3 Perspectives Immédiates

- **Optimisation** : Explorer les causes de la variabilité de la latence (buffers, interruptions, configuration du port série).
- **Tests complémentaires** : Réaliser des tests sur des durées plus longues et à différents baudrates.
- **Comparaison** : Évaluer l'impact de la charge système et des différents modes de communication (asynchrone, batch).

Ces résultats préliminaires constituent une base solide pour la poursuite de l'optimisation et la compréhension fine des limitations du système de communication série du banc DDS/ADC.

## Références

1. Documentation technique ADS131
2. Spécifications de communication série
3. Standards de performance pour systèmes d'acquisition
