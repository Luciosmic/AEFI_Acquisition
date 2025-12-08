# Interface d'Acquisition AD9106/ADS131A04 - Phase 1 (Bloc de Base)

## 🎯 Objectif Phase 1
Créer un **bloc fonctionnel de base** qui gère :
- **2 modes d'acquisition** : Temps Réel (exploration) vs Export (mesures)
- **Interface simplifiée** : Configuration 3 paramètres dans onglet principal
- **Affichage numérique temps réel** : 8 canaux ADC avec facteur V to V/m
- **Export automatique** en CSV pour le mode mesures
- **Conversion ADC → Tensions** avec facteur 4.76837E-7 V/LSB
- **Onglet Réglages Avancés** : Interface complète DDS/ADC (existante)

---

## 📋 Tâches Prioritaires - Phase 1

### 1. 🏗️ Interface Principale PyQt5

#### 1.1 Onglet Principal **[Complexité: 4/10]**
- [x] **Interface "Visualisation & Export"** avec 3 zones : **[3/10]** ✅ **Validé** : Interface complète avec configuration, affichage numérique, contrôles et graphique pyqtgraph
  - [x] Configuration 3 paramètres (Gain DDS, Fréq Hz, N_avg) **[2/10]** ✅ **Validé** : Widget ConfigurationWidget fonctionnel avec synchronisation
  - [x] **Affichage numérique temps réel 8 canaux** **[4/10]** ✅ **Validé** : Affichage 8 canaux avec unités et facteur V to V/m
    - [x] Créer grille QGridLayout 2x4 **[1/10]**
    - [x] 8 QLabel pour valeurs numériques **[1/10]**
    - [x] Codes couleur ADC1 (bleus) + ADC2 (verts) **[2/10]**
    - [x] Timer QTimer pour mise à jour périodique **[2/10]** ✅ **Validé** : Timer QTimer connecté à update_display() pour rafraîchissement périodique de l'affichage 8 canaux
    - [x] Gestion des unités (ComboBox) **[2/10]**
  - [x] **Contrôles d'acquisition selon le mode** **[3/10]** ✅ **Validé** : Boutons synchronisés avec les modes, interface fluide
    - [x] QPushButton "Démarrer/Arrêter" avec états **[2/10]**
    - [x] QLabel status acquisition **[1/10]**
    - [x] Logic switch boutons selon mode **[2/10]**
- [x] **Indicateur Mode Actif** : **[2/10]** ✅ **Validé** : Transitions de mode fonctionnelles
  - [x] 🟢 Mode Temps Réel : "Exploration - Modifications immédiates" **[2/10]**
  - [x] 🔴 Mode Export : "Mesures - Interface verrouillée" **[2/10]**

#### 1.2 Configuration 3 Paramètres **[Complexité: 3/10]**
- [x] **Interface inspirée LabVIEW** : **[2/10]** ✅ **Validé** : Interface ConfigurationWidget avec style moderne et thème sombre
  ```
  ┌─── Configuration Acquisition ───┐
  │ Gain DDS:  [5000] (DDS1 & DDS2) │
  │ Fréq (Hz): [500 ]               │  
  │ N_avg:     [10  ]               │
  └─────────────────────────────────┘
  ```
- [x] **Comportement selon mode** **[4/10]** ✅ **Validé** : Synchronisation des modes exploration/export fonctionnelle
  - [x] **Mode Temps Réel modifiable** **[3/10]** ✅ **Validé** : Widgets activés en mode exploration
    - [x] QSpinBox avec validateurs **[1/10]**
    - [x] Signal valueChanged connecté **[2/10]**
    - [x] Validation ranges (Gain: 0-16376, Freq: 0.1-1MHz) **[2/10]**
  - [ ] **Mode Export lecture seule** **[5/10]** → **Non testé** : Fonctionnalité export non encore implémentée
    - [ ] setEnabled(False) sur widgets **[1/10]**
    - [ ] Style grisé CSS **[2/10]**
    - [ ] Sauvegarde valeurs avant verrouillage **[2/10]**
    - [ ] Restauration lors déverrouillage **[3/10]** → **DÉCOMPOSÉ :**
      - [ ] Récupération valeurs sauvegardées **[1/10]**
      - [ ] setEnabled(True) sur widgets **[1/10]**
      - [ ] Validation cohérence post-restauration **[2/10]**

#### 1.3 Onglet Réglages Avancés **[Complexité: 2/10]**
- [x] **Onglet "⚙️ Réglages Avancés DDS/ADC"** basé sur AD9106_ADS131A04_GUI.py : **[2/10]** ✅ **Validé** : Intégration complète des composants DDSControl et ADCControl
  - [x] **Contrôle DDS détaillé** : 4 DDS individuels Gain & Phase **[1/10]** ✅ **Validé** : Composant DDSControlAdvanced créé avec contrôles individuels
  - [x] **Configuration ADC complète** : Timing, Gains, Références **[1/10]** ✅ **Validé** : Composant ADCControlAdvanced créé avec tous les paramètres
  - [x] **Barre de contrôle** : Port, Connexion, Fréquence globale **[2/10]** ✅ **Validé** : Barre de contrôle partagée avec fréquence globale
  - [x] **Interface moderne** **[3/10]** → **DÉCOMPOSÉ :**
    - [x] Import des classes DDSControl/ADCControl **[1/10]** ✅ **Validé** : Import des composants avancés
    - [x] Application thème CSS identique **[2/10]** ✅ **Validé** : Thème sombre cohérent avec l'interface principale
    - [x] Layout et disposition uniforme **[2/10]** ✅ **Validé** : Layout 2x2 pour DDS, zone ADC séparée
- [x] **Intégration avec modes** **[3/10]** → **DÉCOMPOSÉ :**
  - [x] Mode Temps Réel : Onglet accessible et modifiable **[2/10]** ✅ **Validé** : Contrôles activés en mode exploration
  - [x] **Mode Export lecture seule** **[4/10]** → **DÉCOMPOSÉ :**
    - [x] Désactivation tous les contrôles **[2/10]** ✅ **Validé** : Méthode set_enabled() implémentée
    - [x] Indicateur visuel "Mode Export" **[1/10]** ✅ **Validé** : Gestion automatique selon le mode
    - [x] Prévention modifications accidentelles **[2/10]** ✅ **Validé** : Verrouillage complet en mode export
- [x] **Synchronisation** **[6/10]** ✅ **Validé** : Synchronisation bidirectionnelle complète via AcquisitionManager
  - [x] **Configuration 3 paramètres ↔ Réglages avancés** **[6/10]** ✅ **Validé** : Architecture centralisée via AcquisitionManager
    - [x] Système d'événements QSignal centralisé **[3/10]** ✅ **Validé** : Signal unique `configuration_changed` émis par AcquisitionManager
      - [x] Signal `configuration_changed` dans AcquisitionManager **[1/10]** ✅ **Validé**
      - [x] Connexion signals/slots vers tous les widgets **[2/10]** ✅ **Validé** : Méthode `_on_acquisition_config_changed()` connectée
      - [x] Test communication bidirectionnelle **[1/10]** ✅ **Validé** : Synchronisation automatique entre onglets
    - [x] Détection changements et propagation **[3/10]** ✅ **Validé** : Tous les widgets émettent vers AcquisitionManager
      - [x] Listeners sur widgets source **[1/10]** ✅ **Validé** : Signaux connectés depuis tous les widgets
      - [x] Logic propagation conditionnelle **[2/10]** ✅ **Validé** : AcquisitionManager centralise et redistribue
      - [x] Prévention boucles infinies **[2/10]** ✅ **Validé** : Utilisation de `blockSignals()` dans `set_configuration()`
  - [x] **Gain DDS bidirectionnel** **[5/10]** ✅ **Validé** : Synchronisation DDS1/DDS2 via AcquisitionManager
    - [x] Principal → Avancé : copie vers DDS1 & DDS2 **[2/10]** ✅ **Validé** : Méthode `set_dds_gain()` dans AdvancedSettingsWidget
    - [x] Avancé → Principal : transmission via AcquisitionManager **[3/10]** ✅ **Validé** : Méthodes `_on_dds_gain_changed()` et `_on_dds_phase_changed()`
      - [x] Émission signal vers AcquisitionManager **[1/10]** ✅ **Validé**
      - [x] Update widget gain principal **[1/10]** ✅ **Validé** : Via signal `configuration_changed`
      - [x] Validation range résultat **[1/10]** ✅ **Validé** : Validation dans AcquisitionManager
  - [x] **Fréquence synchronisée** **[7/10]** ✅ **Validé** : Fréquence globale synchronisée entre onglets
    - [x] Widget fréquence partagé **[3/10]** ✅ **Validé** : Fréquence synchronisée via AcquisitionManager
      - [x] Référence unique widget fréquence **[1/10]** ✅ **Validé** : AcquisitionManager comme source unique
      - [x] Mise à jour simultanée **[1/10]** ✅ **Validé** : Signal `configuration_changed` vers tous les widgets
      - [x] Gestion focus et édition **[2/10]** ✅ **Validé** : `blockSignals()` préserve le focus utilisateur
    - [x] Signal global frequencyChanged **[2/10]** ✅ **Validé** : Signal `configuration_changed` centralisé
    - [x] Validation ranges cohérente **[2/10]** ✅ **Validé** : Validation dans AcquisitionManager
    - [x] Mise à jour immédiate DDS hardware **[4/10]** ✅ **Validé** : Application hardware centralisée dans AcquisitionManager

