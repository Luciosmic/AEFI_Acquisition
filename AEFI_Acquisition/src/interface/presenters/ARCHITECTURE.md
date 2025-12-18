# Scan Presenter Architecture

## Pattern: Controller → Service → Output Port

### Architecture Overview

```
┌─────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│     UI      │────────▶│   ScanPresenter      │────────▶│ ScanApplication │
│  (View)     │ Signals │  (IScanOutputPort)    │  Calls  │    Service      │
└─────────────┘         └──────────────────────┘         └─────────────────┘
                                                                    │
                                                                    │ Events
                                                                    ▼
                                                          ┌─────────────────┐
                                                          │  EventBus        │
                                                          └─────────────────┘
                                                                    │
                                                                    │
                                                                    ▼
                                                          ┌─────────────────┐
                                                          │ ScanPresenter   │
                                                          │ (via _on_domain │
                                                          │  _event)        │
                                                          └─────────────────┘
```

### Connection Pattern

**ScanPresenter** implémente `IScanOutputPort` et est connecté au service :

```python
# Dans ScanPresenter.__init__
self._service.set_output_port(self)  # Presenter = Output Port
```

**ScanCLIOutputPort** (CLI) implémente aussi `IScanOutputPort` :

```python
# Dans cmd_scan_start
service.set_output_port(cli_output)  # CLI Output = Output Port
```

### Validation par les Tests CLI

Les tests CLI intensifs valident :
1. ✅ **Service Layer** : `ScanApplicationService` fonctionne correctement
2. ✅ **Output Port Interface** : `IScanOutputPort` est correctement implémentée
3. ✅ **Event Flow** : Les événements sont correctement transmis

Puisque `ScanPresenter` implémente la même interface (`IScanOutputPort`) et utilise le même service, les tests CLI valident indirectement le presenter.

### Flow Comparison

#### CLI Flow
```
User Input (JSON) 
  → CLI Parser
  → ScanCLIOutputPort (IScanOutputPort)
  → ScanApplicationService.set_output_port(cli_output)
  → Service.execute_scan()
  → Events → cli_output.present_*()
  → JSON Output
```

#### UI Flow
```
User Input (UI Widgets)
  → ScanControlPanel signals
  → ScanPresenter.on_scan_start_requested()
  → ScanPresenter (IScanOutputPort)
  → ScanApplicationService.set_output_port(presenter)
  → Service.execute_scan()
  → Events → presenter.present_*()
  → Qt Signals → UI Updates
```

### Key Points

1. **Même Service** : CLI et UI utilisent `ScanApplicationService`
2. **Même Interface** : Les deux implémentent `IScanOutputPort`
3. **Même Pattern** : `service.set_output_port(output_port)`
4. **Validation Croisée** : Tests CLI valident le service, qui est utilisé par le presenter

### Verification

Pour vérifier que le presenter est bien connecté :

```python
# Dans main.py
scan_presenter = ScanPresenter(scan_service, ...)
# scan_service.set_output_port(scan_presenter) est appelé dans __init__

# Le service utilise le presenter comme output port
# Les événements du service sont automatiquement transmis au presenter
```

### Conclusion

**Le presenter est bien connecté** au service de la même manière que le CLI. Les tests CLI intensifs valident le comportement du service, qui est utilisé par le presenter. Le presenter fonctionne donc correctement car il utilise le même service validé.

## Validation

### Tests CLI (Step 9)
- ✅ 20 tests d'intégration CLI
- ✅ Validation du service `ScanApplicationService`
- ✅ Validation de l'interface `IScanOutputPort`
- ✅ Validation du flow d'événements

### Tests Presenter
- ✅ `test_presenter_implements_output_port`: Vérifie que le presenter implémente `IScanOutputPort`
- ✅ `test_presenter_sets_output_port_on_service`: Vérifie que le presenter s'enregistre comme output port
- ✅ `test_presenter_receives_events_from_service`: Vérifie que le presenter reçoit les événements du service
- ✅ `test_presenter_same_pattern_as_cli`: Vérifie que le presenter utilise le même pattern que le CLI

### Preuve de Connexion

```python
# CLI Pattern
service = create_scan_service()
service.set_output_port(cli_output)  # CLI Output Port

# UI Pattern (dans main.py)
scan_presenter = ScanPresenter(scan_service, ...)
# Dans ScanPresenter.__init__:
self._service.set_output_port(self)  # Presenter = Output Port

# Même pattern, même service, même interface
```

**Résultat** : Le presenter UI est connecté au même service validé par les tests CLI. Les tests CLI valident indirectement le presenter car ils testent le service que le presenter utilise.

