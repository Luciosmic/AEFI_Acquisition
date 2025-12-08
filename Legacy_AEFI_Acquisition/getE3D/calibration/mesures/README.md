# README - Fichiers de mesures de calibration

Les fichiers CSV générés dans ce dossier contiennent les résultats des mesures de phase et d'amplitude lors des campagnes de calibration DDS.

## Colonnes typiques
- `frequence_Hz` : fréquence DDS testée (Hz)
- `phase_deg` : déphasage mesuré entre CH3 et CH4 (degrés)
- `VPP_CH3` : amplitude crête à crête sur CH3 (V)
- `VPP_CH4` : amplitude crête à crête sur CH4 (V)
- `diff_amp_V` : différence d'amplitude absolue (V)
- `timestamp` : date et heure de la mesure

## Utilisation
- Les fichiers sont au format CSV, lisibles avec Excel, pandas, etc.
- Une ligne par mesure/fréquence.
- Les scripts ajoutent automatiquement les nouvelles mesures à la suite. 