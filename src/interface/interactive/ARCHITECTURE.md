# Interactive Port Architecture

## Principe

**L'interactive_port s'intègre avec EventBus et CommandBus, ne les remplace pas.**

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              CompositeController                        │
│  (Agrège tous les controllers)                         │
│                                                          │
│  - register_controller(ScanController)                  │
│  - register_controller(MotionController)               │
│  - handle_command("scan_start", {...})                  │
└─────────────────────────────────────────────────────────┘
                    ▲
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────┴────────┐    ┌────────┴────────┐
│ ScanController │    │ MotionController│
│                 │    │                  │
│ - handle_command│    │ - handle_command │
│ - subscribe     │    │ - subscribe     │
│ - publish       │    │ - publish       │
└────────────────┘    └─────────────────┘
        │                       │
        │                       │
        ▼                       ▼
┌─────────────────────────────────────────┐
│           EventBus                      │
│  (Domain Events)                        │
│                                         │
│  - scanstarted                          │
│  - scanpointacquired                    │
│  - motionstarted                        │
└─────────────────────────────────────────┘
        ▲                       ▲
        │                       │
┌───────┴────────┐    ┌────────┴────────┐
│ ScanService    │    │ MotionService   │
│ (publie)       │    │ (publie)        │
└────────────────┘    └─────────────────┘
```

## Pattern EventBus

### Controllers s'abonnent aux événements

```python
# Dans ScanController.initialize()
event_bus.subscribe("scanstarted", self._on_scan_started)
event_bus.subscribe("scanpointacquired", self._on_scan_point_acquired)
```

### Services publient des événements

```python
# Dans ScanApplicationService
self._event_bus.publish("scanstarted", scan_started_event)
```

### Controllers réagissent aux événements

```python
def _on_scan_started(self, event: ScanStarted) -> None:
    # Forward to output port
    self._output_port.present_scan_started(...)
```

## Pattern CommandBus (Futur)

### Controllers reçoivent des commandes

```python
# Via CompositeController
composite.handle_command("scan_start", {
    "x_min": 0.0,
    "x_max": 10.0,
    ...
})
```

### Controllers exécutent via services

```python
def handle_command(self, command_type: str, command_data: Dict[str, Any]) -> None:
    if command_type == "scan_start":
        dto = Scan2DConfigDTO(**command_data)
        self._scan_service.execute_scan(dto)
```

## Interface Segregation Principle (ISP)

### Interfaces séparées

1. **IInteractivePort** : Base (initialize, shutdown, get_controller_name)
2. **ICommandHandler** : Gestion des commandes (handle_command)
3. **IEventPublisher** : Publication d'événements (publish_event)

### Controllers implémentent seulement ce dont ils ont besoin

```python
class ScanController(IInteractivePort, ICommandHandler, IEventPublisher):
    # Implémente les 3 interfaces
    pass

class ReadOnlyController(IInteractivePort, IEventPublisher):
    # N'implémente pas ICommandHandler (lecture seule)
    pass
```

## Intégration avec Services

### Controllers utilisent les services

```python
class ScanController:
    def __init__(self, scan_service: ScanApplicationService, ...):
        self._scan_service = scan_service
```

### Services utilisent EventBus

```python
class ScanApplicationService:
    def __init__(self, ..., event_bus: IDomainEventBus):
        self._event_bus = event_bus
        # Publie des événements
        self._event_bus.publish("scanstarted", event)
```

## Flux Complet

### 1. Initialisation

```python
# Créer composite
composite = CompositeController()

# Enregistrer controllers
scan_controller = ScanController(scan_service, output_port)
composite.register_controller(scan_controller)

# Initialiser avec EventBus
composite.initialize(event_bus)
```

### 2. Commande Utilisateur

```python
# User action → Command
composite.handle_command("scan_start", {
    "x_min": 0.0,
    "x_max": 10.0,
    ...
})

# → ScanController.handle_command()
# → ScanService.execute_scan()
# → Service publie événements via EventBus
```

### 3. Réaction aux Événements

```python
# EventBus publie "scanstarted"
# → ScanController._on_scan_started() (abonné)
# → OutputPort.present_scan_started()
# → UI mise à jour
```

## Avantages

1. **Découplage** : Controllers indépendants des services
2. **ISP** : Interfaces petites et spécifiques
3. **EventBus** : Communication asynchrone via événements
4. **CommandBus** : Routage unifié des commandes
5. **Composabilité** : CompositeController agrège facilement

## Exemple d'Utilisation

```python
from interface.interactive.composite_controller import CompositeController
from interface.interactive.controllers.scan_controller import ScanController
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

# Setup
event_bus = InMemoryEventBus()
scan_service = ScanApplicationService(...)
output_port = ScanCLIOutputPort()

# Create controllers
scan_controller = ScanController(scan_service, output_port)

# Create composite
composite = CompositeController()
composite.register_controller(scan_controller)
composite.initialize(event_bus)

# Use
composite.handle_command("scan_start", {
    "x_min": 0.0,
    "x_max": 10.0,
    "y_min": 0.0,
    "y_max": 10.0,
    "x_nb_points": 3,
    "y_nb_points": 3
})

# Cleanup
composite.shutdown()
```

