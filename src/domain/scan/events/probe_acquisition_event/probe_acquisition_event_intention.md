# probe_acquisition_event — Intention

## Rationale

Sans contrat commun, le handler de clôture doit connaître la forme de chaque événement d'acquisition (`aefi_point_id`, puis l'identifiant d'une ligne, puis celui d'une mesure Narda), ce qui signifie un `if` par capteur, ce qui force à modifier le handler à chaque sonde ajoutée.

## Responsibility

- Dire ce que tout événement « une acquisition d'une sonde est faite » expose au `Scan` : `scan_id`, `source` (nom de la source déclarée au `Scan`) et `acquisition_id`.

## Design

- `Protocol` structurel `runtime_checkable` : les événements des agrégats émetteurs le respectent sans l'importer (le domaine émetteur ne dépend pas du `Scan`).
- `source` est une constante de l'agrégat émetteur (p.ex. `"aefi_point"`).
