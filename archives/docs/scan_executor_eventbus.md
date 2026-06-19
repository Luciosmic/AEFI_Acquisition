# Scan Executor avec Event Bus - Architecture Event-Based

## Problème Actuel

### Symptôme
Le scan executor ne fonctionne pas correctement avec le hardware réel (Arcus), alors que le mock fonctionne.

### Cause Racine

**Différence de comportement Mock vs Hardware réel :**

1. **MockMotionPort** (fonctionne) :
   - `move_to()` est **synchrone** : met à jour la position immédiatement
   - `wait_until_stopped()` ne fait rien (mock toujours arrêté)

2. **ArcusAdapter** (ne fonctionne pas) :
   - `move_to()` est **asynchrone** : met la commande dans une queue et retourne immédiatement
   - Le worker thread exécute le mouvement en arrière-plan
   - `wait_until_stopped()` fait du polling sur `is_moving()` → **race condition**

### Séquence Problématique

```python
# Dans StepScanExecutor._worker()
self._motion_port.move_to(position)  # ← Asynchrone, retour immédiat
self._motion_port.wait_until_stopped()  # ← Vérifie is_moving() immédiatement
# Problème : le worker thread n'a peut-être pas encore commencé le mouvement
```

### Problème d'Arrêt d'Urgence

Si `wait_until_stopped()` est bloqué dans une boucle de polling, l'annulation du scan n'est pas détectée immédiatement :

```python
# Dans StepScanExecutor._worker()
for i, position in enumerate(trajectory):
    if scan.status == ScanStatus.CANCELLED:  # ← Vérifié entre les points
        return False
    self._motion_port.move_to(position)
    self._motion_port.wait_until_stopped()  # ← BLOQUÉ ICI si mouvement en cours
    # L'annulation n'est pas vérifiée pendant l'attente
```

---

## Solution Proposée : Architecture Event-Based

### Principe

Utiliser l'Event Bus existant pour découpler le scan executor du hardware motion :

1. **Motion Port** publie des événements :
   - `MotionStarted` : mouvement commencé
   - `MotionCompleted` : mouvement terminé
   - `MotionFailed` : erreur de mouvement

2. **Scan Executor** s'abonne à ces événements :
   - Attend `MotionCompleted` avant de passer au point suivant
   - Vérifie l'annulation entre les événements (non-bloquant)

3. **Mock réaliste** :
   - Simule les délais de mouvement
   - Publie les mêmes événements que le hardware réel

### Avantages

- ✅ **Découplage** : Scan executor ne dépend plus de l'implémentation motion
- ✅ **Annulation réactive** : Vérification possible entre les événements
- ✅ **Testable sans hardware** : Mock réaliste avec événements
- ✅ **Cohérent avec l'architecture** : Utilise l'Event Bus existant
- ✅ **Extensible** : D'autres composants peuvent s'abonner aux événements motion

---

## Architecture Event-Based

### 1. Domain Events

```python
# domain/events/motion_events.py

@dataclass
class MotionStarted(DomainEvent):
    """Événement publié quand un mouvement commence."""
    motion_id: str
    target_position: Position2D
    timestamp: datetime

@dataclass
class MotionCompleted(DomainEvent):
    """Événement publié quand un mouvement est terminé."""
    motion_id: str
    final_position: Position2D
    duration_ms: float
    timestamp: datetime

@dataclass
class MotionFailed(DomainEvent):
    """Événement publié en cas d'erreur de mouvement."""
    motion_id: str
    error: str
    timestamp: datetime
```

### 2. Motion Port (Interface)

```python
# application/services/scan_application_service/i_motion_port.py

class IMotionPort(ABC):
    @abstractmethod
    def move_to(self, position: Position2D) -> str:
        """
        Démarre un mouvement vers la position cible.
        
        Returns:
            motion_id: Identifiant unique du mouvement (pour associer événements)
        """
        pass
    
    # ... autres méthodes existantes ...
```

