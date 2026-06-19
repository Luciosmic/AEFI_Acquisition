# Bilan : ScanExecutor et Thread d'Exécution - Architecture Event-Based

## État Actuel de l'Implémentation

### ✅ Ce qui est en place

#### 1. **Architecture Event-Based (Partiellement Implémentée)**

**Domain Events** (`domain/events/motion_events.py`):
- ✅ `MotionStarted` : publié au début d'un mouvement
- ✅ `MotionCompleted` : publié à la fin d'un mouvement
- ✅ `MotionFailed` : publié en cas d'erreur

**Event Bus** (`infrastructure/events/in_memory_event_bus.py`):
- ✅ Implémentation thread-safe (basique)
- ✅ Subscribe/Unsubscribe fonctionnels
- ✅ Publish avec gestion d'erreurs dans les handlers

#### 2. **StepScanExecutor** (`infrastructure/execution/step_scan_executor.py`)

**Points Positifs**:
- ✅ S'abonne aux événements `motioncompleted` et `motionfailed`
- ✅ Utilise `threading.Event` pour synchroniser l'attente de mouvement
- ✅ Vérifie l'annulation pendant l'attente (non-bloquant)
- ✅ Gère les timeouts
- ✅ Se désabonne proprement dans le `finally`

**Flux d'exécution**:
```python
for position in trajectory:
    1. move_to() → retourne motion_id
    2. Attend MotionCompleted via threading.Event
    3. Stabilise
    4. Acquiert
    5. Ajoute résultat au scan
    6. Publie événements domain
```

#### 3. **ArcusAdapter** (`infrastructure/hardware/arcus_performax_4EX/adapter_motion_port_arcus_performax4EX.py`)

**Points Positifs**:
- ✅ Publie `MotionStarted` avant de mettre dans la queue (ligne 300)
- ✅ Publie `MotionCompleted` après mouvement réussi (ligne 193)
- ✅ Publie `MotionFailed` en cas d'erreur (ligne 201)
- ✅ Worker thread séparé pour exécution asynchrone
- ✅ Retourne `motion_id` (UUID) depuis `move_to()`

**Architecture**:
- Worker thread unique gère toute la communication série
- Queue de commandes pour sérialiser les opérations
- Évite les race conditions sur le port série

---

## ❌ Problèmes Identifiés

### 1. **Double Appel à `scan.fail()` - CRITIQUE**

**Symptôme**:
```
ValueError: Cannot fail scan in status ScanStatus.FAILED
```

**Cause**:
- `StepScanExecutor._worker()` catch une exception et appelle `scan.fail()` (ligne 170)
- `ScanApplicationService.execute_scan()` catch aussi l'exception et appelle `self._current_scan.fail()` (ligne 137)

**Séquence d'erreur**:
```python
# Dans StepScanExecutor._worker()
except Exception as exc:
    scan.fail(str(exc))  # ← Premier appel (scan → FAILED)
    return False

# Exception remonte à ScanApplicationService.execute_scan()
except Exception as e:
    if self._current_scan:
        self._current_scan.fail(str(e))  # ← Deuxième appel (déjà FAILED → erreur!)
```

**Solution**:
- Le `StepScanExecutor` ne devrait PAS appeler `scan.fail()` directement
- Il devrait seulement lever l'exception et laisser le service gérer
- OU le service devrait vérifier le statut avant d'appeler `fail()`

### 2. **MockMotionPort Non Compatible avec Event-Based**

**Problème**:
- `MockMotionPort.move_to()` retourne `None` au lieu de `str` (motion_id)
- Ne publie PAS d'événements `MotionStarted`/`MotionCompleted`
- Exécution synchrone (pas de délai réaliste)

**Impact**:
- Le `StepScanExecutor` attend un `motion_id` mais reçoit `None`
- L'attente sur `MotionCompleted` ne se termine jamais (événement jamais publié)
- Le scan bloque indéfiniment avec le mock

**Code actuel** (`adapter_mock_i_motion_port.py`):
```python
def move_to(self, position: Position2D) -> None:  # ← Devrait retourner str
    # Pas d'event_bus, pas d'événements publiés
    self._current_pos = position  # Synchrone, pas de délai
```

**Solution nécessaire**:
- Injecter `event_bus` dans `MockMotionPort.__init__()`
- Retourner un `motion_id` (UUID)
- Publier `MotionStarted` avant le mouvement
- Simuler un délai (thread ou `time.sleep`)
- Publier `MotionCompleted` après le délai

### 3. **Event Bus Non Injecté dans MockMotionPort**

**Problème**:
Dans `main.py` ligne 136:
```python
motion_port = MockMotionPort()  # ← Pas d'event_bus injecté
```

Alors que `ArcusCompositionRoot` injecte l'event_bus correctement.

