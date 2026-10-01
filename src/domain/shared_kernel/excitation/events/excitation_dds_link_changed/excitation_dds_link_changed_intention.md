# excitation_dds_link_changed — Intention

## Rationale

The Excitation panel's "Link S1-S2 = S3-S4" checkbox used to be purely local
UI state — it mirrored the two level spinboxes client-side but had no
existence outside that one widget. Changing a single channel's gain from the
Hardware Advanced Config tab could silently desynchronize the pair, and
neither panel would know the other's link preference. This event is the
excitation-specific DDS1/DDS2 gain link's sync channel, named distinctly from
a generic "DdsLinkChanged" because DDS3/DDS4 are expected to grow their own,
different link concept later (phase/frequency linking for synchronous
detection dephasing) — a generic name would not carry that distinction.

## Responsibility

- Signal that the DDS1/DDS2 gain link flag (`link_dds1_dds2`) actually
  changed, from either write path: `AD9106AdvancedConfigurator.apply_config()`
  (Hardware Advanced Config tab) or
  `AdapterExcitationConfigurationAD9106.set_link_dds1_dds2()` (Excitation
  panel).
- Published once per actual change (guarded against re-publishing an
  unchanged value), so both panels stay reconciled to one shared boolean.

## Design

- `@dataclass(frozen=True)` inheriting `DomainEvent`.
- `linked: bool` — the new state.
- Topic of publication: `"excitationddslinkchanged"`.
