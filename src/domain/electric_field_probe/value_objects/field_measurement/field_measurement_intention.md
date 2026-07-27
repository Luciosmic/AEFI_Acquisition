# field_measurement — Intention

## Rationale

Représenter une mesure de champ électrique en V/m, pour un nombre d'axes
variable (mono/bi/tri-axial), sans porter aucune notion d'in-phase/quadrature
— ce concept est propre au contexte `aefi_device` (`AefiVoltageMeasurement`), pas
à une sonde de champ électrique générique.

## Responsibility

- Stocker les composantes mesurées (`components`, en V/m) et l'horodatage.
- Exposer la norme du champ (`norm`), calculée à la volée pour ne jamais
  désynchroniser une valeur stockée des composantes qui la définissent.

## Design

- `@dataclass(frozen=True)` : immuable, sans identité — value object pur.
- `components: Tuple[float, ...]` plutôt que des champs `x`/`y`/`z` fixes :
  la longueur du tuple porte la dimensionnalité de la sonde (voir
  `ElectricFieldProbe.axis_labels`), pas une hypothèse figée à 3 axes.
- Seule `ElectricFieldProbe.record_measurement` construit une instance
  (garantit l'invariant de dimensionnalité) — pas de constructeur public
  alternatif dans le code applicatif.
