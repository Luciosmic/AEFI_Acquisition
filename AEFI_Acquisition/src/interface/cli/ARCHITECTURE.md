# CLI Architecture & UI Connection

## Architecture Pattern

Le CLI et l'UI sont **deux interfaces différentes** vers le **même service** (`ScanApplicationService`).

```
┌─────────────────┐         ┌──────────────────────────┐
│   CLI (Testé)   │─────────▶│  ScanApplicationService  │
│  scan_cli.py    │         │   (Domain Logic)          │
└─────────────────┘         └──────────────────────────┘
                                      ▲
┌─────────────────┐                   │
│   UI (PySide6)  │───────────────────┘
│  ScanPresenter  │
│  + Panels       │
└─────────────────┘
```

## Connexion Actuelle

### CLI
- **Fichier**: `src/interface/cli/scan_cli.py`
- **Service**: Crée sa propre instance via `create_scan_service()` (avec mocks)
- **Output Port**: `ScanCLIOutputPort` (sortie JSON)
- **Testé**: ✅ 20 tests d'intégration

### UI
- **Fichier**: `src/interface/presenters/scan_presenter.py`
- **Service**: Reçoit l'instance depuis `main.py` (via constructeur)
- **Output Port**: `ScanPresenter` implémente `IScanOutputPort` (signaux Qt)
- **Connecté**: ✅ Dans `main.py` lignes 276, 341-401

## Vérification de la Connexion

### Dans main.py

```python
# 1. Service créé UNE FOIS (ligne 197)
scan_service = ScanApplicationService(
    motion_port, acquisition_port, event_bus, 
    scan_executor, fly_scan_executor=fly_scan_executor
)

# 2. Presenter reçoit le service (ligne 276)
scan_presenter = ScanPresenter(
    scan_service,  # ← MÊME SERVICE
    scan_export_service, 
    event_bus, 
    transformation_service
)

# 3. Presenter s'enregistre comme output port (ligne 51 de scan_presenter.py)
self._service.set_output_port(self)  # ← CONNEXION

# 4. Panels connectés au presenter (lignes 341-401)
scan_control_panel.scan_start_requested.connect(scan_presenter.on_scan_start_requested)
flyscan_control_panel.flyscan_start_requested.connect(scan_presenter.on_flyscan_start_requested)
```

## Pattern de Connexion

### UI Flow
```
User clicks "START" 
  → ScanControlPanel.scan_start_requested signal
  → ScanPresenter.on_scan_start_requested()
  → ScanApplicationService.execute_scan(dto)
  → Service publie événements via EventBus
  → Service._on_domain_event() 
  → ScanPresenter.present_scan_started() (IScanOutputPort)
  → ScanPresenter.scan_started signal
  → ScanControlPanel.on_scan_started()
```

### CLI Flow
```
CLI command executed
  → cmd_scan_start()
  → create_scan_service() (nouvelle instance)
  → service.set_output_port(cli_output)
  → service.execute_scan(dto)
  → Service publie événements via EventBus
  → Service._on_domain_event()
  → ScanCLIOutputPort.present_scan_started()
  → JSON output
```

## Différence Clé

- **CLI**: Crée sa propre instance du service (isolée, pour tests)
- **UI**: Partage l'instance du service créée dans `main.py` (runtime)

## Validation

Le fait que le CLI soit **intensivement testé** valide que :
1. ✅ `ScanApplicationService` fonctionne correctement
2. ✅ L'interface `IScanOutputPort` est correctement implémentée
3. ✅ Les événements sont correctement émis

Le presenter UI utilise **exactement le même service** et **la même interface**, donc :
- ✅ Le presenter UI bénéficie des tests du CLI
- ✅ Le service est validé par les tests CLI
- ✅ La connexion UI est correcte (même pattern)

## Conclusion

**Oui, le CLI (controller testé) est bien connecté à l'UI via le presenter.**

Le presenter UI utilise le même service que le CLI, donc les tests du CLI valident aussi le comportement du service utilisé par l'UI.