### 2. 📊 Affichage Numérique Temps Réel

#### 2.1 Interface 8 Canaux **[Complexité: 5/10]**
- [x] **Grille 2x4 avec codes couleur** **[4/10]** → **DÉCOMPOSÉ :**
  - [x] Création QGridLayout 2x4 **[1/10]**
  - [x] 8 QLabel avec fonts monospace **[1/10]**
  - [x] Codes couleur : ADC1 (4 bleus), ADC2 (4 verts) **[2/10]**
  - [ ] Formatage numérique avec précision **[2/10]**
  - [ ] Gestion états (Normal/Erreur/NonUtilisé) **[2/10]**
- [x] **ComboBox Unités** **[3/10]** → **DÉCOMPOSÉ :**
  - [x] QComboBox [Codes ADC | V | mV | µV | V/m] **[1/10]**
  - [x] Conversion automatique lors changement **[2/10]**
  - [ ] Persistance choix utilisateur **[2/10]**
- [x] **Facteur V to V/m** : Champ numérique (ex: 63600) pour calibration champ électrique **[2/10]**

#### 2.2 Indicateurs Visuels **[Complexité: 4/10]**
- [ ] **Codes couleur** **[3/10]** → **DÉCOMPOSÉ :**
  - [ ] Palette couleurs ADC1 (4 bleus) **[1/10]**
  - [ ] Palette couleurs ADC2 (4 verts) **[1/10]**
  - [ ] Application CSS dynamique **[2/10]**
- [ ] **États visuels** **[4/10]** → **DÉCOMPOSÉ :**
  - [ ] État Normal : couleur standard **[1/10]**
  - [ ] État Erreur : fond rouge + texte **[2/10]**
  - [ ] État NonUtilisé : gris + italique **[1/10]**
  - [ ] Transitions fluides entre états **[2/10]**
- [ ] **Statistiques** **[3/10]** → **DÉCOMPOSÉ :**
  - [ ] QLabel fréquence acquisition (Hz) **[1/10]**
  - [ ] QLabel timestamp dernière mise à jour **[1/10]**
  - [ ] Timer de calcul fréquence réelle **[2/10]**

#### 2.3 Visualisation Graphique Temps Réel (pyqtgraph) **[Complexité: 6/10]**
- [x] **Ajout d'un graphique temps réel pyqtgraph** **[6/10]**
    - [x] Ajouter pyqtgraph au requirements si besoin (pip install pyqtgraph) [1/10]  
      → pyqtgraph importé en tête du script, prêt à l'emploi.
    - [x] Instancier PlotWidget dans le layout principal [1/10]  
      → Widget graphique ajouté à droite dans l'onglet principal (`RealtimeGraphWidget`).
    - [x] Adapter au redimensionnement [1/10]  
      → Layout QHBoxLayout, le widget s'adapte à la fenêtre.
    - [x] Créer 8 courbes, couleurs identiques à l'affichage numérique [2/10]  
      → 8 courbes créées, couleurs cohérentes (bleu/vert), légende automatique.
    - [x] Initialiser avec données vides ou simulées [1/10]  
      → Courbes initialisées vides, prêtes à recevoir les données live.
    - [x] Utiliser get_latest_data() AcquisitionManager [2/10]  
      → Données extraites via AcquisitionManager (`_data_buffer.get_latest_samples`), jamais accès direct SerialCommunicator.
    - [x] Vérifier structure des données (shape, timestamp, valeurs) [2/10]  
      → Extraction timestamp + valeurs par canal, conversion pour pyqtgraph.
    - [x] Connecter update graphique au timer [1/10]  
      → Appel `update_graph()` à chaque tick du QTimer principal (synchro avec update_display).
    - [x] Optimiser pour éviter ralentissements [2/10]  
      → Fenêtre glissante (2s), nombre de points limité, update partiel.
    - [x] Ajouter QCheckBox/menu pour chaque courbe [2/10]  
      → CheckBox par canal, masquage dynamique des courbes.
    - [x] Masquer/afficher dynamiquement [2/10]  
      → Visibilité des courbes liée à l'état des CheckBox.
    - [x] Limiter affichage à une fenêtre temporelle glissante [2/10]  
      → Affichage des N derniers points (2s), time axis relative.
    - [x] Utiliser fonctions pyqtgraph pour zoom/défilement [2/10]  
      → Zoom/défilement natif pyqtgraph, axes synchronisés.
    - [x] Recentrage auto si acquisition en cours [1/10]  
      → Fenêtre glissante recentrée automatiquement à chaque update.
    - [x] Ajouter option largeur moyenne mobile [2/10]  
      → QSpinBox pour largeur lissage, valeur modifiable à la volée.
    - [x] Appliquer lissage avant affichage [2/10]  
      → Moyenne mobile appliquée sur chaque courbe si demandé.
    - [x] Permettre désactivation (valeur 1) [1/10]  
      → Lissage désactivé si largeur=1.
    - [x] Ajouter QLabel/zone colorée état courant [1/10]  
      → Indicateur d'état acquisition (texte/couleur) sous les contrôles.
    - [x] Synchroniser avec AcquisitionManager [2/10]  
      → Etat affiché selon status AcquisitionManager (RUNNING/PAUSED/ERROR).
    - [x] Appliquer thème sombre pyqtgraph [1/10]  
      → Couleurs de fond/axes cohérentes avec le reste de l'UI.
    - [x] Ajuster taille, polices, marges [1/10]  
      → Layout compact, polices lisibles, intégration harmonieuse.
    - [x] Ajouter commentaire/code/doc sur accès unique via AcquisitionManager [1/10]  
      → Commentaire explicite dans la classe RealtimeGraphWidget sur le pattern d'accès buffer.
    - [x] Adaptation de l'échelle du graphique selon l'unité sélectionnée (Codes ADC, V, mV, µV, V/m) [2/10]  
      → Le graphique pyqtgraph utilise les mêmes paramètres d'unité et de facteur V to V/m que l'affichage numérique (signal/slot). Conversion et label d'axe Y synchronisés en temps réel.

### 3. 🔧 Backend - Gestion des 2 Modes

#### 3.1 Mode Temps Réel (Exploration) **[Complexité: 7/10]**
- [x] **AcquisitionManager réactif** **[8/10]** → **DÉCOMPOSÉ :**
  - [x] **Acquisition continue arrière-plan** **[7/10]** → **DÉCOMPOSÉ :**
    - [x] QThread pour acquisition séparée **[3/10]** → **DÉCOMPOSÉ :**
      - [x] Héritage QThread personnalisé **[1/10]**
      - [x] Méthode run() avec loop acquisition **[2/10]**
      - [x] Signaux started/finished **[1/10]**
    - [x] Loop infinie avec acquisition DDS/ADC **[3/10]** → **DÉCOMPOSÉ :**
      - [x] While loop avec flag running **[1/10]**
      - [x] Appels SerialCommunicator périodiques **[2/10]**
      - [x] Gestion timeout et erreurs **[2/10]**
    - [x] Communication thread principal via QSignal **[3/10]** → **DÉCOMPOSÉ :**
      - [x] Signal dataReady avec payload données **[1/10]**
      - [x] Connexion thread-safe Qt **[2/10]**
      - [x] Emit depuis thread acquisition **[1/10]**
  - [x] **Pause automatique (~100ms)** **[9/10]** → **DÉCOMPOSÉ :**
    - [x] Détection changement des 3 paramètres **[2/10]**
    - [x] Signal pause émis vers AcquisitionManager **[2/10]**
    - [x] Attente thread acquisition (flag pause) **[3/10]** → **DÉCOMPOSÉ :**
      - [x] Flag boolean isPaused thread-safe **[1/10]**
      - [x] Loop attente dans thread acquisition **[2/10]**
      - [x] Confirmation pause reçue **[1/10]**
    - [x] Timer 100ms de délai **[1/10]**
    - [x] Validation aucun autre changement pendant pause **[4/10]**
  - [x] **Application immédiate changements** **[6/10]** → **DÉCOMPOSÉ :**
    - [x] Envoi commandes hardware (SerialCommunicator) **[2/10]**
    - [x] Vérification confirmation hardware **[3/10]** → **DÉCOMPOSÉ :**
      - [x] Lecture status registres hardware **[2/10]**
      - [x] Validation configuration appliquée **[1/10]**
      - [x] Timeout si pas de réponse **[2/10]**
    - [x] Rollback si échec **[3/10]** → **DÉCOMPOSÉ :**
      - [x] Restauration configuration précédente **[2/10]**
      - [x] Notification utilisateur échec **[1/10]**
      - [x] Log erreur pour debugging **[1/10]**
  - [x] **Reprise automatique** **[8/10]** → **DÉCOMPOSÉ :**
    - [x] Signal reprise après délai 100ms **[2/10]**
    - [x] Réactivation thread acquisition **[3/10]** → **DÉCOMPOSÉ :**
      - [x] Reset flag isPaused = False **[1/10]**
      - [x] Signal resume vers thread **[1/10]**
      - [x] Vérification thread actif **[2/10]**
    - [x] Test première acquisition post-reprise **[3/10]** → **DÉCOMPOSÉ :**
      - [x] Acquisition test immédiate **[2/10]**
      - [x] Validation données cohérentes **[1/10]**
      - [x] Fallback si échec test **[2/10]**
