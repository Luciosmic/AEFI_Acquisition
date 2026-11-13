---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 3]]"
doc_type: constat
date: 2026-11-13
---

# Le lot des doubles de `infrastructure/mocks/` n'est pas fait, deux doubles restent à discuter

**Lot non pris dans cette vague.** La consigne le plaçait en dernier, seulement si les lots de jugement 3 et 4 (réels et Fakes sous `hardware/<appareil>/`) étaient faits : ils ne le sont pas, et les doubles vont sous le `fake/` de ces réels. La piste de réel par double reste celle de `constat-lot-mocks-demande-un-choix-de-reel-par-mock.md`.

## À discuter

1. `adapter_mock_excitation_aware_acquisition` : double composite de `IAcquisitionPort` et de `IExcitationPort`, sans réel unique. Il reste en place. Choix : le garder comme outil de test hors de `mocks/` (par exemple dans le `_tests/` de ses 3 importeurs), ou le découper en un Fake par port.
2. `adapter_mock_i_export_port` : aucun import hors de son dossier, donc candidat à la suppression. Il reste en place.

Les deux simulateurs physiques (`cube_sensor_field_simulator.py`, `point_charge_field_simulator.py`) ne bougent pas.
