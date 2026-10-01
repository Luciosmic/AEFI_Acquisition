# Tâches actives

## Fly-scan : transmission mécanique au domaine, puis projection en direct

**Statut** (2026-10-01) : worktree `dev_scan` (décision Luis : tout se fait ici, y compris calibration et
hardware). **Phase A faite** (non commitée) : suite verte hors le test de cadence du fake MCU, instable avant ce
chantier ; démarrage réel en mock vérifié (amorçage moteur/driver/transmission, adaptateur à 21,8 µm/impulsion,
avertissement de courant logué, second démarrage sans réamorçage). Phases B et C à faire. Décision ouverte avant B :
décalage d'une demi-rampe.

### Contexte

Une première version du fly-scan (non commitée) plaçait les mesures **en fin de ligne**, en
normalisant par la durée mesurée de la ligne. Lancée dans l'appli (mock), elle a fait planter
l'application au 27e balayage : le journal d'événements s'arrête net en plein balayage, sans
`ScanFailed`. Cause soupçonnée, **non prouvée** : 81 points envoyés d'un coup à des panneaux
matplotlib qui redessinent tout à chaque point. Décision Luis : projeter **en direct**, à
**vitesse constante**, la vitesse venant de la calibration.

Vitesse = facteur de conversion × fréquence de pas du mode (HS). Le facteur n'est pas propre à
Arcus : il dépend de toute la chaîne (moteur, driver et son réglage, mécanique). Il doit donc
vivre au domaine, et l'infrastructure ne parle en Hz/pas que chez elle.

**Faits (doc `_system/documentation/hardware_datasheet/motorisation/` + notes Luis)** :
- Moteur Igus MOT-AN-S-060-035-060-L-A-AAAA : 200 pas/tour, Nennstrom 4,2 A (datasheet ne
  précise pas efficace ou crête). Pas d'encodeur. Même modèle sur X et Y.
- Driver TB6600 : 1/16 de pas (3200 impulsions/tour), courant max du driver 3,5 A (4,0 A crête).
  1/32 ne fonctionne pas ; 3,0 A saute des pas sur les petits mouvements. Plus de dérive depuis
  le passage au courant max.
- 21,8 µm/impulsion pour le 1/16 = 43,6 (1/8, « probablement ») ÷ 2 — calculé, pas re-mesuré
  en 1/16. D'où une avance de 21,8 µm × 200 × 16 = **69,76 mm par tour moteur**.
- Aujourd'hui le facteur vient de `arcus_default_config.json` (lu par l'adaptateur, modifiable
  dans le panneau avancé Arcus). **Piège** : si ce fichier manque, l'adaptateur retombe sans
  rien dire sur sa constante de classe 43,6 (valeur 1/8) → positions fausses ×2.
- Le type de composant « Moteurs » déclare `step_um`, `max_speed_mm_per_s`,
  `acceleration_mm_per_s2` : jamais remplis, les deux derniers jamais demandés.

### Phase A — Transmission mécanique au domaine

Modèle calqué sur le capteur : produit au catalogue, montage dans le journal, ce qui dépend de
l'assemblage sur ce banc dans une calibration banc qui référence les montages par identité.

1. **Catalogue** (`HardwareComponentKind`) :
   - « Moteurs » : remplacer les 3 grandeurs par `full_steps_per_revolution` (pas/tour) et
     `rated_current_a` (courant nominal, A).
   - Nouveau type « Driver pas à pas » (`stepper_driver`) : `max_current_a` (A).
2. **Calibration banc « transmission mécanique »** (entité de l'agrégat `Calibration`, trio
   atomique, entrées datées, la plus récente fait foi, comme la géométrie des sources) :
   montage moteur, montage driver, micro-pas (16), courant réglé (3,5 A) et sa crête (4,0 A),
   avance par tour moteur (69,76 mm). Une seule transmission pour X et Y.
