---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_serial_link` : Rendre une latence fixée pour un port donné (COM10 par défaut)."
code: ["[[src/infrastructure/hardware/serial_link/fake/fake_serial_link.py]]"]
cause_de_changement: outil
implements: ["[[src/application/shared/acquisition_parameters/i_usb_latency_timer_port_intention]]"]
double_de: "[[src/infrastructure/hardware/serial_link/serial_link_intention]]"
---
# fake_serial_link — Intention

## Rationale

Le lecteur réel lit le registre Windows de la machine : un test applicatif
qui en dépendrait passerait ou échouerait selon le poste (FTDI branché ou
non, latence réglée à 1 ou 16 ms) et ne pourrait pas reproduire un registre
illisible.

## Responsibility

- Rendre une latence fixée pour un port donné (COM10 par défaut).
- Mêmes échecs que le réel : port inconnu, ou `failure` imposé (registre
  illisible, autre OS).

## Design

- Vérification d'état (`requested_ports`).
- Réponse instantanée : le réel est une lecture de registre locale, aucune
  régulation n'en dépend.
