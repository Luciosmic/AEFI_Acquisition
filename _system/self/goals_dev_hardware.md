# Objectifs — worktree dev_hardware

Fichier séparé de `goals.md` (qui reste porté par `develop`) pour éviter les conflits de merge :
ce worktree/branche est un contexte borné dédié au travail hardware (sonde Narda EP-601 en premier lieu).

## Feature en cours : Compensation fréquence sonde Narda EP-601

### Contexte

Le driver bas niveau expose déjà `NardaEP601.set_frequency_correction(freq_hz)` (commande série `#00k`, correction de calibration factory à une fréquence donnée), mais **aucune couche applicative ne l'appelle** — les lectures actuelles ne sont pas corrigées en fréquence. Cahier des charges demandé :

1. Voyant UI indiquant si la compensation est appliquée, avec si possible la valeur du facteur.
2. Changement de fréquence d'excitation (AD9106) → recalage de la correction, **prioritaire dès la prochaine acquisition** (sans forcément arrêter un scan en cours).
3. À chaque connexion sonde → appliquer immédiatement la fréquence d'excitation courante.
4. La sonde n'est qualifiée qu'à partir de 10kHz (`RF_SENSING_RANGE_HZ = (10_000, 9_250_000_000)`) — proposer une gestion du cas hors plage.

### Décisions de conception

**A. Notification inter-services (excitation → sonde).** `ExcitationConfigurationService` n'a aujourd'hui aucune dépendance à l'event bus. On lui ajoute `event_bus: IDomainEventBus` au constructeur ; `set_excitation()` publie un nouvel événement `ExcitationFrequencyChanged(frequency_hz)` **uniquement si la fréquence a réellement changé** (comparaison avec `self._current_params.frequency` avant écrasement) — évite de spammer une correction sonde à chaque changement de mode/niveau. Événement placé dans `domain/shared_kernel/events/` (pas d'aggregate root côté excitation). `ElectricFieldProbeService` s'abonne à ce topic dans son propre `__init__` (aucun nouveau paramètre de constructeur requis pour lui).

**B. Appliquer la correction sans corrompre un stream en cours.** Le worker de `ElectricFieldProbeAcquisitionExecutor` tourne sur un thread dédié et est seul à toucher le port série pendant le streaming (même raison que `refresh_battery` refuse de s'exécuter pendant l'acquisition). On ajoute une méthode `request_frequency_correction(frequency_hz)` qui se contente d'écrire `self._pending_frequency_hz = frequency_hz` (écriture de référence unique, atomique sous le GIL CPython — pas un verrou général, suffisant ici). Le worker lit cette valeur à chaque itération (avant `acquire_sample()`) et la compare à une variable **locale** `last_requested_frequency_hz` : si elle diffère, il applique la correction via `probe_port.apply_frequency_correction(...)` et publie le résultat comme événement domain, exactement comme il le fait déjà pour `FieldSampleAcquired`. Le worker ne réinitialise jamais `self._pending_frequency_hz` à `None` — un read-then-clear introduirait une fenêtre où une requête concurrente serait silencieusement perdue.

Bonus déduit de ce design : comme `_pending_frequency_hz` est un attribut de l'exécuteur (persiste entre `stop()`/`start()`), et que chaque nouveau thread worker repart avec `last_requested_frequency_hz = None`, un redémarrage de stream (ex. changement de sample_rate) **réapplique automatiquement** la dernière fréquence connue au premier tour de boucle — sans code supplémentaire dans le service. Le seul effet de bord est un aller-retour série redondant harmless au redémarrage si rien n'a changé entretemps.

Quand l'acquisition n'est PAS en cours (idle), pas de thread concurrent : `ElectricFieldProbeService` appelle `probe_port.apply_frequency_correction(...)` directement et publie lui-même le résultat.

**C. Cas <10kHz.** `apply_frequency_correction` côté adapter vérifie `frequency_hz < RF_SENSING_RANGE_HZ[0]` **avant** tout appel driver : retourne `in_range=False, applied_hz=None` sans round-trip série ni exception — ce n'est pas une panne matérielle mais une limite physique permanente de la sonde (diode/antenne non qualifiée sous 10kHz selon datasheet). **On ne clamp pas** à 10kHz (ça laisserait croire à une compensation valide qui ne l'est pas) : la dernière correction appliquée reste inchangée, et l'UI affiche un état distinct et explicite. Les vraies pannes matérielles (ValueError/IOError du driver) sont capturées dans l'adapter et renvoyées comme `error=str(e)` plutôt que propagées — l'appelant n'a jamais à connaître les exceptions spécifiques au driver.

