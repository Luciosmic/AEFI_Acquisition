# driver_narda_ep601 — Intention

## Rationale

Wrapper bas-niveau autour du protocole série propriétaire de la sonde Narda EP-601. Isole les échanges `pyserial` et le décodage des trames binaires dans une seule classe pour que les adaptateurs exposent une API Python propre sans manipuler directement les octets du protocole.

La sonde démarre en **mode Master** (spam continu d'un beacon d'identification ~1×/s, cf. sous-projet) et ne bascule en mode Slave (query/réponse, requis pour le polling) que sur commande explicite (`?v`) — et ce beacon peut recouvrir n'importe quel échange série de façon transitoire. Le driver doit donc être robuste au polling continu sans intervention de l'appelant : forcer et confirmer le mode Slave à la connexion, absorber la corruption transitoire de trame par des ré-essais bornés, sans jamais masquer une sonde réellement éteinte.

## Responsibility

- Ouvrir/fermer la liaison série (`connect`/`disconnect`, utilisable en context manager). `connect()` force et confirme le passage en mode Slave par défaut (`auto_slave_mode=True`) — `False` réservé aux scripts de diagnostic bas-niveau qui doivent observer l'état brut avant bascule.
- Envoyer les commandes `#00?v*`, `#00?s*`, `#00?b*`, `#00?T*`, `#00?A*`, `#00e <n>*`, `#00k <fr>*` et décoder/valider les réponses correspondantes (version, numéro de série, tension batterie, champ total, champ par axe, délai auto-off, correction fréquentielle).
- Reproduire côté client le moyennage arithmétique (le protocole série n'a pas de mode "Average" — celui-ci n'existe que côté GUI/DLL WinEP600).
- Lever `NardaProbeTimeout` sur absence de réponse (sonde éteinte par auto-off ou déconnectée) plutôt que de laisser fuiter une erreur `serial` générique — **jamais** retenté automatiquement (retenter une sonde éteinte ne fait que tripler l'attente, cf. `narda-ep60x_allumage-extinction-led.md` : aucune commande de réveil à distance).
- Retenter automatiquement (borné par `retries`, défaut 4) une trame malformée (`IOError` — recouvrement transitoire par le beacon Master) avant de la remonter à l'appelant.
- Exposer un hook optionnel `on_raw` (callable appelé à chaque échange série, succès ou échec) pour la journalisation détaillée sans changer le comportement par défaut — voir `characterize_narda.py` dans le sous-projet pour un exemple d'usage complet.

## Design

- **Couche driver pure** : pas de logique domain, pas de publication d'événements.
- Protocole documenté et validé sur banc dans le sous-projet externe `Ressources/ExperimentalData_ASSOCE/Narda-electric-field-probe-acquisition` (voir `notes-narda-electric-field-probe-acquisition/sources/narda-ep60x_protocole-communication.md` et `.../narda-ep60x_allumage-extinction-led.md`).
- Consommé par `adapter_electric_field_probe_port.py` (`NardaEP601ProbeAdapter`, implémentation de `IElectricFieldProbePort`). **Lacune connue** : `acquire_sample()` de cet adaptateur ne catch pas `NardaProbeTimeout`/`IOError` — une acquisition manquée (même après épuisement des ré-essais du driver) remonte donc telle quelle à l'appelant plutôt que d'être gérée explicitement par la boucle de polling. Pas corrigé ici (hors périmètre du driver), à traiter côté adaptateur/service applicatif.
- `IOError` est un **alias d'`OSError`** en Python 3, et `TimeoutError` (dont hérite `NardaProbeTimeout`) est une sous-classe d'`OSError` — tout `except IOError` dans ce module (et dans tout code appelant) doit explicitement `except NardaProbeTimeout: raise` AVANT, sous peine de retenter silencieusement une sonde éteinte (bug réel rencontré et corrigé le 2026-07-23, cf. self-check `test_driver_raw_log.py` du sous-projet et `_tests/driver_narda_ep601_test.py::TestNardaEP601SlaveModeAndRetries`).
