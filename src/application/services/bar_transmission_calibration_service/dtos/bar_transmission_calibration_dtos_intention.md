# bar_transmission_calibration_dtos — Intention

## Rationale

L'interface ne doit pas importer le domaine (ni `EdgeBracket`, ni
`AxisBarTransmissionMeasurement`). Sans DTO, le panneau recevrait soit des objets du
domaine, soit des tuples dont le sens (incréments ? millimètres ? demi-largeur ou
largeur ?) ne serait porté que par la position.

## Responsibility

- `BarCalibrationSettingsDTO` : réglages surchargeables depuis l'interface, avec leurs
  valeurs initiales nommées (à ajuster sur le banc).
- `LidarDistanceReading` : une distance horodatée à sa réception (sortie du port LIDAR).
- `ProfilePointDTO`, `CoarseLocalizationDTO`, `RestPointDTO`, `FrontBracketDTO` : le
  tracé en direct (points du fly scan, seuil et fronts approximatifs, points lus à
  l'arrêt avec leur classement `on_bar` / `off_bar` / `undecidable`, encadrement
  courant d'un front).
- `EdgeBracketDTO`, `AxisBarTransmissionDTO` : la mesure d'un axe, encadrements,
  N ± δ, transmission ± incertitude, plateaux et seuil.
- `BarTransmissionMeanDTO` : moyenne X/Y, incertitude, écart, compatibilité, et
  l'identifiant de l'entrée une fois enregistrée.

## Design

- `@dataclass(frozen=True)` ; unités dans les noms de champs et dans l'en-tête du
  module (incréments moteur, mm, s, incréments/s).
- `AxisBarTransmissionDTO` contient tout ce qu'il faut pour reconstruire la mesure
  du domaine : `record(x, y)` reçoit les DTO affichés, pas un état caché du service.
