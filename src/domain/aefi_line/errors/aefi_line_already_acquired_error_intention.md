# aefi_line_already_acquired_error — Intention

## Rationale

Sans ce refus, une seconde tentative écraserait les points d'une ligne déjà publiée via `AefiLineAcquired`, ce qui signifie un fait publié qui ne correspond plus à l'état, ce qui force les consommateurs à se méfier de chaque événement.

## Responsibility

- Nommer la promesse refusée : une ligne acquise est figée.

## Design

- Hérite de `ValueError`, comme `AefiPointAlreadyAcquiredError`.