- [x] **Buffer court** **[4/10]** → **DÉCOMPOSÉ :**
  - [x] Structure CircularBuffer (100 échantillons max) **[2/10]**
  - [x] Overwrite automatique des anciens **[1/10]**
  - [x] Thread-safe access **[2/10]**

#### 3.2 Mode Export (Mesures Scientifiques) **[Complexité: 6/10]**
- [x] **AcquisitionManager continu** **[6/10]** → **DÉCOMPOSÉ :**
  - [x] **Configuration figée** **[5/10]** → **DÉCOMPOSÉ :**
    - [x] Snapshot configuration au début acquisition **[2/10]**
    - [x] Verrouillage widgets 3 paramètres **[2/10]**
    - [x] Validation cohérence avant export **[2/10]**
    - [x] Hash configuration pour traçabilité **[1/10]**
  - [x] **Durée définie/continu** **[4/10]** → **DÉCOMPOSÉ :**
    - [x] QSpinBox durée en secondes **[1/10]**
    - [x] QCheckBox mode continu **[1/10]**
    - [x] Timer progression/timeout **[2/10]**
    - [x] Arrêt conditionnel selon mode **[2/10]**
  - [x] **Prévention interruptions** **[7/10]** → **DÉCOMPOSÉ :**
    - [x] Désactivation complete interface principale **[2/10]**
    - [x] Intercept signaux paramètres **[3/10]**
    - [x] Message warning si tentative modification **[1/10]**
    - [x] Protection thread acquisition **[3/10]**
- [x] **Buffer production** **[5/10]** → **DÉCOMPOSÉ :**
  - [x] CircularBuffer 1000+ échantillons **[2/10]**
  - [x] Gestion mémoire dynamique **[2/10]**
  - [x] Flush périodique vers CSV **[3/10]**
- [x] **Export CSV obligatoire** **[4/10]** → **DÉCOMPOSÉ :**
  - [x] Validation homogénéité données **[2/10]**
  - [x] Contrôle qualité échantillons **[2/10]**
  - [x] Métadonnées configuration figée **[1/10]**

#### 3.3 Transitions de Mode **[Complexité: 8/10]**
- [x] **Temps Réel → Export** **[7/10]** → **DÉCOMPOSÉ :**
  - [x] Sauvegarde configuration actuelle **[2/10]**
  - [x] Verrouillage interface (3 paramètres + onglet avancé) **[3/10]**
  - [x] Switch buffer court → buffer production **[2/10]**
  - [x] Changement mode AcquisitionManager **[3/10]**
- [x] **Export → Temps Réel** **[7/10]** → **DÉCOMPOSÉ :**
  - [x] Finalisation et fermeture fichier CSV **[3/10]**
  - [x] Déverrouillage interface complète **[2/10]**
  - [x] Switch buffer production → buffer court **[2/10]**
  - [x] Restauration mode exploration **[2/10]**
- [x] **Switch automatique** **[9/10]** → **DÉCOMPOSÉ :**
  - [x] Détection action "Export" (bouton configurer) **[2/10]**
  - [x] Détection action "Arrêt Export" **[1/10]**
  - [x] State machine : EXPLORATION ↔ EXPORT **[3/10]**
  - [x] Guards de transition (validation état) **[3/10]**
  - [x] Rollback automatique si échec transition **[4/10]**

### 4. 🧮 Conversion ADC et Calibration

#### 4.1 Facteurs de Conversion ADC **[Complexité: 2/10]**
- [x] **Constantes par gain** : **[1/10]**
  - [x] Gain 1: 4.76837E-7 V/LSB (±4.0V) **[1/10]**
  - [x] Gain 2: 2.38419E-7 V/LSB (±2.0V) **[1/10]**
  - [x] Gain 4: 1.19209E-7 V/LSB (±1.0V) **[1/10]**
  - [x] Gain 8: 5.96046E-8 V/LSB (±0.5V) **[1/10]**
  - [x] Gain 16: 2.98023E-8 V/LSB (±0.25V) **[1/10]**

#### 4.2 Fonction convert_adc_to_voltage() **[Complexité: 3/10]**
- [x] **Entrée** : code ADC brut + gain du canal **[2/10]**
- [x] **Sortie V to V/m** **[3/10]** → **DÉCOMPOSÉ :**
  - [x] Conversion ADC → tension en volts **[1/10]**
  - [x] Application facteur V to V/m optionnel **[2/10]**
  - [x] Gestion unités selon ComboBox **[1/10]**
- [x] **Gestion gains automatique** **[4/10]** → **DÉCOMPOSÉ :**
  - [x] Dictionnaire gains par canal ADC **[1/10]**
  - [x] Lookup facteur conversion selon gain **[1/10]**
  - [x] Validation range ADC selon gain **[2/10]**
  - [x] Cache calculs pour performance **[1/10]**

### 5. 📊 Contrôles d'Acquisition (Adaptatifs)

#### 5.1 Mode Temps Réel **[Complexité: 5/10]**
- [x] **🟢 Démarrer Exploration** **[6/10]** → **DÉCOMPOSÉ :**
  - [x] Validation configuration 3 paramètres **[2/10]**
  - [x] Initialisation AcquisitionManager mode réactif **[3/10]**
  - [x] Démarrage thread acquisition **[2/10]**
  - [x] Activation timer affichage temps réel **[1/10]** ✅ **Validé** : Timer activé automatiquement au démarrage de l'acquisition, désactivé à l'arrêt
- [x] **🔴 Arrêter** **[3/10]** → **DÉCOMPOSÉ :**
  - [x] Signal stop vers thread acquisition **[1/10]**
  - [x] Attente arrêt propre thread **[2/10]**
  - [x] Reset interface status **[1/10]**
- [x] **💾 Configurer Export** **[5/10]** → **DÉCOMPOSÉ :**
  - [x] QDialog configuration export **[2/10]**
  - [x] Validation paramètres export **[2/10]**
  - [x] Transition automatique vers Mode Export **[3/10]**
- [x] **Status** : EXPLORATION / PAUSED / STOPPED **[2/10]**

#### 5.2 Mode Export **[Complexité: 6/10]**
- [ ] **Dialog Configuration Export** **[4/10]** → **DÉCOMPOSÉ :**
  ```
  ┌─── Configuration Export ───┐
  │ Dossier: [C:\Data\] [📁]   │
  │ Nom: [Default        ]     │
  │ → 2025-01-15-1430_Default_vsTime.csv │
  │ Durée: [300] s ☐ Continu   │
  │ [💾 Démarrer Export]       │
  └────────────────────────────┘
  ```
  - [ ] QFileDialog sélection dossier **[1/10]**
  - [ ] QLineEdit nom fichier + auto-generation **[2/10]**
  - [ ] QSpinBox durée + QCheckBox continu **[2/10]**
  - [ ] Preview nom fichier final **[1/10]**
- [ ] **🟢 Démarrer Acquisition** **[7/10]** → **DÉCOMPOSÉ :**
  - [ ] Validation configuration export **[2/10]**
  - [ ] Verrouillage interface complète **[3/10]**
  - [ ] Initialisation fichier CSV + headers **[2/10]**
  - [ ] Switch AcquisitionManager mode export **[3/10]**
- [ ] **🔴 Arrêter** **[6/10]** → **DÉCOMPOSÉ :**
  - [ ] Signal stop acquisition **[1/10]**
  - [ ] Finalisation fichier CSV **[3/10]**
  - [ ] Déverrouillage interface **[2/10]**
  - [ ] Transition retour Mode Temps Réel **[2/10]**