**Solution**:
- Modifier `main.py` pour injecter `event_bus` dans `MockMotionPort`
- OU modifier `MockMotionPort` pour accepter un `event_bus` optionnel

### 4. **Gestion d'Erreurs dans StepScanExecutor**

**Problème potentiel**:
Si `MotionFailed` est publié, le handler `_on_motion_failed()` met `self._motion_error` mais ne lève pas d'exception immédiatement.

Le code attend que `_motion_completed_event` soit set, puis vérifie `self._motion_error`. C'est correct mais pourrait être plus explicite.

---

## Architecture Thread d'Exécution

### Niveaux de Threads

1. **UI Thread (Main Thread)**
   - PyQt6 event loop
   - Gère les interactions utilisateur
   - Reçoit les signaux Qt pour mise à jour UI

2. **Scan Execution Thread** (`presenter_2d_scan.py` ligne 110)
   - Thread Python standard (`threading.Thread`)
   - Exécute `ScanApplicationService.execute_scan()`
   - Bloquant jusqu'à la fin du scan
   - Émet des signaux Qt pour mettre à jour l'UI (thread-safe)

3. **Motion Worker Thread** (`ArcusAdapter._worker_loop()`)
   - Thread daemon dédié à la communication série Arcus
   - Traite la queue de commandes séquentiellement
   - Publie des événements via EventBus

4. **Event Bus Handlers**
   - Exécutés dans le thread qui publie l'événement
   - Pour `MotionCompleted` : exécuté dans le Motion Worker Thread
   - Pour `StepScanExecutor._on_motion_completed()` : exécuté dans le Motion Worker Thread
   - Utilise `threading.Event` pour synchroniser avec le Scan Execution Thread

### Flux de Synchronisation

```
Scan Execution Thread          Motion Worker Thread
─────────────────────          ────────────────────
move_to(position)
  ↓
  Publie MotionStarted
  ↓
  Attend _motion_completed_event
  ↓ (bloqué)
                              Exécute mouvement
                              ↓
                              Publie MotionCompleted
                              ↓
                              _on_motion_completed() appelé
                              ↓
                              _motion_completed_event.set()
  ↓ (débloqué)
  Continue (stabilise, acquiert)
```

**Avantages**:
- ✅ Découplage entre scan logic et motion hardware
- ✅ Annulation réactive (vérification possible pendant l'attente)
- ✅ Pas de polling CPU-intensive
- ✅ Compatible avec hardware asynchrone

---

## Plan de Correction

### Priorité 1 : Corriger Double `fail()`

**Option A** (Recommandée): Le service gère les erreurs, l'executor lève seulement
```python
# StepScanExecutor._worker()
except Exception as exc:
    # Ne pas appeler scan.fail() ici
    # Juste lever l'exception pour que le service la gère
    raise  # ou return False sans modifier scan

# ScanApplicationService.execute_scan()
except Exception as e:
    if self._current_scan and self._current_scan.status == ScanStatus.RUNNING:
        self._current_scan.fail(str(e))
```

**Option B**: L'executor gère, le service vérifie le statut
```python
# ScanApplicationService.execute_scan()
except Exception as e:
    if self._current_scan and self._current_scan.status != ScanStatus.FAILED:
        self._current_scan.fail(str(e))
```

### Priorité 2 : Rendre MockMotionPort Event-Based

1. Modifier `MockMotionPort.__init__()`:
   ```python
   def __init__(self, event_bus: Optional[IDomainEventBus] = None, motion_delay_ms: float = 100.0):
       self._event_bus = event_bus
       self._motion_delay_ms = motion_delay_ms
   ```

2. Modifier `move_to()` pour retourner `motion_id` et publier événements:
   ```python
   def move_to(self, position: Position2D) -> str:
       motion_id = str(uuid4())
       
       if self._event_bus:
           self._event_bus.publish("motionstarted", MotionStarted(...))
       
       # Simuler mouvement dans thread séparé
       threading.Thread(target=self._simulate_motion, args=(motion_id, position), daemon=True).start()
       
       return motion_id
   ```

3. Injecter `event_bus` dans `main.py`:
   ```python
   motion_port = MockMotionPort(event_bus=event_bus)
   ```

### Priorité 3 : Tests

- Test unitaire : Mock avec événements
- Test d'intégration : Scan complet avec mock
- Test e2e : Scan avec hardware réel

---

## Conclusion

**État Global**: Architecture event-based partiellement implémentée
- ✅ Infrastructure en place (EventBus, Events, Executor)
- ✅ ArcusAdapter compatible
- ❌ MockMotionPort non compatible
- ❌ Double gestion d'erreurs

**Prochaines Étapes**:
1. Corriger le double `fail()` (critique)
2. Rendre MockMotionPort event-based (bloquant pour tests)
3. Valider avec tests unitaires
4. Tester avec hardware réel


