# sphere_id — Intention

## Rationale

L'identité et la position physique des 4 sphères d'excitation (S1-S4) n'existaient
qu'en `str` ad-hoc éparpillées dans les widgets UI (`"S1"`, `"out3"`...) et dans
`position_visualizer.py`. Le domaine ne modélisait pas cette réalité — seul le
hardware (adaptateur AD9106) savait quel canal DDS pilote quoi. Première brique
pour faire remonter cette réalité physique dans le domaine.

## Responsibility

- Identifier une sphère (S1-S4) et son quadrant physique (`x_sign`, `y_sign`).
- Exposer sa paire électronique (S1↔S2, S3↔S4), le générateur DDS physique qui
  la pilote (`dds_channel`), et si elle porte la sortie directe ou
  complémentaire de ce générateur (`is_direct_output`).

## Design

- `Enum` (pas `@dataclass`) — ensemble fermé de 4 valeurs, chacune portant son
  quadrant via `__init__`.
- Convention de quadrant identique à `position_visualizer.py`
  (`src/interface/widgets/motion/position_visualizer.py`) : ne pas dupliquer
  une autre convention.
- Câblage confirmé à l'oscilloscope (2026-07-30), source de vérité historique
  = note "Correspondance Poupette Sortie DDS" (vault thèse de l'utilisateur,
  non versionnée dans ce repo) : **générateur DDS1 → S3 (comp.) / S4 (direct)**,
  **générateur DDS2 → S1 (comp.) / S2 (direct)** — contre-intuitif, ne pas
  supposer "channel N pilote SN".
