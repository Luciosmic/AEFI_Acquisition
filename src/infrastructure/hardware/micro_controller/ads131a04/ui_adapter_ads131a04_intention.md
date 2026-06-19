# ui_adapter_ads131a04 — Intention

## Rationale

Adaptateur spécialisé pour l'affichage UI des données ADS131A04 en temps réel (oscilloscope). Séparer cet adaptateur UI des adaptateurs d'acquisition pure permet d'ajouter des transformations de visualisation (mise à l'échelle, filtre) sans impacter l'acquisition.

## Responsibility

- Adapter les données ADS131A04 brutes pour l'affichage dans les widgets UI (ex. panneau acquisition continue).
- Gérer le format d'affichage (plage, unités affichées).

## Design

- Adaptateur dédié UI — pas utilisé dans les chemins critiques d'acquisition.
