# expected_source — Intention

## Rationale

Sans déclaration de ce qu'une source doit fournir, le `Scan` ne peut savoir quand il est complet qu'en connaissant chaque capteur, ce qui signifie qu'ajouter une sonde modifie l'agrégat, ce qui force le `Scan` à dépendre de l'AEFI, de la Narda et de tout capteur futur.

## Responsibility

- Dire combien d'acquisitions une source doit fournir (`count >= 1`) et si elle conditionne la complétion (`required`, vrai par défaut).
- Une source facultative est enregistrée par le `Scan` mais ne retarde pas sa complétion.

## Design

- `@dataclass(frozen=True)` : immuable, défini par sa valeur.
- Le nom de la source (clé du mapping du `Scan`) est une constante de l'agrégat émetteur, pas du `Scan`.
