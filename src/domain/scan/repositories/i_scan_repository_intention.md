# i_scan_repository — Intention

## Rationale

Sans port de persistance, le handler de clôture dépendrait d'un stockage concret, ce qui signifie un domaine non testable sans infrastructure.

## Responsibility

- Contrat `add` / `get` de l'agrégat `Scan`.

## Design

- ABC pure ; `get` retourne `None` si inconnu (le handler décide quoi en faire).