Nuance à afficher dans l'UI : le protocole ne renvoie **aucun facteur de gain numérique**, seulement le point de calibration en fréquence (Hz) que la sonde confirme avoir appliqué. Le "facteur affiché" sera donc `"Compensée @ X kHz/MHz"`, jamais un chiffre de gain inventé.

**D. État sur l'agrégat vs événement+cache présentateur.** Contrairement à la batterie (rafraîchie manuellement, rarement), la correction fréquence peut changer plusieurs fois par seconde en cours de stream et est appliquée depuis le thread worker. On ne touche donc PAS à `ElectricFieldProbe` (dataclass frozen) : le présentateur garde juste le dernier état reçu pour l'affichage, comme il le fait déjà pour `_noise_offset`/`_last_raw_sample`.

### Fichiers

#### Domain (nouveaux)
- `domain/shared_kernel/events/excitation_frequency_changed/excitation_frequency_changed.py` — `ExcitationFrequencyChanged(DomainEvent)`, champ `frequency_hz: float`. + `_intention.md`.
- `domain/electric_field_probe/events/electric_field_probe_frequency_correction_changed/electric_field_probe_frequency_correction_changed.py` — `ElectricFieldProbeFrequencyCorrectionChanged(DomainEvent)`, champs `requested_hz: float`, `applied_hz: Optional[float]`, `in_range: bool`, `error: Optional[str] = None`. + `_intention.md`. (Nommé "Changed" et non "Applied" : couvre aussi les cas hors-plage/erreur.)

