# Pattern Presenter : CLI JSON comme Base

## Philosophie

**Tous les presenters se basent sur le presenter de la CLI JSON.**

> **Principe** : Le développement des interfaces externes est complètement découplé du développement interne. La CLI JSON est actuellement le moyen le plus pratique avec les agents IA pour l'intégration complète.

### Principe Fondamental

```
┌─────────────────────────────────────────────────────────┐
│         CLI JSON Presenter (ScanCLIOutputPort)           │
│              = BASE / RÉFÉRENCE                          │
│                                                           │
│  - Format JSON standardisé                                │
│  - Intégration complète avec agents IA                   │
│  - Découplage complet interfaces externes / interne       │
│  - Structure événementielle claire                        │
└─────────────────────────────────────────────────────────┘
                    ▲
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────┴────────┐    ┌────────┴────────┐
│  UI Presenter  │    │  API Presenter  │
│  (PySide6)     │    │  (REST/GraphQL) │
│                 │    │                  │
│  S'appuie sur   │    │  S'appuie sur    │
│  structure CLI  │    │  structure CLI    │
│  (même format)  │    │  (même format)    │
└────────────────┘    └─────────────────┘
```

## Avantages

### 1. Découplage Complet
- **Interfaces externes** (UI, API) : Développement indépendant du développement interne
- **Développement interne** : Intégration complète via CLI JSON
- **Agents IA** : Utilisent CLI JSON comme interface standard (le plus pratique)

### 2. Intégration avec Agents IA
- CLI JSON = format le plus pratique pour les agents IA
- Parsing JSON standardisé et déterministe
- Structure événementielle claire (event, data, timestamp)
- Testable via subprocess (isolation complète)
- Intégration complète sans dépendances UI

### 3. Base de Référence
- Tous les presenters suivent la même structure que CLI
- Même interface `IScanOutputPort`
- Même séquence d'événements
- Même format de données (structure JSON CLI)

## Architecture Actuelle

### CLI Presenter (Base)
```python
class ScanCLIOutputPort(IScanOutputPort):
    """Base presenter - JSON output."""
    def present_scan_started(self, scan_id: str, config: Dict[str, Any]):
        self._output({
            "event": "scan_started",
            "scan_id": scan_id,
            "config": config,
            "timestamp": ...
        })
```

### UI Presenter (Dérivé)
```python
class ScanPresenter(QObject, IScanOutputPort):
    """UI presenter - s'appuie sur structure CLI."""
    def present_scan_started(self, scan_id: str, config: Dict[str, Any]):
        # Même structure que CLI
        # + Transformation pour UI (signaux Qt)
        self.scan_started.emit(scan_id, config)
```

## Pattern d'Implémentation

### Étape 1 : Développer CLI JSON
1. Implémenter `ScanCLIOutputPort`
2. Tester avec agents IA
3. Valider structure JSON

### Étape 2 : Développer Autres Presenters
1. Implémenter même interface `IScanOutputPort`
2. Réutiliser structure de données CLI
3. Ajouter transformation spécifique (UI, API, etc.)

### Étape 3 : Validation
1. CLI JSON = référence
2. Autres presenters = compatibles avec structure CLI
3. Tests d'intégration via CLI JSON

## Exemple : Scan Started Event

### CLI JSON (Base)
```json
{
  "event": "scan_started",
  "scan_id": "uuid-123",
  "config": {
    "x_min": 0.0,
    "x_max": 10.0,
    "x_nb_points": 3,
    "y_nb_points": 3,
    "scan_pattern": "SERPENTINE"
  },
  "timestamp": "2025-12-18T..."
}
```

### UI Presenter (Dérivé)
```python
# Même structure de données
# + Émission signal Qt
self.scan_started.emit(scan_id, config)
```

### API Presenter (Dérivé - futur)
```python
# Même structure de données
# + Transformation HTTP
return jsonify({
    "event": "scan_started",
    "scan_id": scan_id,
    "config": config,
    "timestamp": ...
})
```

## Intégration Agents IA

### Pourquoi CLI JSON ?

1. **Standardisé** : JSON est universel
2. **Parsable** : Facile à parser pour agents
3. **Événementiel** : Structure claire (event, data, timestamp)
4. **Testable** : Subprocess + validation JSON
5. **Déterministe** : Sortie prévisible

### Utilisation par Agents

```python
# Agent appelle CLI
result = subprocess.run(
    ["python", "scan_cli.py", "scan-start", "--config", "config.json"],
    capture_output=True,
    text=True
)

# Parse JSON
events = [json.loads(line) for line in result.stdout.splitlines()]

# Traitement événements
for event in events:
    if event["event"] == "scan_started":
        # Action basée sur structure CLI
        ...
```

## Règles de Conception

### ✅ À Faire
- **CLI JSON = première implémentation** (base de référence)
- Tous les presenters suivent même structure de données CLI
- Tests d'intégration via CLI JSON (subprocess)
- Documentation basée sur format CLI
- Développement externe (UI, API) indépendant du développement interne

### ❌ À Éviter
- Formats différents entre CLI et autres presenters
- Structure de données divergente
- Bypass CLI pour développement interne
- Dépendances UI dans développement interne

## Conclusion

**Le CLI JSON est la base de référence pour tous les presenters.**

- ✅ Découplage complet
- ✅ Intégration agents IA optimale
- ✅ Développement externe indépendant
- ✅ Structure standardisée

