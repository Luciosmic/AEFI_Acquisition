# TODO Calibration DDS – Phase & Amplitude

## Objectif
Garantir que les signaux DDS restent parfaitement en phase (et d'amplitude contrôlée) après amplification, en mesurant et corrigeant les éventuels déphasages et écarts d'amplitude sur toute la plage de fréquences utile.

---

## Tâches à réaliser

### 1. Préparation
- [x] Vérifier la connectique : signaux DDS 1 & 2 amplifiés branchés sur CH3 et CH4 de l'oscilloscope
- [x] S'assurer que le module d'acquisition oscilloscope est fonctionnel
- [x] S'assurer que le module de configuration DDS est fonctionnel
- [x] Vérifier que la classe de l'oscilloscope permet la mesure automatique du déphasage entre deux canaux (CH3/CH4)
    - [x] Si non : ajouter une méthode pour calculer le déphasage à partir des acquisitions brutes

### 2. Script de mesure automatique
- [x] Écrire un script Python pour :
    - [x] Configurer la fréquence des DDS [C: 2]
        - [x] Définir la fréquence cible (en Hz) - **Entrée utilisateur interactive**
        - [x] Utiliser la méthode du communicateur DDS pour appliquer la fréquence - **`dds.set_dds_frequency(freq)`**
        - [x] Vérifier que la fréquence est bien appliquée (lecture mémoire ou acquittement) - **Gestion d'erreur avec retour (ok, msg)**
    - [x] Déclencher l'acquisition sur l'oscilloscope (CH3/CH4) [C: 2]
        - [x] Configurer les canaux 3 et 4 (échelle verticale, offset, couplage) - **Configuration initiale + optimisation automatique avec `optimize_vdiv()`**
        - [x] Configurer le trigger (source, niveau, pente) - **Trigger sur CH3, niveau 0V, pente positive**
        - [x] Lancer l'acquisition (mode normal ou moyenné) - **Mode moyenné 64 acquisitions**
        - [x] S'assurer que l'oscilloscope est prêt à fournir les données - **Gestion d'erreur complète**
    - [x] Récupérer les signaux bruts [C: 2]
        - [x] Utiliser la méthode `get_waveform` pour CH3 et CH4 - **Prêt mais pas utilisé (on utilise les mesures automatiques)**
        - [x] Vérifier la cohérence des axes temporels (interpoler si besoin) - **Non nécessaire avec mesures automatiques**
        - [x] Stocker les signaux pour analyse ultérieure - **Non nécessaire, on sauvegarde les mesures**
    - [x] Mesurer :
        - [x] Le déphasage entre les deux signaux [C: 1]
            - [x] Utiliser la méthode `measure_phase` de la classe OscilloscopeDSOX2014AController (et non un appel direct SCPI) - **`scope.measure_phase(CH1, CH2)`**
            - [x] Vérifier la validité de la mesure (valeur numérique, pas d'erreur VISA) - **Gestion d'erreur avec try/catch**
        - [x] L'amplitude de chaque signal [C: 1]
            - [x] Lire la mesure automatique VPP (crête à crête) pour CH3 et CH4 - **`scope.get_measurements(CH1/CH2).get('VPP')`**
            - [x] Vérifier la cohérence des valeurs (pas de valeur aberrante) - **Gestion des valeurs None**
        - [x] La différence d'amplitude [C: 1]
            - [x] Calculer la différence absolue et relative entre VPP des deux canaux - **Remplacé par fonction de transfert (VPP_CH4/VPP_CH3)**
    - [x] Sauvegarder les résultats (CSV ou TXT dans `mesures/`) [C: 2]
        - [x] Créer une structure de données (dict ou DataFrame) pour stocker fréquence, phase, amplitudes, etc. - **DataFrame pandas avec toutes les colonnes**
        - [x] Ajouter une ligne à chaque mesure - **`pd.concat()` pour ajouter les nouvelles mesures**
        - [x] Sauvegarder ou mettre à jour le fichier CSV/TXT à chaque itération - **Sauvegarde automatique dans `mesures_phase_amplitude.csv`**
        - [x] Vérifier que le fichier est bien écrit et lisible - **Création automatique du dossier + gestion d'erreur**

### 3. Balayage en fréquence [C: 1]
- [x] **3.1 Définir la plage de fréquences** [C: 1]
    - [x] Choisir la fréquence de départ (ex : 100 Hz) - **DEFAULT_FREQ_MIN = 100 Hz**
    - [x] Choisir la fréquence de fin (ex : 500 kHz) - **DEFAULT_FREQ_MAX = 500000 Hz**
    - [x] Choisir le nombre de points ou le pas (ex : 50 points logarithmiques) - **DEFAULT_N_POINTS = 50**
    - [x] Créer la liste des fréquences à tester avec `np.logspace()` ou `np.linspace()` - **Fonction `create_frequency_list()`**

- [x] **3.2 Créer le script de balayage automatique** [C: 1]
    - [x] Importer le script de mesure existant (`mesure_phase_amplitude.py`) - **Intégré dans `balayage_frequence.py`**
    - [x] Créer une fonction `balayage_frequence(freq_list)` qui :
        - [x] Parcourt la liste des fréquences - **Boucle `for i, freq in enumerate(freq_list)`**
        - [x] Appelle la fonction de mesure pour chaque fréquence - **Fonction `measure_single_frequency()`**
        - [x] Affiche le progrès (ex : "Mesure 5/50 : 1.2 kHz") - **Affichage détaillé du progrès**
        - [x] Gère les erreurs sans arrêter le balayage complet - **Gestion d'erreur robuste**
    - [x] Sauvegarder tous les résultats dans le même fichier CSV - **Sauvegarde incrémentale dans `balayage_frequence.csv`**

- [x] **3.3 Ajouter des options de configuration** [C: 1]
    - [x] Permettre de choisir la plage de fréquences via arguments en ligne de commande - **Arguments `--freq-min`, `--freq-max`, `--n-points`**
    - [x] Ajouter une option pour reprendre un balayage interrompu - **Option `--resume`**
    - [x] Ajouter une option pour afficher un résumé des résultats - **Affichage du résumé final**

### 4.1 Analyse des résultats [C: 1]
- [x] **4.1.1 Créer un script de visualisation** [C: 1]
    - [x] Lire le fichier CSV des mesures avec `pandas.read_csv()` - **Fonction `load_data()`**
    - [x] Créer un graphique avec `matplotlib` montrant :
        - [x] Déphasage en fonction de la fréquence (échelle log) - **Graphique 1 avec seuils**
        - [x] Fonction de transfert en fonction de la fréquence (échelle log) - **Graphique 2 avec seuils**
        - [x] Amplitudes VPP_CH3 et VPP_CH4 en fonction de la fréquence - **Graphique 3**
    - [x] Ajouter des grilles, légendes et titres appropriés - **Configuration complète matplotlib**
    - [x] Sauvegarder le graphique en PNG/PDF - **Sauvegarde en PNG haute résolution**

- [x] **4.1.2 Identifier les problèmes** [C: 1]
    - [x] Calculer les seuils d'alerte (ex : déphasage > 5°, transfert < 0.9 ou > 1.1) - **Seuils configurables**
    - [x] Identifier les fréquences problématiques avec `np.where()` - **Fonction `identify_problems()`**
    - [x] Afficher un résumé des problèmes détectés - **Affichage détaillé des problèmes**
    - [x] Sauvegarder la liste des fréquences à corriger - **CSV `problemes_phase.csv` et `problemes_transfert.csv`**

- [x] **4.1.3 Générer un rapport d'analyse** [C: 1]
    - [x] Calculer des statistiques (moyenne, écart-type, min, max) - **Statistiques complètes**
    - [x] Créer un fichier texte avec le résumé des résultats - **Rapport `rapport_analyse.txt`**
    - [x] Inclure les graphiques générés - **Référence aux graphiques dans le rapport**
    - [x] Lister les recommandations de correction - **Section recommandations**

### 4.2 Calibration automatique [C: 1]
- [ ] **4.2.1 Créer un script de correction de phase** [C: 1]
    - [ ] Lire les déphasages mesurés depuis le CSV
    - [ ] Calculer les corrections de phase nécessaires (opposé du déphasage mesuré)
    - [ ] Créer une table de correction (fréquence → correction_phase)
    - [ ] Sauvegarder la table de correction en CSV

- [ ] **4.2.2 Créer un script de correction d'amplitude** [C: 1]
    - [ ] Lire les fonctions de transfert mesurées depuis le CSV
    - [ ] Calculer les corrections d'amplitude nécessaires (1/transfer_function)
    - [ ] Créer une table de correction (fréquence → correction_amplitude)
    - [ ] Sauvegarder la table de correction en CSV

- [ ] **4.2.3 Implémenter la correction automatique** [C: 1]
    - [ ] Créer une fonction qui applique les corrections :
        - [ ] Lire les tables de correction
        - [ ] Interpoler la correction pour une fréquence donnée
        - [ ] Appliquer la correction via les commandes DDS appropriées
    - [ ] Tester la correction sur quelques fréquences problématiques
    - [ ] Vérifier que les corrections améliorent les résultats

- [ ] **4.2.4 Validation de la calibration** [C: 1]
    - [ ] Relancer un balayage complet après correction
    - [ ] Comparer les résultats avant/après correction
    - [ ] Générer un rapport de validation
    - [ ] Sauvegarder les résultats finaux

### 5. Validation
- [ ] Vérifier, après calibration, que les signaux sont bien en phase et d'amplitude correcte sur toute la plage
- [ ] Rédiger un rapport de calibration

---

## Notes
- Penser à sauvegarder toutes les données brutes pour traçabilité
- Documenter toute modification apportée aux scripts ou à la configuration matérielle
- Ajouter des captures d'écran ou courbes dans le rapport final si besoin

## ✅ Améliorations apportées au script
- **Gestion robuste des imports** : Vérification des chemins, gestion d'erreur, fichiers `__init__.py`
- **Optimisation automatique oscilloscope** : Utilisation de `optimize_vdiv()` pour chaque canal
- **Fonction de transfert** : Calcul du rapport VPP_CH4/VPP_CH3 au lieu de la différence d'amplitude
- **Interface utilisateur** : Messages informatifs avec indicateurs visuels (✓, ✗, ⚠️)
- **Gestion d'erreur complète** : try/catch, nettoyage automatique, arrêt propre
- **Script de test** : `test_imports.py` pour valider l'environnement avant exécution

## 🔧 Améliorations récentes (2024-12-19)

### **Configuration DDS optimisée**
- **Gain DDS fixé à 1000** pour DDS1 et DDS2 (au lieu de 2000)
- **Amplification externe suffisante** : gain réduit pour éviter la saturation
- **Gestion d'erreur** : vérification que la configuration du gain s'applique correctement
- **Affichage de confirmation** : "✓ Gain DDS configuré à 1000 pour les deux canaux"

### **Optimisation temporelle pour mesure de déphasage**
- **Base de temps optimisée** : `target_timebase = period / 2` pour voir **2 périodes**
- **Calcul automatique** : `period = 1.0 / freq` puis optimisation de la base de temps
- **Commande SCPI** : `:TIMebase:SCALe` pour configurer automatiquement l'oscilloscope
- **Affichage informatif** : période et base de temps affichées en ms
- **Justification** : 2 périodes optimales pour mesure de déphasage (bonne résolution sans zoom excessif)

### **Scripts mis à jour**
- ✅ `mesure_phase_amplitude.py` : Gain 1000 + base de temps 2 périodes
- ✅ `balayage_frequence.py` : Gain 1000 + base de temps 2 périodes
- ✅ **Cohérence** : Même configuration dans les deux scripts

### **Paramètres finaux validés**
- **Gain DDS** : 1000 (DDS1 et DDS2)
- **Base de temps** : 2 périodes visibles
- **Moyennage** : 64 acquisitions
- **Déclenchement** : CH3, niveau 0V, pente positive
- **Couplage** : DC pour les deux canaux 