- [ ] **⏸️ Pause** **[5/10]** → **DÉCOMPOSÉ :**
  - [ ] Pause thread acquisition (garde buffer) **[2/10]**
  - [ ] Indicateur visuel pause **[1/10]**
  - [ ] Reprise sans perte données **[3/10]**
- [ ] **Status + Progress** **[4/10]** → **DÉCOMPOSÉ :**
  - [ ] QLabel status textuel **[1/10]**
  - [ ] QProgressBar progression **[2/10]**
  - [ ] Calcul % progression temps réel **[2/10]**

### 6. 💾 Export CSV (Mode Export uniquement)

#### 6.0 Méthodes du module csv_exporter.py
- `ExportConfig` : dataclass de configuration export (output_dir, filename_base, duration_seconds, metadata, v_to_vm_factor)
- `CSVExporter.start_export(config: ExportConfig) -> bool` : Démarre un export CSV avec la configuration donnée
- `CSVExporter.stop_export() -> bool` : Arrête l'export, finalise et ferme le fichier
- `CSVExporter.add_sample(sample: AcquisitionSample)` : Ajoute un échantillon à la queue d'export
- `CSVExporter.add_samples(samples: List[AcquisitionSample])` : Ajoute plusieurs échantillons à la queue d'export
- `CSVExporter.is_exporting` (propriété bool) : Indique si un export est en cours
- `CSVExporter.samples_written` (propriété int) : Nombre d'échantillons écrits
- `CSVExporter.get_export_status() -> dict` : Retourne un dictionnaire de statut (état, nombre écrits, taille de la queue, config)

#### 6.1 Export Automatique Streaming **[Complexité: 7/10]**
- [x] **Format fichier** **[3/10]** → **DÉCOMPOSÉ :**
  - [x] Génération nom avec timestamp **[1/10]**
  - [x] Pattern `YYYY-MM-DD-HHMM_[Description]_vsTime.csv` **[1/10]**
  - [x] Validation nom fichier (caractères valides) **[1/10]**
- [x] **Écriture continue streaming** **[8/10]** → **DÉCOMPOSÉ :**
  - [x] Thread séparé pour écriture CSV **[3/10]**
  - [x] Queue thread-safe acquisition → écriture **[3/10]**
  - [x] Buffer circulaire pour batch writes **[2/10]**
  - [x] Flush périodique vers disque **[2/10]**
  - [x] Gestion erreurs écriture disque **[3/10]**
- [x] **Métadonnées complètes** **[4/10]** → **DÉCOMPOSÉ :**
  - [x] Headers configuration figée (3 paramètres) **[1/10]**
  - [x] Métadonnées hardware (gains ADC, DDS) **[2/10]**
  - [x] Timestamp début/fin acquisition **[1/10]**
  - [x] Hash configuration pour vérification **[1/10]**

#### 6.2 Structure CSV **[Complexité: 5/10]**
- [x] **Headers métadonnées** **[4/10]** → **DÉCOMPOSÉ :**
  - [x] Section config : dates, mode, paramètres **[2/10]**
  - [x] Section hardware : gains, fréquences **[2/10]**
  - [x] Section conversions : facteurs, unités **[1/10]**
  - [x] Délimiteurs standards CSV **[1/10]**
- [x] **Colonnes données** **[5/10]** → **DÉCOMPOSÉ :**
  - [x] Colonne timestamp (ISO format) **[1/10]**
  - [x] 8 colonnes canaux ADC avec unités **[2/10]**
  - [x] Métadonnées acquisition (fréq réelle, qualité) **[2/10]**
  - [x] Formatage numérique cohérent **[1/10]**
- [x] **Traçabilité** **[3/10]** → **DÉCOMPOSÉ :**
  - [x] Facteur V to V/m utilisé **[1/10]**
  - [x] Gains ADC par canal **[1/10]**
  - [x] Fréquence acquisition réelle **[2/10]**

### 7. ⚙️ Onglet Réglages Avancés (Integration AD9106_ADS131A04_GUI.py)

#### 7.1 Structure de l'Onglet Avancé **[Complexité: 2/10]**
- [x] **Réutilisation du code existant** : Classes DDSControl et ADCControl **[1/10]** ✅ **Validé** : Composants DDSControlAdvanced et ADCControlAdvanced créés
- [x] **Intégration TabWidget** : Ajout comme 2ème onglet **[2/10]** ✅ **Validé** : Onglet avancé intégré dans l'interface principale
- [x] **Thème unifié** : Application du même thème sombre **[2/10]** ✅ **Validé** : Thème cohérent avec l'interface principale
- [x] **Barre de connexion partagée** **[3/10]** → **DÉCOMPOSÉ :**
  - [x] Référence unique SerialCommunicator **[1/10]** ✅ **Validé** : Même instance SerialCommunicator partagée
  - [x] Partage état connexion entre onglets **[2/10]** ✅ **Validé** : État connexion synchronisé
  - [x] Synchronisation boutons connexion **[1/10]** ✅ **Validé** : Connexion automatique au démarrage

#### 7.2 Contrôles DDS Avancés (reprend DDSControl) **[Complexité: 2/10]**
- [x] **4 DDS individuels** en grille 2x2 : **[1/10]** ✅ **Validé** : Layout 2x2 avec contrôles individuels
  - [x] **Gain** : SpinBox 0-16376 (précision complète) **[1/10]** ✅ **Validé** : SpinBox avec range complet
  - [x] **Phase** : SpinBox 0-65535 + conversion degrés **[1/10]** ✅ **Validé** : Conversion automatique degrés ↔ valeur numérique
  - [x] **Mode AC/DC** : Sélection par DDS (automatique AC pour compatibilité) **[1/10]** ✅ **Validé** : Mode AC automatique pour tous les DDS
  - [x] **Boutons d'application** : Par DDS individuel **[1/10]** ✅ **Validé** : Bouton "Appliquer" par DDS
  - [x] **Configuration globale** **[3/10]** → **DÉCOMPOSÉ :**
    - [x] **Fréquence synchronisée** **[4/10]** → **DÉCOMPOSÉ :**
      - [x] QDoubleSpinBox 0.1-1MHz **[1/10]** ✅ **Validé** : SpinBox fréquence globale
      - [x] Signal vers onglet principal **[2/10]** ✅ **Validé** : Signal frequency_changed émis
      - [x] Validation range hardware **[2/10]** ✅ **Validé** : Range 0.1-1MHz respecté
    - [x] **Application simultanée** **[2/10]** → **DÉCOMPOSÉ :**
      - [x] QPushButton "Appliquer Tous DDS" **[1/10]** ✅ **Validé** : Bouton "Appliquer à tous DDS"
      - [x] Loop application séquentielle **[1/10]** ✅ **Validé** : Application via SerialCommunicator

#### 7.3 Configuration ADC Avancée (reprend ADCControl) **[Complexité: 1/10]**
- [x] **Timing ADC** : **[1/10]** ✅ **Validé** : Tous les paramètres de timing implémentés
  - [x] **CLKIN Divider** : ComboBox [2,4,6,8,10,12,14] **[1/10]** ✅ **Validé** : ComboBox avec toutes les valeurs
  - [x] **ICLK Divider** : ComboBox [2,4,6,8,10,12,14] **[1/10]** ✅ **Validé** : ComboBox avec toutes les valeurs
  - [x] **Oversampling** : ComboBox [32,48,64...4096] **[1/10]** ✅ **Validé** : ComboBox avec toutes les valeurs d'oversampling
- [x] **Gains ADC** : **[1/10]** ✅ **Validé** : Contrôles de gains complets
  - [x] **4 canaux individuels** : ComboBox [1,2,4,8,16] **[1/10]** ✅ **Validé** : 4 ComboBox pour les gains individuels
  - [x] **Synchronisation** : Facteurs de conversion automatiques **[2/10]** ✅ **Validé** : Facteurs de conversion intégrés
  - [x] **Chaîne de synchronisation des gains ADC (UI → backend → ADCConverter)** **[2/10]** ✅ **Validé** : Chaîne complète implémentée
    - [x] L'UI transmet la demande de gain au backend ✅ **Validé** : Signal gain_changed émis
    - [x] Le backend applique le gain matériel via SerialCommunicator ✅ **Validé** : Appel set_adc_gain()
    - [x] Le backend met à jour l'ADCConverter avec le mapping {canal: gain} ✅ **Validé** : Synchronisation via AcquisitionManager
    - [x] L'UI n'utilise que le numéro de canal pour la conversion ✅ **Validé** : Architecture respectée
    - [x] **Note :** La synchronisation des gains est garantie par le backend, assurant la cohérence entre la configuration matérielle effective et la conversion logicielle pour la traçabilité scientifique.
