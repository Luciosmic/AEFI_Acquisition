# spectral_analysis_result — Intention

## Rationale

Le résultat d'une analyse spectrale (fréquences + amplitudes par canal) doit être un fait immuable que `SpectralAnalysisCalculator` retourne et que `SpectralAnalysisResultUpdated` transporte — sans ce type, le calcul retournerait un tuple ou dict ad hoc, perdant la traçabilité de la fenêtre temporelle (début/fin, nombre d'échantillons) qui donne son contexte au spectre.

## Responsibility

- Porter les fréquences (Hz) et l'amplitude par canal (mêmes clés que `AefiContinuousReadingPanel.CHANNELS`), ainsi que la fenêtre temporelle (début, fin, nombre d'échantillons) ayant produit ce spectre.

## Design

- `@dataclass(frozen=True)` : immuable, value object simple sans invariant propre (la validité du contenu est garantie par `SpectralAnalysisCalculator`, pas par ce type).
