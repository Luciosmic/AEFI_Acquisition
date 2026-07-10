# driver_narda_ep601 — Intention

## Rationale

Wrapper bas-niveau autour du protocole série propriétaire de la sonde Narda EP-601. Isole les échanges `pyserial` et le décodage des trames binaires dans une seule classe pour que les futurs adaptateurs puissent exposer une API Python propre sans manipuler directement les octets du protocole.

## Responsibility

- Ouvrir/fermer la liaison série (`connect`/`disconnect`, utilisable en context manager).
- Envoyer les commandes `#00?v*`, `#00?s*`, `#00?b*`, `#00?T*`, `#00?A*` et décoder les réponses binaires correspondantes (version, numéro de série, tension batterie, champ total, champ par axe).
- Reproduire côté client le moyennage arithmétique (le protocole série n'a pas de mode "Average" — celui-ci n'existe que côté GUI/DLL WinEP600).
- Lever `NardaProbeTimeout` sur absence de réponse (sonde éteinte par auto-off ou déconnectée) plutôt que de laisser fuiter une erreur `serial` générique.

## Design

- **Couche driver pure** : pas de logique domain, pas de publication d'événements.
- Protocole documenté et validé sur banc dans le sous-projet externe `Ressources/ExperimentalData_ASSOCE/Narda-electric-field-probe-acquisition` (voir `notes-narda-electric-field-probe-acquisition/sources/narda-ep60x_protocole-communication.md`).
- Pas encore consommé par un adaptateur `I*Port` — ce driver est actuellement autonome (`demo()` en `__main__` pour test manuel sur banc).
