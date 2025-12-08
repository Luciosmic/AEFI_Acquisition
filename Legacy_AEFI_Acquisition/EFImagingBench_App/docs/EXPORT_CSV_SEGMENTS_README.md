# Système d'Export CSV avec Identification de Segments

## Vue d'ensemble

Le système d'export CSV a été enrichi pour identifier et marquer automatiquement les segments du scan 2D, permettant de distinguer les lignes de scan actives des mouvements de transition.

## Fonctionnalités principales

### 1. **Génération de trajectoire segmentée**
- Le module `Scan2DConfigurator` génère une trajectoire complète avec identification des segments
- Chaque segment est marqué comme :
  - `scan_line` : Ligne de scan active (données utiles)
  - `transition` : Mouvement de transition entre lignes

### 2. **Signal de changement de segment**
- Le `StageManager` émet un signal `scan_segment_changed(segment_id, segment_type, is_active_line)`
- Ce signal est émis à chaque changement de segment pendant le scan

### 3. **Export CSV enrichi**
- Chaque échantillon exporté contient :
  - `segment_id` : Identifiant unique du segment (ex: "scan_line_5")
  - `is_active_line` : 1 si ligne active, 0 si transition
- Option de filtrage : "Exporter uniquement lignes actives"

### 4. **Arrêt automatique**
- L'export s'arrête automatiquement à la fin du scan
- Signal `scan2d_finished` déclenche l'arrêt de l'export

## Utilisation

### Dans l'interface graphique

1. Configurer le scan 2D (positions, nombre de lignes, mode E/S)
2. Cocher "Exporter uniquement lignes actives" si désiré
3. Vérifier le chemin d'export
4. Cliquer "Exécuter le scan"
5. L'export démarre et s'arrête automatiquement

### Format des fichiers CSV

**Fichier capteur** (`YYMMDD_HHMMSS_Default_E_all.csv`) :
```csv
# Metadata
# freq_hz,1000
# gain_dds,500
...
index,timestamp_rel,segment_id,is_active_line,ADC1_Ch1 Ex_real,ADC1_Ch2 Ex_imag,...
0,0.000001,scan_line_0,1,1.234,2.345,...
1,0.001002,scan_line_0,1,1.235,2.346,...
...
150,0.150001,transition_1,0,1.240,2.350,...
```

**Fichier position** (`YYMMDD_HHMMSS_Default_Position_all.csv`) :
```csv
# Metadata
# scan_mode,E
# N_lines,10
...
index,timestamp_rel,segment_id,is_active_line,x,y
0,0.000001,scan_line_0,1,0.0,0.0
1,0.001002,scan_line_0,1,0.0,0.5
...
```

## Avantages

1. **Traçabilité complète** : Chaque point de donnée est associé à son contexte
2. **Filtrage flexible** : Possibilité de filtrer en temps réel ou en post-traitement
3. **Performance** : Pas d'impact sur la vitesse d'acquisition
4. **Pas d'interpolation** : Les données restent dans leur domaine temporel natif

## Post-traitement

Pour filtrer les données après coup (Python) :
```python
import pandas as pd

# Charger les données
df_sensor = pd.read_csv('fichier_E_all.csv', comment='#')
df_position = pd.read_csv('fichier_Position_all.csv', comment='#')

# Filtrer uniquement les lignes actives
df_sensor_active = df_sensor[df_sensor['is_active_line'] == 1]
df_position_active = df_position[df_position['is_active_line'] == 1]

# Grouper par segment
for segment_id, group in df_sensor_active.groupby('segment_id'):
    print(f"Segment {segment_id}: {len(group)} échantillons")
```

## Architecture technique

```
Scan2DConfigurator
    ↓ génère trajectoire segmentée
StageManager
    ↓ émet scan_segment_changed
MetaManager
    ↓ propage le signal
CSVExporter
    ↓ marque les échantillons
Fichiers CSV (avec segment_id et is_active_line)
```

## Configuration

- **Mode E** : Toutes les lignes dans le même sens (retour rapide)
- **Mode S** : Lignes en serpent (pas de retour, plus efficace)
- **filter_active_lines_only** : Si True, seules les données des lignes actives sont enregistrées 