### 3. ArcusAdapter (Implémentation Réelle)

```python
# infrastructure/hardware/arcus_performax_4EX/adapter_motion_port_arcus_performax4EX.py

class ArcusAdapter(IMotionPort):
    def __init__(self, ..., event_bus: IDomainEventBus):
        self._event_bus = event_bus
        # ...
    
    def move_to(self, position: Position2D) -> str:
        motion_id = str(uuid4())
        
        # Publier événement de début
        event = MotionStarted(
            motion_id=motion_id,
            target_position=position,
            timestamp=datetime.now()
        )
        self._event_bus.publish("motionstarted", event)
        
        # Mettre dans la queue (asynchrone)
        self._command_queue.put(("MOVE_TO", (motion_id, position)))
        
        return motion_id
    
    def _internal_move_to(self, motion_id: str, position: Position2D):
        """Exécuté par le worker thread."""
        start_time = time.time()
        try:
            # ... mouvement réel ...
            final_pos = self.get_current_position()
            
            # Publier événement de fin
            event = MotionCompleted(
                motion_id=motion_id,
                final_position=final_pos,
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
            self._event_bus.publish("motioncompleted", event)
        except Exception as e:
            event = MotionFailed(
                motion_id=motion_id,
                error=str(e),
                timestamp=datetime.now()
            )
            self._event_bus.publish("motionfailed", event)
```

### 4. MockMotionPort (Mock Réaliste)

```python
# infrastructure/mocks/adapter_mock_i_motion_port.py

class MockMotionPort(IMotionPort):
    def __init__(self, event_bus: IDomainEventBus, motion_delay_ms: float = 100.0):
        self._event_bus = event_bus
        self._motion_delay_ms = motion_delay_ms  # Simule le temps de mouvement
        # ...
    
    def move_to(self, position: Position2D) -> str:
        motion_id = str(uuid4())
        
        # Publier événement de début
        event = MotionStarted(
            motion_id=motion_id,
            target_position=position,
            timestamp=datetime.now()
        )
        self._event_bus.publish("motionstarted", event)
        
        # Simuler le mouvement dans un thread (comme le hardware réel)
        threading.Thread(
            target=self._simulate_motion,
            args=(motion_id, position),
            daemon=True
        ).start()
        
        return motion_id
    
    def _simulate_motion(self, motion_id: str, target: Position2D):
        """Simule un mouvement avec délai réaliste."""
        start_time = time.time()
        time.sleep(self._motion_delay_ms / 1000.0)  # Simule le temps de mouvement
        
        # Mettre à jour la position
        self._current_pos = target
        
        # Publier événement de fin
        event = MotionCompleted(
            motion_id=motion_id,
            final_position=target,
            duration_ms=(time.time() - start_time) * 1000,
            timestamp=datetime.now()
        )
        self._event_bus.publish("motioncompleted", event)
```

### 5. StepScanExecutor (Refactoré)

