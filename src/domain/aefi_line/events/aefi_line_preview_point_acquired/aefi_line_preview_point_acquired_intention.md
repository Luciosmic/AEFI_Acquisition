# aefi_line_preview_point_acquired — Intention

## Rationale

Une `AefiLine` est atomique : ses points ne sont publiés (`ScanPointAcquired`) qu'une fois la ligne complète, et la ligne peut être abandonnée. Sans signal provisoire, l'opérateur ne verrait rien de la carte pendant des dizaines de secondes de balayage. Publier les points définitifs en direct ferait écrire à l'export des points d'une ligne ensuite abandonnée.

## Responsibility

- Fait **provisoire** : un point de grille vient d'être placé sur la ligne en cours de balayage (scan, rang de la ligne, rang dans la ligne, position, mesure).
- Réservé à l'aperçu de l'interface. L'export et les compteurs de progression l'IGNORENT ; les `ScanPointAcquired` définitifs, publiés au commit, écrasent l'aperçu.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`. Topic : `"aefilinepreviewpointacquired"`.
- Publié par le service applicatif pendant le balayage, pas par l'agrégat `AefiLine` (qui n'existe pas encore) : ce n'est pas un fait de l'agrégat.