- [x] **Références** : **[1/10]** ✅ **Validé** : Configuration des références complète
  - [x] **Negative Reference** : CheckBox **[1/10]** ✅ **Validé** : CheckBox avec style moderne
  - [x] **High Resolution** : CheckBox **[1/10]** ✅ **Validé** : CheckBox activé par défaut
  - [x] **Reference Voltage** : ComboBox [2.442V, 4.0V] **[1/10]** ✅ **Validé** : ComboBox avec les deux tensions
  - [x] **Reference Selection** : ComboBox [External, Internal] **[1/10]** ✅ **Validé** : ComboBox avec sélection interne/externe

#### 7.4 Synchronisation Entre Onglets **[Complexité: 6/10]**
- [ ] **Configuration 3 paramètres → Avancé** **[5/10]** → **DÉCOMPOSÉ :**
  - [ ] **Gain DDS propagation** **[4/10]** → **DÉCOMPOSÉ :**
    - [x] Signal gainChanged depuis principal **[1/10]**
    - [x] Mise à jour simultanée DDS1 & DDS2 **[2/10]**
    - [x] Validation ranges cohérentes **[2/10]**
  - [ ] **Fréquence propagation** **[5/10]** → **DÉCOMPOSÉ :**
    - [ ] Signal frequencyChanged **[2/10]**
    - [ ] Update widget fréquence avancé **[1/10]**
    - [ ] Application hardware immédiate **[3/10]**
  - [ ] **N_avg → Métadonnées** **[6/10]** → **DÉCOMPOSÉ :**
    - [ ] Pas de contrôle ADC direct **[1/10]**
    - [ ] Stockage valeur pour export CSV **[2/10]**
    - [ ] Affichage informatif dans onglet avancé **[1/10]**
    - [ ] Calcul moyennage logiciel si nécessaire **[3/10]**
- [ ] **Avancé → Configuration 3 paramètres** **[6/10]** → **DÉCOMPOSÉ :**
  - [ ] **Fréquence retour** **[5/10]** → **DÉCOMPOSÉ :**
    - [ ] Signal depuis widget avancé **[2/10]**
    - [ ] Update principal sans boucle **[2/10]**
    - [ ] Prévention récursion signaux **[2/10]**

- [ ] **Verrouillage selon mode** **[7/10]** → **DÉCOMPOSÉ :**
  - [ ] **Mode Export lecture seule** **[6/10]** → **DÉCOMPOSÉ :**
    - [ ] Désactivation tous widgets avancés **[2/10]**
    - [ ] Sauvegarde état avant verrouillage **[2/10]**
    - [ ] Indicateur visuel "Export en cours" **[1/10]**
    - [ ] Prévention modifications accidentelles **[2/10]**
  - [ ] **Mode Temps Réel modifiable** **[8/10]** → **DÉCOMPOSÉ :**
    - [ ] Réactivation widgets avancés **[2/10]**
    - [ ] Restauration état pré-export **[2/10]**
    - [ ] Synchronisation immédiate avec principal **[3/10]**
    - [ ] Validation cohérence post-transition **[2/10]**

#### 7.5 Intégration SerialCommunicator **[Complexité: 3/10]**
- [ ] **Instance partagée** : Même communicator pour les 2 onglets **[2/10]**
- [ ] **Initialisation par défaut** : Utilisation de `init_default_config()` **[2/10]**
- [ ] **État mémoire** **[4/10]** → **DÉCOMPOSÉ :**
  - [ ] Lecture memory_state au démarrage **[1/10]**
  - [ ] Synchronisation bidirectionnelle **[2/10]**
    - [ ] Persistance modifications **[2/10]**
  - [ ] **Configuration au démarrage** **[3/10]** → **DÉCOMPOSÉ :**
    - [ ] Application automatique de la config par défaut **[2/10]**
    - [ ] **Sync 3 paramètres par défaut** **[4/10]** → **DÉCOMPOSÉ :**
      - [ ] Lecture valeurs depuis SerialCommunicator.memory_state **[1/10]**
      - [ ] Application aux widgets principaux **[2/10]**
      - [ ] Propagation vers onglet avancé **[2/10]**

### 8. 🛠️ Gestion d'Erreurs

#### 8.1 Validation Paramètres **[Complexité: 4/10]**
- [ ] **Mode Temps Réel validation** **[4/10]** → **DÉCOMPOSÉ :**
  - [ ] Validation ranges (Gain: 0-16376, Freq: 0.1-1MHz) **[2/10]**
  - [ ] Validation hardware disponibilité **[2/10]**
  - [ ] Feedback immédiat utilisateur **[1/10]**
- [ ] **Mode Export validation** **[3/10]** → **DÉCOMPOSÉ :**
  - [ ] Validation configuration complète **[2/10]**
  - [ ] Validation chemin fichier export **[1/10]**
  - [ ] Validation espace disque disponible **[2/10]**
- [ ] **Messages contextuels** **[3/10]** → **DÉCOMPOSÉ :**
  - [ ] QMessageBox erreurs selon mode **[1/10]**
  - [ ] StatusBar messages temporaires **[1/10]**
  - [ ] Tooltips contextaux **[1/10]**

#### 8.2 Gestion Déconnexions **[Complexité: 6/10]**
- [ ] **Mode Temps Réel déconnexion** **[5/10]** → **DÉCOMPOSÉ :**
  - [ ] Détection perte communication **[2/10]**
  - [ ] Tentatives reconnexion automatique **[3/10]**
  - [ ] Affichage états erreur dans interface **[2/10]**
  - [ ] Fallback mode dégradé **[1/10]**
- [ ] **Mode Export déconnexion** **[8/10]** → **DÉCOMPOSÉ :**
  - [ ] Détection immédiate perte communication **[2/10]**
  - [ ] Sauvegarde urgente buffer vers CSV **[3/10]**
  - [ ] Finalisation propre fichier **[2/10]**
  - [ ] Transition forcée vers Mode Temps Réel **[2/10]**
  - [ ] Rapport incident utilisateur **[2/10]**

### 9. **Robustesse accès buffer et découplage hardware**
  - [x] Vérifier que l'UI et les autres modules accèdent uniquement au buffer via AcquisitionManager (jamais à SerialCommunicator) ✅ **Validé** : Architecture respectée - UI utilise uniquement AcquisitionManager.get_latest_data()
  - [x] S'assurer que le thread d'acquisition utilise la bonne méthode de SerialCommunicator pour remplir le buffer ✅ **Validé** : Thread utilise SerialCommunicator.acquisition(n_avg) simplifiée
  - [x] Supprimer tout accès direct à SerialCommunicator ailleurs que dans AcquisitionManager ✅ **Validé** : AcquisitionManager centralise tous les appels hardware
  - [x] Documenter ce pattern dans la doc technique pour la traçabilité scientifique ✅ **Validé** : Pattern documenté dans la conversation - séparation claire des responsabilités

---

## 📊 **Résumé des Complexités par Section**

| Section | Complexité Moyenne | Tâches Difficiles (≥7/10) |
|---------|-------------------|---------------------------|
| **1. Interface Principale** | 3.2/10 | Fréquence synchronisée (7/10) |
| **2. Affichage Numérique** | 4.0/10 | - |
| **3. Backend 2 Modes** | 7.0/10 | Pause automatique (9/10), Reprise auto (8/10), Switch auto (9/10) |
| **4. Conversion ADC** | 2.5/10 | - |
| **5. Contrôles Acquisition** | 5.0/10 | Démarrer Acquisition Export (7/10) |
| **6. Export CSV** | 6.0/10 | Écriture streaming (8/10) |
| **7. Onglet Avancé** | 3.0/10 | Mode Temps Réel modifiable (8/10), Moyenne gains (7/10) |
| **8. Gestion Erreurs** | 5.0/10 | Gestion déconnexions Export (8/10) |

---

## 🔥 **Top 10 des Sous-Tâches les Plus Difficiles**

| Rang | Sous-Tâche | Complexité | Section |
|------|------------|------------|---------|
| 1 | Pause automatique (~100ms) lors modification paramètres | **9/10** | Backend Temps Réel |
| 1 | Switch automatique selon action utilisateur | **9/10** | Transitions |
| 3 | Écriture continue pendant acquisition | **8/10** | Export CSV |
| 3 | Reprise automatique de l'acquisition | **8/10** | Backend Temps Réel |
| 3 | Mode Temps Réel : Onglet avancé modifiable | **8/10** | Synchronisation |
| 3 | Mode Export : Sauvegarde données + arrêt propre | **8/10** | Gestion Erreurs |
| 7 | Acquisition continue en arrière-plan | **7/10** | Backend Temps Réel |
| 7 | Fréquence synchronisée entre onglets | **7/10** | Interface |
| 7 | Démarrer Acquisition Export (verrouille interface) | **7/10** | Contrôles |
| 7 | Moyenne DDS1/DDS2 gains → Gain DDS principal | **7/10** | Synchronisation |