3. **Règles domaine** :
   - µm/impulsion = avance par tour ÷ (pas/tour du moteur × micro-pas) → 21,8.
   - Courant réglé < courant nominal du moteur → avertissement (non bloquant) affichant les
     deux valeurs du driver : « 3,5 A (4,0 A crête) < nominal moteur 4,2 A ». Permanent sur ce
     banc (le TB6600 plafonne sous 4,2 A) : c'est un fait connu, pas une erreur.
4. **Amorçage sans saisie** : un template versionné `config_templates/` contient moteur,
   driver et transmission ci-dessus ; au premier démarrage, la composition root les enregistre
   via les services (même chemin que l'UI, comme la géométrie des sources) et monte moteur et
   driver.
5. **Infrastructure** :
   - `IMotionPort` reçoit le facteur (µm/impulsion) ; la composition root le lui donne au
     démarrage, avant tout mouvement.
   - `ArcusAdapter` ne lit plus `arcus_default_config.json` pour le facteur, plus de constante
     43,6 : **refuse de bouger** tant qu'il n'a pas reçu de facteur.
   - Retrait de `microns_per_step` du template Arcus et du panneau avancé Arcus.
   - Le caractériseur de timing lit le facteur courant comme l'appli.
6. **Export** : la transmission courante (et l'avertissement de courant) dans les métadonnées
   d'acquisition, à côté des composants.

Hors périmètre de cette phase : onglet UI pour saisir une nouvelle transmission (changer de
réglage = éditer le template/registre, puis redémarrer) ; contrôleur PMX-4EX non référencé
(aucune grandeur utile aujourd'hui).

### Phase B — Projection en direct

1. `IMotionPort` expose la vitesse de croisière du mode courant en mm/s (HS lu sur le
   contrôleur × facteur reçu). Mock : idem.
2. Domaine : la règle « vitesse constante » remplace la normalisation par durée de ligne —
   position = début + vitesse × (t − t_départ − décalage) ; dit quel point de grille vient
   d'être dépassé. **Décision ouverte** : décalage = demi-rampe du mode (recommandé : sans lui,
   ~16 mm d'erreur en fast, ~5 mm en medium) ou 0.
3. Boucle fly : chaque point émis dès qu'il est dépassé (interpolation entre les deux
   échantillons qui encadrent son instant) ; points restants en fin de ligne = dernier
   échantillon.
4. Affichage : mesurer le coût de redessin des panneaux, limiter la cadence si nécessaire
   (fast, pas 2,5 mm → 24 points/s). Attention : `scan_visualization_panel.py`,
   `dashboard*.py` ont des modifications non commitées qui ne viennent pas de ce chantier.

### Phase C — Vérification

- Suite de tests.
- **Appli réelle en mode mock** (`main_mock.py`) : un fly-scan complet sur la grille par défaut
  (81 × 81) sans plantage, carte remplie en direct, avant de dire que ça marche.
- Limite connue : le fake Arcus ne valide que la plomberie (position linéaire sur tout le
  déplacement, pas de rampe, pas de latence USB) ; le calage du décalage se fait au banc.

## Observabilité : migration vers Observability-Driven Design (ODD)

**Statut** : pas commencé — prompt de démarrage prêt ci-dessous, à lancer dans une nouvelle
discussion (chantier distinct, nécessite une décision d'architecture avant tout code).

### Contexte — pourquoi ce chantier existe

Une session précédente (2026-09-18) a fait une remédiation de logging massive (commit
`c2043b6`, 136 fichiers) : conversion de ~220 `print()` en `logging.getLogger(__name__)`
sur toute la couche application/infrastructure, en suivant le standard Packmind
**"Logs-Driven Design (LDD)"** (`.packmind/standards/logs-driven-design-ldd.md`).

En cours de route, deux standards Packmind plus récents sont apparus côté org UTUKI et
n'existaient pas au moment où ce travail a été planifié :

- **"Observability-Driven Design (ODD)"**
  (`.packmind/standards/standard-observability-driven-design-odd.md`) — remplace/étend
  LDD. Reprend ses règles (logger nommé, granularité intention métier, décisions de
  branche non triviales loguées) et ajoute :
  - **3 piliers OpenTelemetry** : métriques (détectent qu'un problème existe), logs
    (diagnostiquent pourquoi), traces (montrent le chemin). Un log seul ne détecte pas
    une absence de signal.
  - **Logs structurés obligatoires** (JSON ou clé=valeur) — jamais de chaîne interpolée
    libre. Tout le travail déjà committé utilise des f-strings/`%s` en texte libre, donc
    **ne respecte pas cette règle**.
  - **`correlation_id`** généré à l'entrée de tout flux async/multi-étapes, propagé dans
    tous les logs/métriques de la chaîne — jamais recréé à mi-flux. **N'existe nulle
    part dans le code actuel.**
  - **Métriques de comptage** sur tout flux métier significatif (succès/échec) et sur
    toute exception capturée (type + contexte métier). **Aucune lib de métriques
    intégrée** (pas de `prometheus_client`, pas d'OpenTelemetry SDK) — à choisir.
  - **Subsegments de trace** par opération métier distincte dans un flux multi-étapes.
    **Aucun tracing n'existe.**

- **"SolidAI — EventStore : Création de Domain Events"** — précise la frontière domain
  event vs log ODD : une idempotence ou un rejet d'invariant domain n'est JAMAIS un
  domain event, toujours un log+métrique côté application. Déjà appliqué (voir commit 4
  ci-dessous).

Ces deux standards ont été synchronisés dans ce repo ET propagés dans les 4 autres
worktrees (`AEFI_Acquisition`, `AEFI_Acquisition_dev_hardware`,
`AEFI_Acquisition_dev_scan`, `AEFI_Acquisition_n8n-poc`) via
`npx @packmind/cli@latest install`. Si le tunnel SSH vers le serveur Packmind (port
8081, localhost via tunnel) n'est plus ouvert, la skill `get-solidai-standards`
documente comment le rétablir.

### Déjà fait (lire les commits pour le détail exact, ne pas refaire)

Sur `develop`, 4 commits de cette lignée de travail :

1. `074197a` — chore(packmind): sync standards
2. `c2043b6` — refactor(observability): migration print()→logging LDD, 136 fichiers,
   infra + application uniquement (domain volontairement exclu, voir point 4)
3. `0a24f63` — fix(scan): correction d'une race condition subscribe-after-publish dans
   `scan_differential_mode_integration_test.py` (trouvée en creusant une flakiness de
   tests révélée — pas causée — par le commit 2 ; confirmé par profiling cProfile que le
   temps perdu vient d'attentes `threading.Event.wait()` légitimes, pas du logging)
4. `cb79201` — fix(domain): 4 trous d'observabilité domain fermés (audit en 3
   sous-agents sur les 76 fichiers domain), en appliquant la règle EventStore/ODD :
   idempotence → valeur de retour observable + log côté appelant ; rejet d'invariant →
   exception ; jamais un domain event pour ces deux cas. Le domain reste pur : zéro
   `import logging` dedans, par design.

Lire `git show <sha> --stat` puis `git log -1 <sha>` pour le détail de chaque commit
avant de commencer, pour ne pas re-découvrir ce qui est déjà su.

### Périmètre de ce chantier

Amener le travail existant au niveau ODD complet :

1. **Format structuré** — convertir les logs texte libre en JSON/clé=valeur, en gardant
   la lisibilité humaine dans le panneau Logs Qt existant
   (`src/interface/widgets/panels/logs_panel.py`) — probablement deux sorties, pas une
   seule (lisible à l'écran + structuré vers un sink séparé).
2. **`correlation_id`** — génération à l'entrée de chaque flux (ex. `execute_scan()`,
   `apply_config()`), propagation à travers les threads (`ThreadPoolTaskRunner`) et les
   domain events (le standard EventStore le veut aussi comme champ optionnel sur les
   events eux-mêmes).
3. **Métriques** — aucune lib en place ; c'est un outil desktop mono-poste, pas un
   service web avec Prometheus à côté. Évaluer des pistes légères (compteurs in-process
   exposés dans un panneau UI, ou métriques déduites de logs structurés agrégables)
   avant de choisir une stack lourde.
4. **Traces** — même remarque : évaluer si OpenTelemetry complet a du sens pour un
   poste mono-utilisateur, ou si `correlation_id` + logs d'étape structurés suffisent.

### Méthode recommandée

**Ne pas commencer par écrire du code.** Il y a une vraie décision d'architecture à
trancher (quelle stack métriques/traces pour un outil desktop, quel format structuré)
avant toute exécution. Proposer un plan court, le faire valider, puis seulement lancer
des sous-agents d'exécution (comme pour le passage print()→logging).

### Point connexe, pas ce chantier

Gap de fidélité QoS trouvé en tâche annexe (audit du commit `c2043b6`) : le nouveau
standard SolidAI publié cette session-là
(`solidai-fidelite-de-promesse-des-doubles-de-test-...`) a motivé un audit des mocks qui
a trouvé `adapter_mock_i_motion_port.py::home()` retournant instantanément alors que le
vrai driver Arcus a des timeouts de homing mécanique jusqu'à 120s. Non corrigé, laissé
en advisory. À mentionner si pertinent, pas à traiter dans ce chantier ODD sauf demande
explicite.

**Mise à jour 2026-10-01 (worktree `dev_scan`, à reporter dans `dev_hardware`)** : la durée des
*déplacements* est maintenant fidèle. Caractériseur banc
`infrastructure/hardware/arcus_performax_4EX/characterization/` (360 mouvements, modèle
`t = t0 + max(|dx|,|dy|)/v`, synthèse commitée dans `results/`) → constantes nommées dans
`MockMotionPort` (niveau port, exact) et `FakeArcusPerformax4EXController` (niveau contrôleur,
exact ; vu depuis le port, t0 sous-estimé d'environ 0,19 s faute de latence USB simulée). Restent
ouverts :
- `home()` non caractérisé (toujours instantané/0,2 s) ;
- rampe d'accélération en fast (environ 0,1 s d'erreur sur 2,5 mm) ;
- **extrapolé de la mesure** (non mesuré directement, déplacements ≤ 100 mm) : en slow, home → (600, 600) dure environ 35 s, au-delà des 30 s de timeout du scan
  (`wait_for_motion`) et de `ArcusAdapter._internal_wait_until_stopped` (qui publie alors un
  `MotionCompleted` alors que le moteur roule encore). Reproductible en test avec `MockMotionPort`.
- LS=0 et DEC=0 relus sur le contrôleur : le `ls=10`/`dec=300` de `arcus_default_config.json` n'est
  jamais appliqué.

## Config hardware : source unique de vérité (AD9106+MCU fait, ADS131A04 restant)

**Statut** : refonte implémentée pour AD9106 + MCU (2026-09-08, puis corrections et ajout du
lien DDS1-DDS2 le 2026-09-17-18, suite verte — 387 passed, 2 skipped, 1 flaky de timing
préexistant sans rapport). Détail complet dans
`C:\Users\manip\.claude\plans\lively-seeking-backus.md`. Reste à généraliser à l'ADS131A04
(ADC) — voir "Fait vs à faire" ci-dessous.

**Incident post-déploiement corrigé (2026-09-17)** : `AD9106AdvancedConfigurator.apply_config()`
faisait `config.get(f"ch{ch}_gain", 0)` — un dict partiel (envoyé par les tests, pas par l'UI
qui envoie toujours tout) mettait à 0 les canaux non mentionnés dans `ad9106_last_config.json`,
et comme ce fichier est réputé "complet" une fois écrit, `resolve_config()` ne pouvait plus
récupérer les valeurs default perdues. Des tests pré-existants corrompaient donc le **vrai**
fichier de config à chaque run de la suite (pas d'isolation CWD/backup). Corrigé par :
apply_config()/save_config_as_default() font maintenant un vrai read-modify-write contre
l'état résolu ; tous les tests qui appellent apply_config() sauvegardent/restaurent
`ad9106_last_config.json` réel dans setUp/tearDown (pattern déjà utilisé par
`config_persistence_test.py` pour l'ADC — l'ADC a le même risque latent, non traité).

**Fonctionnalité ajoutée (2026-09-18)** : lien DDS1-DDS2 (gain) partagé entre le panel
Excitation ("Link S1-S2 = S3-S4", jusque-là 100% local au widget) et Hardware Advanced
Config (nouveau paramètre `link_dds1_dds2`, persisté, résolu comme le reste). Nouvel event
`ExcitationDdsLinkChanged` (nommé ainsi, pas `DdsLinkChanged` générique, car une notion de
lien différente est prévue pour DDS3/DDS4 phase+fréquence — synchronisation de la détection
synchrone — à ne pas confondre). Enforcement dans `apply_config()` : si lié, un apply qui ne
touche qu'un seul de ch1_gain/ch2_gain (ou les deux avec des valeurs différentes) aligne
l'autre canal avant écriture — élimine la désync à la source, quel que soit le panel
d'origine. Sync bidirectionnelle vérifiée bout-en-bout avec de vrais widgets Qt (headless).

### Le problème (constaté sur AD9106/MCU, mais généralisable)

Chaque hardware configurable (AD9106 DDS, ADS131A04 ADC, MCU n_avg) a deux lecteurs
indépendants de "la config" :
- le panel Hardware Advanced Config lit `*_default_config.json` seul
- le boot réel (`MCUCompositionRoot._load_and_apply_config()`) fusionne
  `*_default_config.json` + `*_last_config.json` avec des règles ad hoc (parfois un
  `dict.update()` superficiel qui écrase des sous-dicts imbriqués entiers, parfois aucune
  fusion du tout)

Résultat déjà observé : le panel affiche une valeur (ex. gain DDS3/4 = 10000, n_avg = 127)
alors que le hardware réel démarre avec une autre valeur (0, ou la dernière valeur
sauvegardée), jusqu'à ce que l'utilisateur clique manuellement sur "Apply".

### Périmètre de la refonte propre (voir le plan pour le détail par fichier)

1. Module partagé `hardware_config_resolution.py` (`resolve_config()` deep-merge pur,
   testé) — remplace les fusions ad hoc dispersées.
2. Convergence sur un **écrivain unique** par hardware : `MCULifecycleAdapter` au boot doit
   appeler le même `apply_config()` que le panel manuel (`AD9106AdvancedConfigurator` pour
   l'AD9106), au lieu de dupliquer une écriture registre séparée qui ne publie pas les
   events de sync (`ExcitationFrequencyChanged`, `DdsChannelConfigChanged`).
3. Les panels (`get_parameter_specs()`) doivent lire l'état résolu (default+last), pas le
   default seul — sinon l'affichage continue de mentir sur ce qui est réellement appliqué.

### Fait vs à faire

- **AD9106 + MCU (n_avg)** : ✅ fait. Nouveau module partagé
  `infrastructure/hardware/micro_controller/hardware_config_resolution.py`
  (`resolve_config()`/`load_json_if_exists()`, testés). `MCULifecycleAdapter` au boot
  délègue à `AD9106AdvancedConfigurator.apply_config()` (écrivain unique — plus de double
  écriture registre, les events `ExcitationFrequencyChanged`/`DdsChannelConfigChanged`
  sont publiés automatiquement). `MCUAdvancedConfigurator.get_parameter_specs()` et
  `AD9106AdvancedConfigurator.get_parameter_specs()` lisent désormais l'état résolu
  (default+last), plus le default seul. Tests ajoutés :
  `_tests/hardware_config_resolution_test.py`,
  `_tests/adapter_lifecycle_MCU_dds_config_test.py` (chemin JSON-driven de `_configure_dds`,
  jusque-là jamais testé), + tests du flatten helper dans
  `ad9106/_tests/ad9106_advanced_configurator_test.py`.
- **ADS131A04 (ADC)** : la fusion default+last de la composition root utilise maintenant
  `resolve_config()` (ferme le risque d'écrasement en bloc de `channels`), mais
  `ADS131A04AdvancedConfigurator.get_parameter_specs()` lit toujours le default seul — **même
  angle mort confirmé mais non corrigé** pour l'affichage panel vs état réellement appliqué. À
  traiter dans une passe suivante (`resolve_config()` + `get_parameter_specs()` sur l'état résolu).
  *Fait 2026-09-25* : écrivain unique ADC (`apply_persisted_config`, appelé par le boot avec
  `persist=False` et par l'Apply), encodage registre seulement dans `ADS131Controller`, un nom
  physique par réglage (`reference_voltage`, `reference_source`, `high_resolution`,
  `negative_charge_pump`) — corrige Vref jamais écrite, bit réservé A_SYS_CFG, OSR mal encodé au
  boot (hors 4096) et OSR jamais écrit à l'Apply.
- Modes AC/DC des DDS (`mode_dds1_dds2`/`mode_dds3_dds4`) : pas de panel, pas de risque de
  désync — volontairement hors scope.
- Pas de vérification read-back des registres (fiabilité hardware) — chantier séparé, plus
  large, non commencé.

## Mesure différentielle (baseline sans excitation + mesure normale)

**Statut** : implémenté en TDD (2026-07-30) — mute()/unmute(), ScanPointResult/events + baseline, boucle différentielle, export CSV, checkbox UI. Suite complète verte (293 passed).

### Principe

À chaque point de scan, en plus de la mesure normale existante (avec excitation), on
acquiert optionnellement une mesure baseline (excitation coupée juste avant) et on
l'associe à la mesure normale. C'est une **extension** : `measurement` (excité) reste
inchangé, on ajoute un champ optionnel `baseline_measurement` à côté.

Le mute/unmute de l'excitation est **électronique** (gain DDS → 0), pas mécanique — son
délai de stabilisation (`differential_settle_delay_ms`) est court et distinct du
`stabilization_delay_ms` moteur existant. Le mute se fait **une seule fois par point**,
partagé entre le canal AEFI primaire et toutes les sondes auxiliaires actives (ex. Narda
EF probe) — ne pas re-toggler l'excitation par canal.

### Fichiers à toucher

- `domain/step_scan/value_objects/scan_point_result/` : `ScanPointResult` + champ optionnel
  `baseline_measurement: AefiVoltageMeasurement | None`
- `domain/step_scan/events/scan_point_acquired/` : `ScanPointAcquired` + champ optionnel
  `baseline_measurement`
- `domain/step_scan/events/electric_field_scan_point_acquired/electric_field_scan_point_acquired.py` :
  + champ optionnel `baseline_field_measurement: FieldMeasurement | None`
- `application/services/excitation_configuration_service/excitation_configuration_service.py` :
  + `mute()` / `unmute()` (gardent mode/fréquence, togglent juste le niveau à 0 puis
  restaurent le niveau précédent)
- `application/services/scan_application_service/scan_application_service.py` :
  - `AuxiliaryProbeChannel.publish_point_result` : signature étendue pour accepter des
    échantillons baseline optionnels (aujourd'hui `Callable[[Any, int, Any, List], None]`,
    l.114)
  - `make_electric_field_probe_channel._publish` (l.124-134) : calculer aussi
    `baseline_field_measurement` si des échantillons baseline sont fournis
  - `_execute_scan_loop` (l.279-479) : restructurer le bloc par point (aujourd'hui
    l.398-442) — si `config.differential_mode` :
    1. `excitation_service.mute()` → délai `differential_settle_delay_ms`
    2. drain + collecte baseline sur `adc_queue` ET chaque `(channel, channel_queue)` de
       `active_channels` (réutilise `_drain_queue`/`_collect_samples` existants)
    3. `excitation_service.unmute()` → délai `differential_settle_delay_ms`
    4. bloc excité existant (l.398-442), inchangé
    5. attacher les baselines aux résultats avant `ScanPointResult(...)` et
       `channel.publish_point_result(...)`
- `application/services/scan_application_service/dtos/scan_dtos.py` : `Scan2DConfigDTO` +
  `differential_mode: bool = False`, + `differential_settle_delay_ms: float`
- `application/services/scan_export_service/scan_export_service.py` (`_flatten_point`) et
  `infrastructure/persistence/csv_scan_export_port.py` (`write_point` + `write_field_point`) :
  + colonnes `baseline_*` (vides si non différentiel)
- UI : case à cocher "Mesure différentielle" dans le panneau de config scan →
  `Scan2DConfigDTO.differential_mode`

Pas de nouveau VO type `DifferentialMeasurement` — le delta (excité − baseline) se calcule
à la volée à l'export/post-traitement, pas stocké dans le domaine.

### Validation déterministe en mode MOCK (important — priorité de ce chantier)

Le mock stack existant simule déjà le couplage excitation↔acquisition et permet de
prouver le mécanisme de mute de façon déterministe, sans hardware :

- `infrastructure/mocks/adapter_mock_i_acquisition_port.py::RandomNoiseAcquisitionPort` —
  bruit gaussien avec `seed` optionnel pour reproductibilité (mettre `noise_std=0.0` pour
  un test 100% déterministe sans bruit).
- `infrastructure/mocks/adapter_mock_i_excitation_port.py::MockExcitationPort` — stocke
  `last_parameters` à chaque `apply_excitation()`.
- `infrastructure/mocks/adapter_mock_excitation_aware_acquisition.py::ExcitationAwareAcquisitionPort` —
  lit `excitation_port.last_parameters` à chaque `acquire_sample()` et applique un offset
  3D déterministe proportionnel au niveau d'excitation (`avg_level/100.0`), **nul quand le
  niveau est à 0** (`DEFAULT_EXCITATION_OFFSET_MAP`, l.88-94 et check `avg_level > 0`,
  l.163). C'est exactement le point qui prouve que le mute fonctionne : offset=0 pendant
  la fenêtre mutée, offset≠0 pendant la fenêtre normale.
- Wiring de référence : `src/main.py::main()` (branches `hardware_config["aefi_device"] ==
  "mock"`) — c'est ainsi que ces trois mocks sont déjà composés ensemble. Lancer
  `src/main_mock.py` pour ce mode sans éditer `main.py` (le launcher réel ne doit pas
  dépendre des mocks).

Test à écrire (application ou scan_application_service niveau intégration, avec les
fakes) : construire ce même stack (`RandomNoiseAcquisitionPort(noise_std=0.0, seed=...)`
→ `ExcitationAwareAcquisitionPort` → `MockExcitationPort`), lancer un scan en mode
différentiel sur au moins un point, puis vérifier :
1. `baseline_measurement` du point == mesure brute sans offset (puisque `mute()` doit
   avoir mis le niveau à 0 avant l'acquisition baseline)
2. `measurement` (excité) == mesure brute + offset attendu du mode d'excitation configuré
3. la différence `measurement - baseline_measurement` reconstruit exactement le vecteur
   d'offset attendu (avec `noise_std=0.0`, égalité exacte ; sinon tolérance sur la moyenne
   après `averaging_per_position` échantillons)

C'est le test qui valide que le cycle mute→collecte→unmute→collecte fonctionne de bout en
bout dans `ScanApplicationService`, sans dépendre du hardware réel.

### Ordre TDD suggéré

1. `ExcitationConfigurationService.mute()/unmute()` + tests unitaires
2. `ScanPointResult` + `baseline_measurement` (VO/entité, tests domain)
3. `ScanApplicationService` : test d'intégration avec le mock stack ci-dessus (le test qui
   compte le plus — voir section précédente) avant de coder la boucle
4. Implémentation de la boucle différentielle
5. Events (`ScanPointAcquired`, `ElectricFieldScanPointAcquired`) + export CSV
6. UI (case à cocher)
