=============================================================
SYNTHESE COMPLETE : LOGIQUE DE CREATION DES ONGLETS UI GLOBALE
=============================================================

Objectif :
  - Reproduire fidèlement la structure, les layouts, les widgets et la logique de connexion des signaux
    des deux interfaces validées, dans une nouvelle UI globale à 4 onglets, connectée à un metaManager.

Sources analysées :
  - ArcusPerfomax4EXStage/EFImagingBench_Interface_ArcusPerformax4EXStage_v4.py (contrôle moteurs)
  - AD9106_ADS131A04_ElectricField_3D/AD9106_ADS131A04_Visualization_GUI_v2.py (acquisition/excitation)

Structure cible :
  1. Contrôle axes + visualisation (Arcus, onglet 1)
  2. Paramètres moteurs (Arcus, onglet 2)
  3. Acquisition/Export (ElectricField, onglet 1)
  4. Réglages avancés (ElectricField, onglet 2)

Chaque widget doit être connecté au metaManager (et non aux sous-managers directs).

-----------------------------------------------------------------------------

1. Onglets issus de ArcusPerfomax4EXStage/EFImagingBench_Interface_ArcusPerformax4EXStage_v4.py
-----------------------------------------------------------------------------

--- Onglet 1 : Contrôle axes + visualisation ---
  - Layout principal : QVBoxLayout
  - Ligne de contrôle des axes : QHBoxLayout
      * AxisControlWidget("X", ...)
      * AxisControlWidget("Y", ...)
  - Zone du bas : QHBoxLayout
      * À gauche : QGroupBox "Configuration Scan 2D" (QGridLayout)
          - QDoubleSpinBox pour x_min, x_max, y_min, y_max
          - QSpinBox pour N (lignes)
          - QComboBox pour mode (E/S)
          - QPushButton "Générer le scan"
          - QPushButton "Exécuter le scan"
      * À droite : GeometricalViewWidget (visualisation)
  - Connexions :
      * Boutons AxisControlWidget → metaManager.move_to, home, stop, etc.
      * Boutons scan → metaManager.generate_scan2d, inject_scan_batch
      * Signal position_changed → visual_widget.set_current_position
      * Signal status_changed → activation/désactivation des boutons

--- Onglet 2 : Paramètres moteurs ---
  - Layout principal : QVBoxLayout
  - Widget principal : SpeedParametersWidget
      * 2 lignes (X, Y), 4 QSpinBox par ligne (ls, hs, acc, dec)
      * QPushButton "Appliquer Paramètres"
  - Connexions :
      * Bouton appliquer → metaManager.set_axis_params
      * Chargement initial des paramètres via metaManager.get_axis_params

-----------------------------------------------------------------------------

2. Onglets issus de AD9106_ADS131A04_ElectricField_3D/AD9106_ADS131A04_Visualization_GUI_v2.py
-----------------------------------------------------------------------------

--- Onglet 3 : Acquisition/Export ---
  - Layout principal : QHBoxLayout
  - À gauche : QVBoxLayout
      * MainParametersConfigWidget (gain DDS, freq, n_avg)
      * ExportWidget (gestion export CSV)
  - Au centre : NumericDisplayWidget (affichage valeurs live)
  - À droite : RealtimeGraphWidget (graphique temps réel)
  - Connexions :
      * MainParametersConfigWidget.configuration_changed → metaManager.update_configuration
      * ExportWidget.start_export → metaManager.start_export_csv
      * ExportWidget.stop_export → metaManager.stop_export_csv
      * metaManager.data_ready → NumericDisplayWidget.update_values
      * metaManager.data_ready → RealtimeGraphWidget.update_graph
      * metaManager.configuration_changed → MainParametersConfigWidget.set_configuration
      * metaManager.mode_changed → activation/désactivation des widgets

--- Onglet 4 : Réglages avancés ---
  - Layout principal : QVBoxLayout
  - Widget principal : AdvancedSettingsWidget
      * Zone DDS (gauche) : 4 DDSControlAdvanced (gain, phase)
      * Zone ADC (droite) : ADCControlAdvanced (gains ADC)
      * Barre de contrôle fréquence globale
  - Connexions :
      * DDSControlAdvanced.gain_changed/phase_changed → metaManager.update_configuration
      * ADCControlAdvanced.gain_changed → metaManager.update_configuration
      * metaManager.configuration_changed → AdvancedSettingsWidget.set_* (gain, phase, freq)
      * metaManager.mode_changed → activation/désactivation des widgets

-----------------------------------------------------------------------------

3. Points transverses et exigences d’intégration
-----------------------------------------------------------------------------

- Tous les widgets doivent être instanciés avec le metaManager comme backend (adapter les constructeurs si besoin).
- Les signaux PyQt5 doivent être connectés au metaManager, qui relaie vers les sous-managers.
- Les callbacks asynchrones (ex : get_axis_params) doivent passer par le metaManager.
- Les layouts, styles, et organisation visuelle doivent être fidèlement reproduits.
- Les méthodes utilitaires (conversion cm/inc, etc.) doivent être appelées via le metaManager.
- Les boutons d’activation/désactivation doivent suivre la logique d’origine (mode exploration/export).

-----------------------------------------------------------------------------

4. Synthèse des widgets à réutiliser (ou à adapter)
-----------------------------------------------------------------------------

- AxisControlWidget (contrôle X/Y)
- SpeedParametersWidget (paramètres moteurs)
- GeometricalViewWidget (visualisation)
- MainParametersConfigWidget (config acquisition)
- ExportWidget (gestion export)
- NumericDisplayWidget (affichage live)
- RealtimeGraphWidget (graphique temps réel)
- AdvancedSettingsWidget (réglages avancés DDS/ADC)

-----------------------------------------------------------------------------

5. Synthèse des connexions de signaux (backend <-> UI)
-----------------------------------------------------------------------------

- metaManager.position_changed → GeometricalViewWidget.set_current_position
- metaManager.status_changed → activation/désactivation des boutons
- metaManager.data_ready → NumericDisplayWidget.update_values, RealtimeGraphWidget.update_graph
- metaManager.configuration_changed → MainParametersConfigWidget.set_configuration, AdvancedSettingsWidget.set_*
- metaManager.mode_changed → activation/désactivation des widgets
- Boutons UI → metaManager (move_to, home, stop, set_axis_params, generate_scan2d, inject_scan_batch, start_export_csv, stop_export_csv, update_configuration)

-----------------------------------------------------------------------------

6. Contraintes et recommandations
-----------------------------------------------------------------------------

- Ne pas dupliquer inutilement le code : factoriser au maximum, réutiliser les widgets existants.
- Adapter les constructeurs des widgets si besoin pour accepter le metaManager.
- Respecter la robustesse et la logique validée des scripts d’origine.
- Ne pas importer les QMainWindow ou méthodes de création d’onglets des scripts d’origine.
- L’UI globale doit être claire, modulaire, et facilement maintenable.

=============================================================
FIN DE LA SYNTHESE COMPLETE
=============================================================
