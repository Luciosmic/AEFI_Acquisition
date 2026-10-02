# acquisition_throughput_characterization — Intention

## Rationale

Le moyennage MCU (`n_avg`) arbitre entre deux pertes : trop petit, le coût
fixe de chaque aller-retour série domine et la plupart des conversions de
l'ADC sont perdues entre deux requêtes ; trop grand, la cadence de sortie
s'effondre sans gain de bruit par seconde de mesure. Sans un objet qui porte
la mesure de ce compromis, le choix de `n_avg` reste « de mémoire », et une
caractérisation refaite ne peut pas être comparée à la précédente.

## Responsibility

- `AcquisitionThroughputPoint` : pour un `n_avg`, la période moyenne par
  échantillon renvoyé, le débit d'échantillons, le débit de conversions ADC
  utilisées (`n_avg / période`), le bruit σ par voie (6 voies, ordre
  x/y/z en phase puis quadrature), leur moyenne quadratique `σ_rms`, et le
  bruit atteignable en 1 s
  (`σ_rms · √période`).
- `AcquisitionThroughputCharacterization` : les points, le modèle ajusté
  `T(n) = T₀ + n / ODR` (coût fixe `overhead_s`, cadence ADC
  `adc_output_rate_hz`, `None` si la pente n'est pas positive), l'écart
  relatif max au modèle (la non-linéarité éventuelle), et le `n_avg`
  recommandé.

## Design

- `@dataclass(frozen=True)`, aucune logique : construits et testés via
  `services/acquisition_throughput_analysis/`.
- Grandeurs en unités SI (s, Hz, V) ; la présentation (ms, µV) est faite par
  l'interface.