---

## 🗂️ Structure de Fichiers

```
getE3D/interface/
├── AD9106_ADS131A04_Visualization_GUI.py      # Interface principale
├── components/
│   ├── mode_controller.py                     # Gestion des 2 modes
│   ├── acquisition_manager.py                 # Backend acquisition adaptatif
│   ├── numeric_display.py                     # Affichage 8 canaux temps réel
│   ├── adc_converter.py                       # Conversions ADC + facteur V to V/m
│   ├── csv_exporter.py                        # Export streaming Mode Export
│   ├── data_buffer.py                         # Buffer adaptatif selon mode
│   ├── dds_control_advanced.py               # Contrôles DDS avancés (réutilise code existant)
│   └── adc_control_advanced.py               # Contrôles ADC avancés (réutilise code existant)
└── data/                                       # Exports CSV générés
```

---

## 🚀 Ordre de Développement (Par complexité croissante)

### **🟢 Sprint 1 : Fondations (Tâches 1-3/10)**
1. **Onglet Réglages Avancés** : Intégration code existant **[1-2/10]**
2. **Conversions ADC** : Constantes et calculs **[1-3/10]**
3. **Interface 3 paramètres** : Layout LabVIEW **[2-3/10]**

### **🟡 Sprint 2 : Interface Standard (Tâches 3-5/10)**
4. **Affichage 8 canaux** : Grille + couleurs **[3-5/10]**
5. **Contrôles de base** : Boutons et status **[2-4/10]**
6. **Export CSV structure** : Format et headers **[3-5/10]**

### **🟠 Sprint 3 : Synchronisation (Tâches 5-6/10)**
7. **Synchronisation onglets** : Logique de liaison **[4-6/10]**
8. **Validation paramètres** : Contrôles et messages **[3-4/10]**

### **🟠 Sprint 4 : Backend Complexe (Tâches 7-9/10)**
9. **Backend acquisition** : Threading + acquisition continue **[6-8/10]**
10. **Export streaming** : Écriture continue **[8/10]**
11. **Gestion des modes** : Transitions automatiques **[7-9/10]**

### **🔴 Sprint 5 : Finitions Critiques (Tâches 8-9/10)**
12. **Pauses micro et reprises** : Logique réactive **[9/10]**
13. **Switch automatique** : Détection intelligente **[9/10]**
14. **Robustesse** : Gestion déconnexions et erreurs **[5-8/10]**

---

## 🏗️ **Notes d'Architecture Validées**

### **Pattern de Gestion Série (Validé)**
- **Séparation des responsabilités** : 
  - `SerialCommunicator` : Communication hardware pure (méthode `acquisition(n_avg)` simplifiée)
  - `AcquisitionManager` : Gestion des modes, buffer, thread d'acquisition
  - `UI` : Affichage et contrôles utilisateur (accès buffer via `AcquisitionManager.get_latest_data()`)
- **Connexion série** : Gérée au niveau UI principale (constructeur `MainApp`) avec déconnexion propre dans `closeEvent()`
- **Vidage buffer série** : Centralisé dans `AcquisitionManager` lors des reprises après pause, implémenté dans `SerialCommunicator.clear_serial_buffer()`

### **Simplification Acquisition (Validé)**
- **Suppression des retry complexes** : Une seule méthode `acquisition(n_avg)` dans `SerialCommunicator`
- **Gestion des erreurs** : Validation des données dans `AcquisitionManager`, rollback si nécessaire
- **Performance** : Suppression du `time.sleep` dans la boucle d'acquisition pour maximiser le débit

### **Intégration UI (Validé)**
- **Connexion automatique** : Port série ouvert au démarrage de l'UI
- **Affichage live** : Timer QTimer connecté à `update_display()` pour rafraîchissement périodique
- **Gestion des modes** : Transitions automatiques entre Temps Réel et Export fonctionnelles
- **Synchronisation bidirectionnelle** : Architecture centralisée via AcquisitionManager avec signal `configuration_changed` ✅ **Validé**

---

## 📋 Critères de Validation Phase 1

### Fonctionnalités Core :
- [ ] **2 modes distincts** avec transitions automatiques propres
- [ ] **Affichage temps réel** : 8 canaux avec facteur V to V/m
- [ ] **Configuration réactive** (Temps Réel) vs figée (Export)
- [ ] **Export CSV** avec métadonnées complètes (Mode Export uniquement)
- [ ] **Onglet Réglages Avancés** : Accès complet DDS/ADC fonctionnel

### Performance :
- [ ] **Réactivité** : Modifications visibles <200ms (Mode Temps Réel)
- [ ] **Stabilité** : Acquisition continue sans interruption (Mode Export)
- [ ] **Mémoire optimisée** : Buffer adaptatif selon le mode
- [ ] **Robustesse** : Gestion déconnexions selon le mode actif
- [ ] **Synchronisation** : Configuration 3 paramètres ↔ Réglages avancés

### Intégration :
- [x] **Code existant réutilisé** : DDSControl et ADCControl fonctionnels ✅ **Validé**
- [x] **Thème unifié** : Interface cohérente entre les onglets ✅ **Validé**
- [x] **Configuration par défaut** : SerialCommunicator.init_default_config() appliquée ✅ **Validé**
- [x] **État mémoire synchronisé** : memory_state partagé entre onglets ✅ **Validé**
- [x] **Synchronisation bidirectionnelle** : Configuration 3 paramètres ↔ Réglages avancés ✅ **Validé** : Architecture centralisée via AcquisitionManager

## 🔄 Migration : AcquisitionManager comme Modèle Central de Configuration

#### Objectif
- Utiliser `AcquisitionManager` comme source unique de vérité pour la configuration d'acquisition (gain_dds, freq_hz, n_avg).
- Toutes les modifications passent par `AcquisitionManager.update_configuration()`.
- L'UI se synchronise automatiquement via un signal `configuration_changed` émis par `AcquisitionManager`.
- Seul `AcquisitionManager` applique la configuration au hardware (SerialCommunicator).

#### Étapes à réaliser (détaillées)
- [x] **Ajouter un signal `configuration_changed` (PyQt) dans `AcquisitionManager`** (Complexité : 2)
- [x] **Émettre ce signal à chaque modification effective de la configuration** (Complexité : 2)
- [ ] **Identifier tous les points d'entrée utilisateur dans les widgets (principal, avancé, etc.)** (Complexité : 3)
    - [x] Lister tous les widgets modifiant la config (Complexité : 2)
        - [ ] Principal : ConfigurationWidget (gain_spinbox, freq_spinbox, navg_spinbox)
            - gain_spinbox : QSpinBox (valueChanged)
            - freq_spinbox : QDoubleSpinBox (editingFinished)
            - navg_spinbox : QSpinBox (valueChanged)
        - [ ] Avancé : AdvancedSettingsWidget
            - freq_spin : QDoubleSpinBox (editingFinished, bouton "Appliquer à tous DDS")
            - DDSControlAdvanced (gain_changed, phase_changed)
            - ADCControlAdvanced (gain_changed)
    - [x] Rechercher tous les signaux Qt connectés à des modifications de paramètres (Complexité : 3)
        - [ ] Principal :
            - ConfigurationWidget.configuration_changed (dict)
        - [ ] Avancé :
            - AdvancedSettingsWidget.frequency_changed (float)
            - AdvancedSettingsWidget.dds_gain_changed (int, int)
            - AdvancedSettingsWidget.dds_phase_changed (int, int)
            - AdvancedSettingsWidget.adc_gain_changed (int, int)
    - [x] Vérifier les callbacks personnalisés (Complexité : 3)
        - [ ] Principal : _on_config_changed, _apply_frequency_to_all_dds
        - [ ] Avancé : _apply_frequency_to_all_dds, set_frequency, set_dds_gain, set_dds_phase, set_adc_gain
    - [x] Documenter les points d'entrée trouvés (Complexité : 2)
        - [ ] Voir ci-dessus : chaque widget, signal et callback est listé pour traçabilité et future documentation utilisateur.
- [x] **Remplacer les connexions directes (`valueChanged`, `editingFinished`, etc.) pour qu'elles appellent une méthode qui construit un dict de config et appelle `acquisition_manager.update_configuration(config)`** (Complexité : 5)
    - [x] Créer une méthode utilitaire de construction du dict de config (Complexité : 3)
    - [x] Modifier chaque callback pour utiliser cette méthode (Complexité : 4)
        - [x] Identifier les callbacks à modifier (Complexité : 2)
        - [x] Adapter la signature des callbacks (Complexité : 3)
        - [x] Remplacer l'appel direct par l'appel à la méthode utilitaire (Complexité : 2)
    - [x] Tester la propagation de la config (Complexité : 3)
        - [x] Vérifier la MAJ du modèle central (Complexité : 2)
        - [x] Vérifier la MAJ des autres widgets (Complexité : 2)
    - [ ] Gérer les cas de validation/annulation utilisateur (Complexité : 4)
        - [ ] Détecter les annulations (Complexité : 2)
        - [ ] Gérer les retours à l'état précédent (Complexité : 3)