```python
# infrastructure/execution/step_scan_executor.py

class StepScanExecutor(IScanExecutor):
    def __init__(self, ..., event_bus: IDomainEventBus):
        self._event_bus = event_bus
        # ...
        self._pending_motion_id: Optional[str] = None
        self._motion_completed_event = threading.Event()
    
    def _worker(self, scan: StepScan, trajectory: ScanTrajectory, config: StepScanConfig) -> bool:
        # S'abonner aux événements motion
        self._event_bus.subscribe("motioncompleted", self._on_motion_completed)
        self._event_bus.subscribe("motionfailed", self._on_motion_failed)
        
        try:
            for i, position in enumerate(trajectory):
                # Vérifier annulation AVANT chaque mouvement
                if scan.status == ScanStatus.CANCELLED:
                    return False
                
                # A. Démarrer mouvement (non-bloquant)
                motion_id = self._motion_port.move_to(position)
                self._pending_motion_id = motion_id
                self._motion_completed_event.clear()
                
                # B. Attendre événement MotionCompleted (avec timeout et vérification annulation)
                timeout = 30.0  # secondes
                start_wait = time.time()
                
                while not self._motion_completed_event.is_set():
                    # Vérifier annulation PENDANT l'attente
                    if scan.status == ScanStatus.CANCELLED:
                        # Annuler le mouvement en cours
                        self._motion_port.stop(immediate=True)
                        return False
                    
                    # Vérifier timeout
                    if time.time() - start_wait > timeout:
                        raise RuntimeError(f"Motion timeout after {timeout}s")
                    
                    time.sleep(0.01)  # Petit délai pour éviter CPU spinning
                
                # C. Stabilize
                if config.stabilization_delay_ms > 0:
                    time.sleep(config.stabilization_delay_ms / 1000.0)
                
                # D. Acquire (existant)
                # ...
        finally:
            # Se désabonner
            self._event_bus.unsubscribe("motioncompleted", self._on_motion_completed)
            self._event_bus.unsubscribe("motionfailed", self._on_motion_failed)
    
    def _on_motion_completed(self, event: MotionCompleted):
        """Handler appelé quand le mouvement est terminé."""
        if event.motion_id == self._pending_motion_id:
            self._motion_completed_event.set()
    
    def _on_motion_failed(self, event: MotionFailed):
        """Handler appelé en cas d'erreur de mouvement."""
        if event.motion_id == self._pending_motion_id:
            raise RuntimeError(f"Motion failed: {event.error}")
```

---

## Plan d'Implémentation

### Phase 1 : Domain Events (Sans modification du code existant)
1. Créer `domain/events/motion_events.py`
2. Définir `MotionStarted`, `MotionCompleted`, `MotionFailed`

### Phase 2 : Mock Réaliste (Testable sans hardware)
1. Modifier `MockMotionPort` pour publier des événements
2. Ajouter délai de simulation configurable
3. Tester avec `StepScanExecutor` (mock uniquement)

### Phase 3 : ArcusAdapter (Hardware réel)
1. Modifier `ArcusAdapter.move_to()` pour retourner `motion_id`
2. Publier `MotionStarted` avant de mettre dans la queue
3. Publier `MotionCompleted`/`MotionFailed` dans le worker thread
4. Injecter `event_bus` dans `ArcusAdapter.__init__()`

### Phase 4 : StepScanExecutor (Refactoring)
1. S'abonner aux événements motion dans `_worker()`
2. Remplacer `wait_until_stopped()` par attente d'événement
3. Vérifier annulation pendant l'attente
4. Gérer timeout et erreurs

### Phase 5 : Tests
1. Test unitaire : Mock avec événements
2. Test d'intégration : Scan complet avec mock
3. Test e2e : Scan avec hardware réel (quand disponible)

---

## Questions Ouvertes

1. **Timeout** : Quelle valeur par défaut pour le timeout de mouvement ?
   - le timeout n'est pas à gérer par scanExecutor; on doit faire une prédiction du temps de trajet ; le timeout maximal est lié la longueur du banc et la vitesse de déplacement lors de la consigne.

2. **Gestion d'erreurs** : Comment gérer `MotionFailed` dans le scan ?
   -  Arrêter le scan immédiatement
-

3. **Multiple mouvements** : Que faire si un nouveau `move_to()` est appelé avant la fin du précédent ?
   - Option A : Rejeter (erreur) - qui est responsable de cela ? 

4. **Event Bus thread-safety** : L'Event Bus est-il thread-safe ?
   - À vérifier dans `InMemoryEventBus`
   - Si non, ajouter des locks

---

## Références

- Event Bus existant : `infrastructure/events/in_memory_event_bus.py`
- Scan Executor actuel : `infrastructure/execution/step_scan_executor.py`
- Motion Port interface : `application/services/scan_application_service/i_motion_port.py`
- Arcus Adapter : `infrastructure/hardware/arcus_performax_4EX/adapter_motion_port_arcus_performax4EX.py`


