# dds_channel_config_changed — Intention

## Rationale

Mirror of `excitation_frequency_changed`, but for gain and phase: the
Hardware Advanced Config tab and the Excitation panel both write to the same
shared `AD9106Controller` (channels 1/2), through two different adapters
(`AdapterExcitationConfigurationAD9106` for the Excitation panel,
`AD9106AdvancedConfigurator` for the Hardware Config tab). Frequency already
had this sync (`ExcitationFrequencyChanged`, published from the Hardware
Config side); this event closes the same gap in the other direction — for
level (-> gain) and mode (-> phase) — published from
`AdapterExcitationConfigurationAD9106.apply_excitation()`, since that's
where the domain->hardware-units conversion already happens (avoids
duplicating `MAX_EXCITATION_GAIN`/phase-mapping constants in the interface
layer).

## Responsibility

- Signal that channel `channel`'s (1 or 2) actual DDS gain and/or phase
  register value changed as a result of `apply_excitation()` — carries
  hardware units directly (gain: 0-5500, phase: 0-65535), not domain
  percentages, so consumers (e.g. the Hardware Config tab) don't need to
  know the conversion formula.
- Published once per channel whenever that channel's gain or phase was
  actually written this call (including the "full OFF" path, which zeroes
  both).

## Design

- `@dataclass(frozen=True)` inheriting `DomainEvent`.
- `channel: int` (1 or 2), `gain: int`, `phase: int` — always both, even if
  only one of the two was touched this call, so a consumer always gets a
  complete per-channel snapshot rather than having to merge partial updates.
- Topic of publication: `"ddschannelconfigchanged"`.
