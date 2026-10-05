# ftdi_usb_latency_timer_reader — Intention

## Rationale

Le MCU parle à l'hôte par un pont USB-série FTDI. Le pilote Windows retient
chaque octet jusqu'à `LatencyTimer` ms avant de l'envoyer : sur le banc,
T₀ (coût fixe par échantillon) valait 23,6 ms avec 16 ms et 7,6 ms avec
1 ms. Ce réglage vit dans le registre Windows, hors de l'application ; s'il
n'est pas lu, deux balayages de débit faits à des latences différentes
paraissent contradictoires sans qu'on puisse dire pourquoi (cas du
2026-10-02, reconstitué à la main).

Le pont identifié sur le banc est un **FT232R** (PID USB `0403:6001`, lu
dans `FTDIBUS\COMPORT&VID_0403&PID_6001`), une puce **USB Full-Speed
uniquement** (pas de micro-trame, contrairement aux FT2232H/FT4232H/FT232H
Hi-Speed). La trame Full-Speed impose un plancher physique de 1 ms :
`LatencyTimer=1ms` est donc déjà le minimum atteignable sur cette puce, pas
un réglage sous-optimal. Voir `_system/documentation/adr/003_latency_budget_acquisition_chain.md`.

## Responsibility

- Implémenter `IUsbLatencyTimerPort` : pour un port série (`COM10`),
  trouver le périphérique FTDI dont `PortName` est ce port et rendre sa
  valeur `LatencyTimer` (ms).
- Tout échec (autre OS, pont non FTDI, port absent, registre illisible) →
  `OperationResult.fail` avec la raison, jamais d'exception.

## Design

- Registre : `HKLM\SYSTEM\CurrentControlSet\Enum\FTDIBUS\<périphérique>\0000\Device Parameters`
  (valeurs `PortName`, `LatencyTimer`), bibliothèque standard `winreg`.
- La valeur lue est celle **configurée** ; le pilote l'applique à
  l'ouverture du port (le document le dit dans `usb_latency_timer_source`).
- L'énumération du registre est injectable : les tests passent une liste de
  périphériques, aucun test ne dépend du registre de la machine.
- Log : une ligne par lecture (port, périphérique, valeur) ou par échec.
