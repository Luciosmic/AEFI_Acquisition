# fake_mcu_serial_communicator — Intention

## Rationale

Le mode "mock" de l'app construisait jusqu'ici des doubles bas-de-gamme
(`infrastructure/mocks/adapter_mock_i_excitation_port.py`, etc.) qui court-
circuitent tout le code réel — résultat : en mock, l'onglet Hardware Config
n'affiche même pas l'AD9106, et rien du câblage réel (dont la synchro
fréquence Hardware Config ↔ Excitation) n'est vérifiable sans le vrai banc.

`MCU_SerialCommunicator` ne se connecte jamais tout seul (`__init__` ne fait
rien) et `send_command()` renvoie déjà gracieusement `(False, "Not connected")`
si `.connect()` n'a jamais été appelé — sans exception. Les tests AD9106
exploitent déjà ce fait (`patch.object(MCU_SerialCommunicator, 'send_command',
return_value=(True, "OK"))` + vrai `AD9106Controller`). Ce Fake généralise la
même idée pour une utilisation "app réelle", pas seulement des tests.

## Responsibility

- Implémenter le même contrat que `MCU_SerialCommunicator` :
  `connect()`, `disconnect()`, `send_command(cmd) -> (bool, str)`.
- Laisser tourner sans modification `AD9106Controller`, `ADS131Controller`,
  `ADS131A04Adapter`, `AdapterExcitationConfigurationAD9106`,
  `AD9106AdvancedConfigurator`, `ADS131A04AdvancedConfigurator`,
  `AdapterAefiAcquisitionAds131a04` — seul le transport change.
- Simuler une réponse plausible pour la commande d'acquisition ADS131
  (`m<n>*`) : ≥6 codes 24-bit signés séparés par tabulation, seul format dont
  le contenu est réellement parsé côté adaptateur.
- Introduire un délai réaliste (`acquisition_delay_s`, défaut 10ms/100Hz) sur
  cette même commande `m<n>*`. Incident constaté : `AdapterAefiAcquisitionAds131a04`
  (acquisition continue) n'a **aucun** pacing logiciel — il compte
  explicitement sur le round-trip ADC réel pour s'autoréguler. Sans ce délai,
  la boucle continue tourne à vide en quelques millisecondes et inonde
  l'event bus / le thread Qt principal, plantant l'app peu après le démarrage
  de l'acquisition continue. 1ms (1kHz) testé d'abord, encore trop rapide
  pour l'UI en pratique — 10ms est le nouveau défaut.

## Design

- Pas de threading, pas d'I/O — état interne minimal (`_connected: bool`).
- Pas de couplage physique excitation→bruit simulé ici (ponytail : ce
  couplage existe déjà, une couche plus haut, dans
  `ExcitationAwareAcquisitionPort` — pas besoin de le dupliquer au niveau
  registre).
