# i_usb_latency_timer_port — Intention

## Rationale

Le coût fixe par échantillon T0 est dominé par le timer de latence du pont
USB-série FTDI : 23,6 ms avec 16 ms, 7,6 ms avec 1 ms (banc, 2026-10-02).
C'est un réglage du pilote Windows, hors de l'application : rien dans le code
ne le connaît. Sans ce port, un résultat de débit ne dit pas sous quelle
latence il a été mesuré, et deux balayages ne sont pas comparables ; le lire
depuis le service mettrait du registre Windows dans la couche application.

## Responsibility

- `read_latency_timer_ms(serial_port)` : la latence configurée pour le port
  série donné, en ms, ou un échec lisible.

## Design

- ABC pure, port sortant.
- Implémentations : `FtdiUsbLatencyTimerReader` (registre Windows, pilote
  FTDI), `FakeUsbLatencyTimerPort` (tests).
- Échec attendu, jamais d'exception : autre OS, pont non FTDI, port absent du
  registre, accès refusé. L'appelant le déclare inconnu dans le document.
