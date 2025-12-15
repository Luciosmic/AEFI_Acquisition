# Tâches d'implémentation du Double Buffer pour l'export CSV

## Contexte
L'objectif est d'implémenter un système de double buffer dans les modules d'export CSV pour améliorer les performances d'écriture sur disque sans bloquer l'acquisition. Cette optimisation sera activée uniquement en mode export, tandis que le mode exploration conservera la logique actuelle.

Cette implémentation doit être réalisée pour les deux sous-managers:
1. **AcquisitionManager** (données des capteurs via `AD9106_ADS131A04_CSVexporter_Module.py`)
2. **StageManager** (données de position via `ArcusPerfomax4EXStage_CSVexporter_Module.py`)

## Tâches à réaliser

### Phase 1: Modification du module pour le StageManager

#### 1. Modifier la classe CSVSensorExporter dans ArcusPerfomax4EXStage_CSVexporter_Module.py
- [ ] Ajouter les attributs de double buffer dans `__init__()`
  ```python
  self._buffer_A = []  # Premier buffer d'accumulation
  self._buffer_B = []  # Second buffer d'accumulation
  self._active_buffer = "A"  # Buffer actif (A ou B)
  self._writing_buffer = None  # Buffer en cours d'écriture
  self._buffer_lock = Lock()  # Verrou pour l'échange de buffers
  ```

#### 2. Créer une méthode d'initialisation du système de double buffer
- [ ] Implémenter `_init_double_buffer_system()`
  ```python
  def _init_double_buffer_system(self):
      self._buffer_A = []
      self._buffer_B = []
      self._active_buffer = "A"
      self._writing_buffer = None
  ```

#### 3. Modifier la méthode d'ajout d'échantillons
- [ ] Adapter `add_sample()` pour utiliser le double buffer en mode export
  ```python
  # Déterminer le buffer cible
  # Ajouter l'échantillon au buffer actif
  # Vérifier si le buffer est plein et déclencher l'échange si nécessaire
  ```

#### 4. Implémenter la méthode d'échange de buffers
- [ ] Créer `_exchange_buffers()`
  ```python
  # Vérifier qu'aucun buffer n'est en cours d'écriture
  # Échanger les rôles des buffers
  # Déclencher l'écriture dans un thread séparé
  ```

#### 5. Adapter le worker d'export
- [ ] Modifier `_export_worker()` pour traiter un buffer complet
  ```python
  # Traiter les cas d'arrêt et de fin d'export
  # Utiliser la nouvelle logique de double buffer
  ```

#### 6. Modifier la méthode d'écriture au format LabVIEW
- [ ] Adapter `_write_labview_format()` pour traiter les données du buffer actif
  ```python
  # Extraire les données du buffer à écrire
  # Réorganiser au format LabVIEW
  # Écrire sur disque
  ```

#### 7. Adapter la classe CSVPositionExporter
- [ ] Appliquer les mêmes modifications à CSVPositionExporter
  ```python
  # Dupliquer les modifications avec les adaptations nécessaires
  ```

### Phase 2: Modification du module pour l'AcquisitionManager

#### 8. Adapter la classe CSVExporter dans AD9106_ADS131A04_CSVexporter_Module.py
- [ ] Ajouter le paramètre `dataFormat_Labview` à la classe ExportConfig
  ```python
  @dataclass
  class ExportConfig:
      # Champs existants
      dataFormat_Labview: bool = False
  ```
- [ ] Ajouter les attributs de double buffer dans `__init__()`
- [ ] Implémenter la méthode `_init_double_buffer_system()`
- [ ] Adapter la méthode `add_sample()` pour utiliser le double buffer
- [ ] Créer la méthode `_exchange_buffers()`
- [ ] Adapter `_export_worker()` pour la logique de double buffer
- [ ] Implémenter `_write_labview_format()` si nécessaire

### Phase 3: Coordination et intégration

#### 9. Modifier le MetaManager pour coordonner les exporteurs
- [ ] Ajouter le paramètre `dataFormat_Labview` à la méthode `start_export_csv()`
  ```python
  def start_export_csv(self, config=None):
      if config is None:
          config = ExportConfig(
              metadata={**self.get_acquisition_config(), **self.get_stage_config()},
              dataFormat_Labview=False  # Par défaut
          )
      # Reste du code inchangé
  ```
- [ ] S'assurer que le paramètre est correctement propagé aux sous-managers

#### 10. Ajouter des mécanismes de gestion d'erreurs
- [ ] Implémenter des try/except robustes dans les deux modules
- [ ] Ajouter des timeouts pour éviter les blocages
- [ ] Prévoir des mécanismes de récupération en cas d'erreur d'écriture
- [ ] Gérer les cas d'arrêt forcé pendant l'écriture

### Phase 4: Tests et validation

#### 11. Tester le module ArcusPerfomax4EXStage_CSVexporter_Module.py
- [ ] Créer des tests unitaires pour le double buffer
- [ ] Tester les performances avec différentes tailles de buffer
- [ ] Valider la rétrocompatibilité du format LabVIEW

#### 12. Tester le module AD9106_ADS131A04_CSVexporter_Module.py
- [ ] Créer des tests unitaires spécifiques
- [ ] Tester les performances sous charge
- [ ] Vérifier la compatibilité avec le système existant

#### 13. Tests d'intégration
- [ ] Tester l'interaction entre les deux modules d'export
- [ ] Vérifier la synchronisation des exports
- [ ] Tester les performances globales du système

## Principes directeurs
- Minimiser les modifications au code existant
- Localiser les changements aux modules d'export CSV
- Ne pas modifier l'API publique
- Éviter d'ajouter du "bruit" inutile au code
- Assurer une transition transparente entre les modes
- Maintenir la cohérence entre les implémentations des deux sous-managers
