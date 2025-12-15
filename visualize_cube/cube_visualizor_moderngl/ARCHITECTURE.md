# Cube Visualizer - Architecture Documentation

## Vue d'Ensemble

Le visualiseur de cube utilise une architecture **CQRS (Command Query Responsibility Segregation)** avec le pattern **MVP (Model-View-Presenter)** pour séparer clairement les responsabilités.

## Diagrammes

### 1. [Architecture Overview](architecture_overview.puml)
Vue d'ensemble montrant le flux CQRS :
- **Commands** (Write) : Modifications d'état via `CommandBus`
- **Events** (Read) : Notifications via `EventBus` (thread-safe avec Qt Signals)
- **Queries** (Read) : Accès en lecture seule à l'état

### 2. [Class Diagram](architecture_class_diagram.puml)
Diagramme de classes détaillé montrant :
- Infrastructure CQRS (`CommandBus`, `EventBus`)
- Modèle de domaine (`SensorOrientation`)
- Couches Presenter, View, et Adapter

### 3. [Sequence Diagram - Update Angles](sequence_update_angles.puml)
Flux complet d'une mise à jour d'angle :
1. User modifie un `QDoubleSpinBox`
2. UI envoie une `UpdateAnglesCommand` via `CommandBus`
3. Presenter modifie `SensorOrientation`
4. Presenter publie un événement `ANGLES_CHANGED` via `EventBus`
5. UI et Adapter reçoivent l'événement et se mettent à jour

## Principes Architecturaux

### CQRS (Command Query Responsibility Segregation)

#### Commands (Write)
- **Responsabilité** : Modifier l'état du système
- **Caractéristiques** :
  - Pas de valeur de retour
  - Asynchrones
  - Passent par le `CommandBus`
- **Exemples** :
  - `UpdateAnglesCommand(theta_x, theta_y, theta_z)`
  - `ResetToDefaultCommand()`

#### Events (Read)
- **Responsabilité** : Notifier les changements d'état
- **Caractéristiques** :
  - Pub/Sub pattern
  - Thread-safe (Qt Signals)
  - Passent par l'`EventBus`
- **Exemples** :
  - `ANGLES_CHANGED` : Angles modifiés
  - `CAMERA_VIEW_CHANGED` : Vue caméra changée

#### Queries (Read)
- **Responsabilité** : Lire l'état sans le modifier
- **Caractéristiques** :
  - Pas de side-effects
  - Synchrones
  - Appels directs au Presenter
- **Exemples** :
  - `presenter.get_rotation()` : Obtenir la rotation actuelle
  - `presenter.get_angles()` : Obtenir les angles actuels

### MVP (Model-View-Presenter)

#### Model
- **`SensorOrientation`** : Value Object contenant `theta_x`, `theta_y`, `theta_z`
- **Single Source of Truth** : Géré par le Presenter

#### View
- **`CubeSensorUI`** : Interface Qt (QMainWindow avec QtAds)
- **Responsabilités** :
  - Afficher les contrôles (spinboxes, boutons)
  - Envoyer des commandes via `CommandBus`
  - S'abonner aux événements via `EventBus`
  - **Passive View** : Pas de logique métier

#### Presenter
- **`CubeVisualizerPresenter`** : Logique métier
- **Responsabilités** :
  - Recevoir les commandes via `CommandBus`
  - Modifier `SensorOrientation`
  - Publier les événements via `EventBus`
  - Fournir des queries (read-only)

#### Adapter
- **`CubeVisualizerAdapter`** : Intégration PyVista
- **Responsabilités** :
  - S'abonner aux événements via `EventBus`
  - Interroger le Presenter (queries)
  - Gérer le rendu PyVista (`QtInteractor`)

## Thread Safety

### EventBus (Qt Signals)
- Utilise `QObject` et `Signal` de PySide6
- `event_published.connect(..., Qt.QueuedConnection)`
- **Garantit** l'exécution sur le thread principal Qt

### Adapter Updates
- `QTimer.singleShot(0, lambda: self.update_view())`
- Force l'exécution sur le thread principal

## Flux de Données

```
User Input (UI)
    ↓
CommandBus.send(Command)
    ↓
Presenter._handle_command()
    ↓
Presenter._update_state()
    ↓
EventBus.publish(Event)
    ↓
┌─────────────────┬─────────────────┐
↓                 ↓                 ↓
UI.update()   Adapter.update()   (autres subscribers)
```

## Avantages de cette Architecture

1. **Séparation des Responsabilités** : Chaque composant a un rôle clair
2. **Thread Safety** : EventBus garantit l'exécution sur le thread principal
3. **Testabilité** : Logique métier isolée dans le Presenter
4. **Extensibilité** : Facile d'ajouter de nouveaux subscribers
5. **Découplage** : UI, Presenter, et Adapter sont indépendants

## Dépendances

- **PySide6** : Framework Qt pour l'UI
- **PySide6-QtAds** : Dock widgets avancés
- **PyVista** : Visualisation 3D
- **pyvistaqt** : Intégration PyVista/Qt
- **scipy** : Rotations 3D (`scipy.spatial.transform.Rotation`)

## Fichiers Principaux

- `main.py` : Point d'entrée, création de `CubeSensorUI`
- `cube_visualizer_presenter.py` : Logique métier (CQRS)
- `cube_visualizer_adapter_pyvista.py` : Intégration PyVista
- `command_bus.py` : Infrastructure CQRS (Commands)
- `event_bus.py` : Infrastructure CQRS (Events)
- `cube_geometry.py` : Géométrie du cube et rotations
