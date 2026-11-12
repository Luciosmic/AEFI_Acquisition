---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 1]]"
doc_type: constat
tldr: "Les 8 erreurs solidai-valeur-mutable d'ACQ sont des faux positifs : 6 Enum, un Protocol et une ABC, déjà immuables ou sans état. Le geste @dataclass(frozen=True) casserait les Enum ; la vérification D5 doit les exempter."
---

# Lots 21 et 22 sautés : `solidai-valeur-mutable` signale des classes déjà immuables

**Sautés, sans aucun changement.** Appliquer `@dataclass(frozen=True)` changerait le comportement, et l'erreur est fausse.

| Classe | Fichier sous `src/domain/` | Nature |
|---|---|---|
| `FrequencySweepRole` | `frequency_sweep/value_objects/frequency_sweep_role/frequency_sweep_role.py` | `Enum` |
| `ScanState` | `scan/value_objects/scan_state/scan_state.py` | `Enum` |
| `ParameterType` | `shared_kernel/value_objects/hardware_configuration/hardware_advanced_parameter_schema.py` | `Enum` |
| `ScanAxis` | `step_scan/value_objects/scan_axis/scan_axis.py` | `Enum` |
| `ScanPattern` | `step_scan/value_objects/scan_pattern/scan_pattern.py` | `Enum` |
| `ScanStatus` | `step_scan/value_objects/scan_status/scan_status.py` | `Enum` |
| `ProbeAcquisitionEvent` | `scan/events/probe_acquisition_event/probe_acquisition_event.py` | `Protocol` (`@runtime_checkable`) |
| `IDomainEventBus` | `shared_kernel/events/i_domain_event_bus.py` | `ABC`, une interface |

Un membre d'`Enum` est déjà immuable, et `@dataclass` sur un `Enum` change son comportement.
Un `Protocol` et une `ABC` ne portent pas de valeur.

La vérification D5 (`solidai-valeur-mutable`, solidai-ddd) devrait exempter les classes qui héritent d'`Enum`, de `Protocol` ou d'`ABC`.
Une fois corrigée, ces 8 erreurs disparaissent sans toucher à ACQ.
