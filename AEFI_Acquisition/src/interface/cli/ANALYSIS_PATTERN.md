# Analyse : Respect du Pattern Presenter

## Problème Identifié

### État Actuel

1. **Service** passe des données brutes aux presenters :
   ```python
   present_scan_started(scan_id, {"pattern": ..., "x_min": ..., ...})
   ```

2. **CLI Presenter** transforme en structure JSON standardisée :
   ```python
   {
     "event": "scan_started",
     "scan_id": scan_id,
     "config": {...},
     "timestamp": ...
   }
   ```

3. **UI Presenter** reçoit directement les données brutes et les utilise :
   ```python
   # Reçoit {"pattern": ..., "x_min": ..., ...}
   # Utilise directement sans structure CLI
   ```

### Problème

Le UI presenter ne suit **pas** la structure CLI. Il devrait recevoir la même structure que le CLI (`{"event": ..., "scan_id": ..., "config": ..., "timestamp": ...}`) et ensuite la transformer pour Qt.

## Solution : Refactoring

### Option 1 : Service passe structure CLI
Le service devrait passer la structure CLI standardisée à tous les presenters.

### Option 2 : Base Presenter
Créer une classe de base qui normalise les données en structure CLI, puis les presenters dérivent.

### Option 3 : CLI Presenter comme référence
Le CLI presenter définit la structure, et les autres presenters doivent recevoir la même structure.

## Recommandation

**Option 1** : Le service doit passer la structure CLI standardisée à tous les presenters. Le CLI presenter l'utilise directement, le UI presenter la transforme pour Qt.

