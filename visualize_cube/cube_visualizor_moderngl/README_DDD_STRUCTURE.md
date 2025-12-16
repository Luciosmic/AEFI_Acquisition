# Structure DDD - Cube Visualizer

## Organisation des Couches

Le projet est organisé selon les principes de **Domain-Driven Design (DDD)** avec séparation claire des responsabilités :

```
cube_visualizor_moderngl/
├── domain/                    # Couche Domain (logique métier pure)
│   ├── value_objects/        # Objets valeur immutables
│   │   └── sensor_orientation.py
│   └── services/             # Services de domaine
│       └── geometry_service.py
│
├── application/               # Couche Application (use cases, services)
│   ├── commands/             # Commandes CQRS
│   │   ├── update_angles_command.py
│   │   ├── reset_to_default_command.py
│   │   └── reset_camera_view_command.py
│   └── services/             # Services d'application
│       └── cube_visualizer_service.py
│
├── infrastructure/            # Couche Infrastructure (implémentations techniques)
│   ├── messaging/            # Messaging CQRS
│   │   ├── command_bus.py
│   │   └── event_bus.py
│   └── rendering/            # Adapters de rendu
│       └── cube_visualizer_adapter_modern_gl.py
│
└── interface/                 # Couche Interface (UI, présentation)
    ├── main.py               # Point d'entrée principal
    └── views/                # Vues UI
        └── cube_visualizer_view.py
```

## Principes DDD

### Domain Layer
- **Aucune dépendance** sur les autres couches
- Logique métier pure (géométrie, rotations)
- Value objects immutables (`SensorOrientation`)
- Services de domaine sans side-effects

### Application Layer
- **Dépend uniquement** de Domain
- Services d'application (orchestration)
- Commandes CQRS (modifications d'état)
- Utilise Domain pour la logique métier

### Infrastructure Layer
- **Dépend** de Domain et Application
- Implémentations techniques (rendering, messaging)
- Adapters pour les frameworks externes (ModernGL, Qt)
- CommandBus et EventBus pour CQRS

### Interface Layer
- **Dépend** de toutes les autres couches
- UI (Qt widgets)
- Point d'entrée de l'application
- Orchestration des composants

## Flux CQRS

1. **Command** : UI → CommandBus → Service
2. **Event** : Service → EventBus → Adapter/UI
3. **Query** : Adapter → Service (lecture seule)

## Utilisation

```python
from interface.main import main

if __name__ == "__main__":
    main()
```

## Avantages de cette Structure

- ✅ **Séparation claire** des responsabilités
- ✅ **Testabilité** : Domain peut être testé sans infrastructure
- ✅ **Maintenabilité** : Chaque couche a un rôle précis
- ✅ **Évolutivité** : Facile d'ajouter de nouveaux adapters (PyVista, etc.)
- ✅ **CQRS** : Séparation Commands/Events/Queries