- [ ] **S'assurer que la config envoyée est toujours complète et cohérente** (Complexité : 4)
    - [ ] Définir les valeurs par défaut pour chaque paramètre (Complexité : 2)
    - [ ] Ajouter des vérifications de cohérence avant l'envoi (Complexité : 3)
        - [ ] Implémenter une fonction de validation (Complexité : 2)
        - [ ] Ajouter des messages d'erreur utilisateur (Complexité : 2)
    - [ ] Gérer les cas de valeurs invalides (Complexité : 4)
        - [ ] Détecter les valeurs hors bornes (Complexité : 2)
        - [ ] Proposer une correction automatique ou un message bloquant (Complexité : 3)
    - [ ] Ajouter des tests unitaires de cohérence (Complexité : 4)
        - [ ] Écrire des cas de test pour chaque paramètre (Complexité : 3)
        - [ ] Automatiser la vérification (Complexité : 2)
- [ ] **Ne plus modifier d'autres widgets directement dans les callbacks utilisateur** (Complexité : 3)
- [ ] **Connecter le signal `configuration_changed` à une méthode `set_configuration(config)` dans chaque widget** (Complexité : 4)
    - [ ] Ajouter la méthode `set_configuration(config)` dans chaque widget (Complexité : 3)
        - [ ] Définir la signature et le comportement (Complexité : 2)
        - [ ] Tester la MAJ d'un champ (Complexité : 2)
    - [ ] Connecter le signal dans la classe principale (Complexité : 2)
    - [ ] Tester la mise à jour automatique des widgets (Complexité : 3)
        - [ ] Simuler un changement de config (Complexité : 2)
        - [ ] Vérifier la MAJ visuelle (Complexité : 2)
    - [ ] Gérer la désactivation temporaire des signaux (Complexité : 4)
        - [ ] Implémenter le blocage/déblocage (Complexité : 3)
        - [ ] Vérifier l'absence de boucle (Complexité : 3)
- [ ] **Dans cette méthode, mettre à jour tous les champs (spinbox, etc.) en bloquant temporairement les signaux pour éviter de rappeler `update_configuration`** (Complexité : 6)
    - [ ] Identifier tous les champs à mettre à jour (Complexité : 3)
    - [ ] Implémenter le blocage/déblocage des signaux pour chaque champ (Complexité : 4)
        - [ ] Utiliser blockSignals(True/False) (Complexité : 2)
        - [ ] Utiliser un context manager si besoin (Complexité : 3)
    - [ ] S'assurer que le focus utilisateur n'est pas perdu (Complexité : 5)
        - [ ] Tester le focus avant/après MAJ (Complexité : 3)
        - [ ] Restaurer le focus si besoin (Complexité : 4)
    - [ ] Tester la non-récursivité de la mise à jour (Complexité : 5)
        - [ ] Ajouter un flag de protection (Complexité : 3)
        - [ ] Vérifier l'absence de double appel (Complexité : 3)
- [ ] **Gérer le blocage/déblocage des signaux proprement (try/finally si besoin)** (Complexité : 5)
    - [ ] Utiliser des context managers ou try/finally pour chaque blocage (Complexité : 4)
        - [ ] Écrire un context manager custom si besoin (Complexité : 3)
    - [ ] Vérifier l'absence de fuite de blocage (Complexité : 4)
        - [ ] Ajouter des assertions/tests (Complexité : 3)
    - [ ] Ajouter des tests de robustesse (Complexité : 4)
        - [ ] Simuler des exceptions dans le bloc (Complexité : 3)
    - [ ] Documenter la convention de blocage (Complexité : 2)
- [ ] **Éviter les effets de bord (focus, validation, etc.) lors de la mise à jour** (Complexité : 4)
    - [ ] Lister les effets de bord possibles (Complexité : 2)
    - [ ] Tester la conservation du focus (Complexité : 3)
    - [ ] Gérer les cas de validation automatique (Complexité : 4)
        - [ ] Vérifier la validation sur perte de focus (Complexité : 2)
        - [ ] Gérer les cas d'annulation utilisateur (Complexité : 3)
    - [ ] Ajouter des tests d'UX (Complexité : 3)
- [ ] **S'assurer que la MAJ ne déclenche pas de boucle** (Complexité : 5)
    - [ ] Vérifier l'absence de rappel de `update_configuration` lors de `set_configuration` (Complexité : 4)
        - [ ] Ajouter un flag ou verrou (Complexité : 3)
    - [ ] Ajouter des flags ou verrous si besoin (Complexité : 4)
    - [ ] Tester la stabilité sur des cycles rapides (Complexité : 5)
        - [ ] Simuler des cycles rapides (Complexité : 3)
        - [ ] Vérifier l'absence de crash (Complexité : 3)
    - [ ] Ajouter des logs de détection de boucle (Complexité : 3)
- [ ] **Utiliser `blockSignals(True)`/`blockSignals(False)` autour des `setValue`, etc.** (Complexité : 3)
- [ ] **Si plusieurs widgets sont mis à jour, il faut tous les bloquer** (Complexité : 3)
- [ ] **Supprimer tous les appels à `set_dds_frequency`, `set_dds_gain`, etc. dans les widgets/UI** (Complexité : 4)
- [ ] **Déplacer toute la logique d'application hardware dans une méthode dédiée d'`AcquisitionManager` (appelée après update de la config)** (Complexité : 7) # Coordination, robustesse, gestion des erreurs
    - [ ] Identifier tous les accès hardware dans le code (Complexité : 3)
    - [ ] Centraliser les appels dans une méthode unique (Complexité : 4)
        - [ ] Refactoriser les appels existants (Complexité : 3)
    - [ ] Gérer la séquence pause/update/reprise (Complexité : 5)
        - [ ] Implémenter la pause automatique (Complexité : 3)
        - [ ] Tester la reprise correcte (Complexité : 3)
    - [ ] Tester la robustesse sur erreurs hardware (Complexité : 4)
        - [ ] Simuler des erreurs série (Complexité : 3)
- [ ] **S'assurer que le signal `configuration_changed` ne déclenche pas d'appel hardware côté UI** (Complexité : 4)
- [ ] **Repérer tous les accès directs au hardware et tester la séquence d'application (pause, update, reprise)** (Complexité : 5)
    - [ ] Faire un audit du code pour les accès hardware (Complexité : 3)
    - [ ] Écrire des tests de séquence (Complexité : 4)
        - [ ] Tester la séquence normale (Complexité : 2)
        - [ ] Tester la séquence avec erreur (Complexité : 3)
    - [ ] Simuler des erreurs de communication (Complexité : 5)
        - [ ] Utiliser un mock communicator (Complexité : 3)
    - [ ] Documenter la séquence correcte (Complexité : 2)
- [ ] **Tester tous les chemins utilisateur pour détecter les bugs de synchronisation (race conditions, focus, etc.)** (Complexité : 5)
    - [ ] Lister tous les scénarios utilisateur (Complexité : 3)
    - [ ] Écrire des tests manuels et automatiques (Complexité : 4)
        - [ ] Automatiser les tests de synchronisation (Complexité : 3)
    - [ ] Vérifier la stabilité sous charge (Complexité : 5)
        - [ ] Simuler des entrées rapides (Complexité : 3)
    - [ ] Ajouter des outils de monitoring/logs (Complexité : 3)
- [ ] **Documenter ce pattern dans la doc technique** (Complexité : 2)

---

# Archives

## Contexte
Avec l'évolution de l'architecture, la synchronisation des paramètres d'acquisition (fréquence, gain, n_avg) est désormais centralisée dans `AcquisitionManager`, qui devient la source unique de vérité. Toutes les modifications passent par `AcquisitionManager.update_configuration()` et l'UI se synchronise via le signal `configuration_changed`. Les sections suivantes sont archivées car elles décrivent des approches manuelles ou intermédiaires qui ne sont plus nécessaires.

---

### Ancienne logique de synchronisation manuelle (obsolète)

#### 🔄 Refonte Synchronisation : Logique Modèle Central (Single Source of Truth)
- Cette section proposait la création d'un modèle central dédié (AcquisitionConfigModel) et des signaux personnalisés entre widgets. Elle est remplacée par l'utilisation directe d'AcquisitionManager comme modèle central.

#### Synchronisation entre onglets (Section 7.4)
- Les sous-tâches sur la définition de signaux personnalisés, la connexion signals/slots entre onglets, la propagation manuelle des changements, la gestion des listeners sur widgets source, etc., sont désormais prises en charge par le signal unique d'AcquisitionManager.
- Les sous-tâches sur la prévention des boucles et la gestion du focus restent pertinentes mais doivent être reformulées pour s'appuyer sur la nouvelle architecture.

