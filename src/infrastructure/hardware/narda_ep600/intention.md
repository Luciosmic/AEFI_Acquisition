# narda_ep600 — Adaptateur Sonde de Champ Électrique

## Rationale
Ce module implémente la communication avec la sonde de champ électrique isotrope Narda EP-601 (via convertisseur série 8053-OC), utilisée comme référence de mesure indépendante du banc de scan AEFI. Le protocole série a été documenté et validé sur banc dans le sous-projet externe `Ressources/ExperimentalData_ASSOCE/Narda-electric-field-probe-acquisition` avant d'être porté ici.

## Responsibility
- `NardaEP601` (`driver_narda_ep601.py`) : encapsuler le protocole série bas-niveau `#AAQcommande(params)*` (adresse broadcast "00", 9600-8N1) — version firmware, numéro de série, tension batterie, champ total isotrope, champ par axe (X/Y/Z), et moyennage côté client.

## Design
- **Couche driver pure** : pas de logique domain, pas de publication d'événements — aucun adaptateur `I*Port` ni `IHardwareInitializationPort` n'existe encore au-dessus de ce driver.
- Auto-off de la sonde après 180 s d'inactivité (réglable via `#00en*`) — un timeout de lecture série est traduit en `NardaProbeTimeout` explicite plutôt que de remonter une erreur `serial` brute.
