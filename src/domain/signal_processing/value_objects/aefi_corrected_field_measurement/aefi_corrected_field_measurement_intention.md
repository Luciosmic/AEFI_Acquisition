# aefi_corrected_field_measurement — Intention

## Rationale

Après `AefiSignalCorrectionService.apply` et `TransformationService.transform_sensor_to_source`, la grandeur n'est plus une tension par canal capteur (`AefiVoltageMeasurement`, repère X/Y/Z du capteur) mais une composante de champ dans le repère sources. Réutiliser `AefiVoltageMeasurement` pour cette valeur transformée masquerait le changement de repère et de sémantique physique derrière un type qui porte encore le nom "voltage" et les commentaires "repère capteur" — un lecteur du domaine ne pourrait plus distinguer les deux étapes du pipeline par le type seul.

## Responsibility

- Stocker les 6 composantes de champ (en volts, mêmes unités que `AefiVoltageMeasurement`, repère sources) : `field_x_in_phase`, `field_x_quadrature`, `field_y_in_phase`, `field_y_quadrature`, `field_z_in_phase`, `field_z_quadrature`.
- Garder l'horodatage de l'échantillon d'origine.
- Garantir la finitude des 6 composantes à la construction (même garde que `AefiVoltageMeasurement`).

## Design

- `@dataclass(frozen=True)` : immuable, même patron que `AefiVoltageMeasurement`.
- `__post_init__` rejette NaN/Inf sur les 6 composantes.
- Payload de l'event `AefiCorrectedFieldSampleAcquired`.