#### Application (modifiés)
- `application/services/electric_field_probe_service/dtos/electric_field_probe_dtos.py` — ajoute `FrequencyCorrectionResult(requested_hz, applied_hz: Optional[float], in_range: bool, error: Optional[str] = None)`.
- `application/services/electric_field_probe_service/ports/i_electric_field_probe_port.py` — ajoute `apply_frequency_correction(self, frequency_hz: float) -> FrequencyCorrectionResult`, docstring précisant : pas d'appel concurrent pendant le streaming (passer par l'exécuteur), jamais d'exception levée pour une panne matérielle (capturée dans `error`).
- `application/services/electric_field_probe_service/ports/i_electric_field_probe_acquisition_executor.py` — ajoute `request_frequency_correction(self, frequency_hz: float) -> None`.
- `application/services/electric_field_probe_service/electric_field_probe_service.py` :
  - constantes `EXCITATION_FREQUENCY_CHANGED_TOPIC`, `FREQUENCY_CORRECTION_CHANGED_TOPIC`.
  - `__init__` : `self._last_known_excitation_frequency_hz: float = 0.0` (miroir de `ExcitationParameters.off().frequency`) ; abonnement à `EXCITATION_FREQUENCY_CHANGED_TOPIC`.
  - helper privé `_publish_frequency_correction(result)`.
  - `connect_probe()` : après connexion réussie, `result = self._probe_port.apply_frequency_correction(self._last_known_excitation_frequency_hz)` + publish (satisfait l'exigence 3), avant de publier `CONNECTION_CHANGED_TOPIC`.
  - nouveau `_on_excitation_frequency_changed(event)` : stocke la fréquence ; si non connecté, return ; si `executor.is_running()`, `executor.request_frequency_correction(event.frequency_hz)` (le worker publiera lui-même) ; sinon appel direct + publish.
- `application/services/excitation_configuration_service/excitation_configuration_service.py` :
  - `__init__(self, excitation_port, event_bus: IDomainEventBus)`.
  - `set_excitation()` : compare l'ancienne/nouvelle fréquence, publie `ExcitationFrequencyChanged` sur `EXCITATION_FREQUENCY_CHANGED_TOPIC` seulement si elle diffère.

#### Infrastructure (modifiés)
- `infrastructure/execution/electric_field_probe_acquisition_executor.py` :
  - `self._pending_frequency_hz: Optional[float] = None` dans `__init__`.
  - `request_frequency_correction()` : écriture simple de l'attribut.
  - `_worker()` : variable locale `last_requested_frequency_hz = None` ; à chaque itération, lecture/comparaison/application/publish avant `acquire_sample()`, avec try/except autour de `apply_frequency_correction` (publie `error=str(e)` plutôt que de crasher la boucle, même tolérance que pour les échecs d'échantillon).
- `infrastructure/hardware/narda_ep600/adapter_electric_field_probe_port.py` — `apply_frequency_correction()` : check `RF_SENSING_RANGE_HZ[0]` avant appel driver ; try/except autour de `driver.set_frequency_correction` → `FrequencyCorrectionResult`.
- `infrastructure/hardware/narda_ep600/fake/fake_electric_field_probe_adapter.py` — même méthode, simulation (quantification 10kHz) pour permettre de tester tout le flux sans matériel (`HARDWARE_CONFIG["electric_field_probe"] = "mock"`).

#### Interface (modifiés)
- `interface/presenters/electric_field_probe_presenter.py` :
  - abonnement/désabonnement à `FREQUENCY_CORRECTION_CHANGED_TOPIC` dans `__init__`/`shutdown()`.
  - nouveau signal `frequency_correction_changed = Signal(str, str)` (état, texte à afficher).
  - handler qui traduit l'événement en un des 4 états : `applied` (vert, `"Compensée @ X kHz/MHz"`), `out_of_range` (ambre, `"Hors plage sonde (<10kHz) — non compensée, sonde non qualifiée à cette fréquence"`), `error` (rouge), `unknown` (gris, `"—"`, y compris à la déconnexion).
- `interface/widgets/panels/electric_field_probe_panel.py` — nouveau `QLabel` voyant dans le groupe "Probe" (à côté de `lbl_probe_status`/`lbl_data_status`), méthode `on_frequency_correction_changed(state, text)` avec dict couleurs suivant la convention existante (`#2ECC71`/`#F4D03F`/`#E74C3C`/`#888`).

#### Composition root
- `main.py` : `ExcitationConfigurationService(excitation_port, event_bus)` (ligne ~277) ; nouveau connect signal→slot pour le voyant (près de la ligne ~438).
- `infrastructure/mocks/example_excitation_aware_usage.py` (ligne ~213) — même ajout d'argument pour ne pas casser l'exemple.

### Tests

- `excitation_configuration_service_test.py` : ajout `event_bus = MagicMock(spec=IDomainEventBus)` dans `setUp` ; test publish sur changement de fréquence ; test absence de publish si seuls mode/niveau changent.
- `electric_field_probe_service_test.py` : test connexion applique la dernière fréquence connue (par défaut 0.0 → hors plage) ; test application directe si idle ; test hors-plage <10kHz ; test application via l'exécuteur pendant un streaming en cours (sans redémarrage — vérifier que le flux d'échantillons n'est pas interrompu).
- **Nouveau** `infrastructure/execution/_tests/electric_field_probe_acquisition_executor_test.py` (n'existe pas encore) : correction appliquée une seule fois sans redémarrage du thread, aucun appel si rien n'est demandé, événement publié avec les bons champs.
- `fake_electric_field_probe_adapter_test.py` : hors-plage vs en-plage.
- **Nouveau** `narda_ep600/_tests/adapter_electric_field_probe_port_test.py` (n'existe pas encore pour l'adapter réel) : hors-plage ne touche pas le port série, en-plage retourne la fréquence appliquée par le driver, mismatch driver → `error` renvoyé (pas d'exception).

Tous les nouveaux tests suivent les conventions déjà en place (`MagicMock(spec=...)`, `DiagramFriendlyTest`, mock de `serial.Serial` comme dans `driver_narda_ep601_test.py`).

### Vérification

- `uv run pytest src/application/services/electric_field_probe_service src/application/services/excitation_configuration_service src/infrastructure/execution src/infrastructure/hardware/narda_ep600 -v`
- Lancement manuel de l'app en mode mock (`HARDWARE_CONFIG["electric_field_probe"] = "mock"`, `"excitation" = "mock"` ou `"real"` selon dispo) : régler une fréquence >10kHz dans le panneau Excitation → voyant vert avec la fréquence affichée ; régler <10kHz → voyant ambre "hors plage" ; connecter la sonde après avoir déjà réglé une fréquence → voyant appliqué dès la connexion ; démarrer une acquisition puis changer la fréquence en cours de stream → voyant se met à jour sans coupure du tracé live.
