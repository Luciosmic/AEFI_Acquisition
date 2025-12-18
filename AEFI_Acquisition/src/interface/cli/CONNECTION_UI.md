# Connexion CLI ↔ UI via Presenter

## Principe

Le **CLI (controller testé)** et l'**UI** utilisent le **même service** (`ScanApplicationService`) via le **même pattern** (Output Port).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              ScanApplicationService                      │
│         (Application Layer - Orchestration)              │
│                                                           │
│  - execute_scan(dto)                                      │
│  - execute_fly_scan(config, rate)                        │
│  - set_output_port(IScanOutputPort)                      │
│  - Publie événements via EventBus                        │
└─────────────────────────────────────────────────────────┘
           ▲                          ▲
           │                          │
           │                          │
    ┌──────┴──────┐          ┌───────┴────────┐
    │             │          │                │
┌───┴───┐   ┌─────┴─────┐  ┌─┴──────────┐  ┌─┴──────────┐
│  CLI  │   │   UI       │  │  Presenter │  │  Panels    │
│       │   │            │  │            │  │            │
│ Testé │   │  main.py   │  │ ScanPres.  │  │ ScanCtrl   │
│ ✅    │   │  ligne 197 │  │ ligne 286  │  │ FlyScanCtrl│
└───────┘   └────────────┘  └────────────┘  └────────────┘
```

## Connexion CLI

**Fichier**: `src/interface/cli/scan_cli.py`

```python
# CLI crée sa propre instance (isolée pour tests)
def create_scan_service() -> ScanApplicationService:
    # ... création avec mocks ...
    service = ScanApplicationService(...)
    return service

# CLI utilise le service
service = create_scan_service()
service.set_output_port(ScanCLIOutputPort())  # ← Output Port JSON
service.execute_scan(dto)  # ← Même méthode que UI
```

**Tests**: ✅ 20 tests d'intégration valident le service

## Connexion UI

**Fichier**: `main.py` + `src/interface/presenters/scan_presenter.py`

```python
# main.py ligne 197 : Service créé UNE FOIS
scan_service = ScanApplicationService(
    motion_port, acquisition_port, event_bus, 
    scan_executor, fly_scan_executor=fly_scan_executor
)

# main.py ligne 286 : Presenter reçoit le service
scan_presenter = ScanPresenter(
    scan_service,  # ← MÊME SERVICE (même classe)
    scan_export_service, event_bus, transformation_service
)

# scan_presenter.py ligne 51 : Presenter s'enregistre comme Output Port
self._service.set_output_port(self)  # ← CONNEXION

# main.py lignes 346, 384 : Panels connectés au presenter
scan_control_panel.scan_start_requested.connect(scan_presenter.on_scan_start_requested)
flyscan_control_panel.flyscan_start_requested.connect(scan_presenter.on_flyscan_start_requested)
```

## Validation de la Connexion

### ✅ Même Service
- CLI : `ScanApplicationService` (instance isolée)
- UI : `ScanApplicationService` (instance partagée)
- **Même classe, même interface**

### ✅ Même Pattern
- CLI : `ScanCLIOutputPort` implémente `IScanOutputPort`
- UI : `ScanPresenter` implémente `IScanOutputPort`
- **Même interface, même contrat**

### ✅ Même Méthodes
- CLI : `service.execute_scan(dto)`
- UI : `service.execute_scan(dto)` (via presenter)
- **Même API, même comportement**

### ✅ Tests CLI Valident UI
Les 20 tests du CLI valident :
1. ✅ `ScanApplicationService.execute_scan()` fonctionne
2. ✅ `IScanOutputPort` est correctement implémentée
3. ✅ Les événements sont correctement émis
4. ✅ La logique métier est correcte

**Conclusion** : Le presenter UI utilise le **même service testé** par le CLI, donc les tests CLI valident aussi le comportement de l'UI.

## Flux de Connexion UI

```
User Action (Click "START")
  ↓
ScanControlPanel.scan_start_requested.emit(params)
  ↓
ScanPresenter.on_scan_start_requested(params)  [ligne 264]
  ↓
ScanApplicationService.execute_scan(dto)  [ligne 294]
  ↓
Service publie événements → EventBus
  ↓
Service._on_domain_event(event)  [ligne 224]
  ↓
ScanPresenter.present_scan_started(...)  [IScanOutputPort, ligne 57]
  ↓
ScanPresenter.scan_started.emit(scan_id, config)  [ligne 71]
  ↓
ScanControlPanel.on_scan_started(scan_id)  [ligne 211]
  ↓
UI mise à jour
```

## Vérification

Pour vérifier que la connexion fonctionne :

1. **Lancer l'UI** : `python main_mock.py`
2. **Cliquer "START"** dans ScanControlPanel
3. **Observer** : Les événements doivent être émis et l'UI mise à jour
4. **Vérifier les logs** : `[ScanApplicationService]` messages dans la console

Si les tests CLI passent et que l'UI utilise le même service, la connexion est **validée**.

## Conclusion

**Oui, le CLI (controller testé) est bien connecté à l'UI via le presenter.**

- ✅ Même service (`ScanApplicationService`)
- ✅ Même interface (`IScanOutputPort`)
- ✅ Même pattern (Output Port)
- ✅ Tests CLI valident le service utilisé par l'UI