#### Widget fréquence partagé, signal global frequencyChanged, update simultanée, gestion focus/édition
- Ces points sont couverts par la nouvelle architecture : un seul signal, une seule source de vérité, plus besoin de widget "partagé" ou de signaux globaux manuels.

#### Synchronisation directe entre widgets
- Toute logique d'accès direct entre widgets (ex : advanced_settings ↔ config_widget) est désormais proscrite et remplacée par la synchronisation via AcquisitionManager.

---

#### Décomposition des sous-tâches complexes

- **Identifier tous les points d'entrée utilisateur dans les widgets (principal, avancé, etc.)** (Complexité : 4)
    - [ ] Lister tous les widgets modifiant la config (Complexité : 2)
    - [ ] Rechercher tous les signaux Qt connectés à des modifications de paramètres (Complexité : 3)
    - [ ] Vérifier les callbacks personnalisés (Complexité : 3)
    - [ ] Documenter les points d'entrée trouvés (Complexité : 2)

- **Remplacer les connexions directes (`valueChanged`, `editingFinished`, etc.) pour qu'elles appellent une méthode qui construit un dict de config et appelle `acquisition_manager.update_configuration(config)`** (Complexité : 5)
    - [x] Créer une méthode utilitaire de construction du dict de config (Complexité : 3)
    - [x] Modifier chaque callback pour utiliser cette méthode (Complexité : 4)
        - [x] Identifier les callbacks à modifier (Complexité : 2)
        - [x] Adapter la signature des callbacks (Complexité : 3)
        - [x] Remplacer l'appel direct par l'appel à la méthode utilitaire (Complexité : 2)
    - [x] Tester la propagation de la config (Complexité : 3)
        - [x] Vérifier la MAJ du modèle central (Complexité : 2)
        - [x] Vérifier la MAJ des autres widgets (Complexité : 2)
    - [ ] Gérer les cas de validation/annulation utilisateur (Complexité : 4)
        - [ ] Détecter les annulations (Complexité : 2)
        - [ ] Gérer les retours à l'état précédent (Complexité : 3)

- **S'assurer que la config envoyée est toujours complète et cohérente** (Complexité : 4)
    - [ ] Définir les valeurs par défaut pour chaque paramètre (Complexité : 2)
    - [ ] Ajouter des vérifications de cohérence avant l'envoi (Complexité : 3)
        - [ ] Implémenter une fonction de validation (Complexité : 2)
        - [ ] Ajouter des messages d'erreur utilisateur (Complexité : 2)
    - [ ] Gérer les cas de valeurs invalides (Complexité : 4)
        - [ ] Détecter les valeurs hors bornes (Complexité : 2)
        - [ ] Proposer une correction automatique ou un message bloquant (Complexité : 3)
    - [ ] Ajouter des tests unitaires de cohérence (Complexité : 4)
        - [ ] Écrire des cas de test pour chaque paramètre (Complexité : 3)
        - [ ] Automatiser la vérification (Complexité : 2)

- **Connecter le signal `configuration_changed` à une méthode `set_configuration(config)` dans chaque widget** (Complexité : 4)
    - [ ] Ajouter la méthode `set_configuration(config)` dans chaque widget (Complexité : 3)
        - [ ] Définir la signature et le comportement (Complexité : 2)
        - [ ] Tester la MAJ d'un champ (Complexité : 2)
    - [ ] Connecter le signal dans la classe principale (Complexité : 2)
    - [ ] Tester la mise à jour automatique des widgets (Complexité : 3)
        - [ ] Simuler un changement de config (Complexité : 2)
        - [ ] Vérifier la MAJ visuelle (Complexité : 2)
    - [ ] Gérer la désactivation temporaire des signaux (Complexité : 4)
        - [ ] Implémenter le blocage/déblocage (Complexité : 3)
        - [ ] Vérifier l'absence de boucle (Complexité : 3)

- **Dans cette méthode, mettre à jour tous les champs (spinbox, etc.) en bloquant temporairement les signaux pour éviter de rappeler `update_configuration`** (Complexité : 6)
    - [ ] Identifier tous les champs à mettre à jour (Complexité : 3)
    - [ ] Implémenter le blocage/déblocage des signaux pour chaque champ (Complexité : 4)
        - [ ] Utiliser blockSignals(True/False) (Complexité : 2)
        - [ ] Utiliser un context manager si besoin (Complexité : 3)
    - [ ] S'assurer que le focus utilisateur n'est pas perdu (Complexité : 5)
        - [ ] Tester le focus avant/après MAJ (Complexité : 3)
        - [ ] Restaurer le focus si besoin (Complexité : 4)
    - [ ] Tester la non-récursivité de la mise à jour (Complexité : 5)
        - [ ] Ajouter un flag de protection (Complexité : 3)
        - [ ] Vérifier l'absence de double appel (Complexité : 3)
    - [ ] Ajouter des logs pour le debug (Complexité : 2)

- **Gérer le blocage/déblocage des signaux proprement (try/finally si besoin)** (Complexité : 5)
    - [ ] Utiliser des context managers ou try/finally pour chaque blocage (Complexité : 4)
        - [ ] Écrire un context manager custom si besoin (Complexité : 3)
    - [ ] Vérifier l'absence de fuite de blocage (Complexité : 4)
        - [ ] Ajouter des assertions/tests (Complexité : 3)
    - [ ] Ajouter des tests de robustesse (Complexité : 4)
        - [ ] Simuler des exceptions dans le bloc (Complexité : 3)
    - [ ] Documenter la convention de blocage (Complexité : 2)

- **Éviter les effets de bord (focus, validation, etc.) lors de la mise à jour** (Complexité : 4)
    - [ ] Lister les effets de bord possibles (Complexité : 2)
    - [ ] Tester la conservation du focus (Complexité : 3)
    - [ ] Gérer les cas de validation automatique (Complexité : 4)
        - [ ] Vérifier la validation sur perte de focus (Complexité : 2)
        - [ ] Gérer les cas d'annulation utilisateur (Complexité : 3)
    - [ ] Ajouter des tests d'UX (Complexité : 3)

- **S'assurer que la MAJ ne déclenche pas de boucle** (Complexité : 5)
    - [ ] Vérifier l'absence de rappel de `update_configuration` lors de `set_configuration` (Complexité : 4)
        - [ ] Ajouter un flag ou verrou (Complexité : 3)
    - [ ] Ajouter des flags ou verrous si besoin (Complexité : 4)
    - [ ] Tester la stabilité sur des cycles rapides (Complexité : 5)
        - [ ] Simuler des cycles rapides (Complexité : 3)
        - [ ] Vérifier l'absence de crash (Complexité : 3)
    - [ ] Ajouter des logs de détection de boucle (Complexité : 3)

- **Déplacer toute la logique d'application hardware dans une méthode dédiée d'`AcquisitionManager` (appelée après update de la config)** (Complexité : 5)
    - [ ] Identifier tous les accès hardware dans le code (Complexité : 3)
    - [ ] Centraliser les appels dans une méthode unique (Complexité : 4)
    - [ ] Gérer la séquence pause/update/reprise (Complexité : 5)
        - [ ] Implémenter la pause automatique (Complexité : 3)
        - [ ] Tester la reprise correcte (Complexité : 3)
    - [ ] Tester la robustesse sur erreurs hardware (Complexité : 4)
        - [ ] Simuler des erreurs série (Complexité : 3)

- **Repérer tous les accès directs au hardware et tester la séquence d'application (pause, update, reprise)** (Complexité : 5)
    - [ ] Faire un audit du code pour les accès hardware (Complexité : 3)
    - [ ] Écrire des tests de séquence (Complexité : 4)
        - [ ] Tester la séquence normale (Complexité : 2)
        - [ ] Tester la séquence avec erreur (Complexité : 3)
    - [ ] Simuler des erreurs de communication (Complexité : 5)
        - [ ] Utiliser un mock communicator (Complexité : 3)
    - [ ] Documenter la séquence correcte (Complexité : 2)

- **Tester tous les chemins utilisateur pour détecter les bugs de synchronisation (race conditions, focus, etc.)** (Complexité : 5)
    - [ ] Lister tous les scénarios utilisateur (Complexité : 3)
    - [ ] Écrire des tests manuels et automatiques (Complexité : 4)
        - [ ] Automatiser les tests de synchronisation (Complexité : 3)
    - [ ] Vérifier la stabilité sous charge (Complexité : 5)
        - [ ] Simuler des entrées rapides (Complexité : 3)
    - [ ] Ajouter des outils de monitoring/logs (Complexité : 3)

---
