---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 1]]"
doc_type: constat
tldr: "Les lots 9 à 20 sont hors de la vague 1 : leur geste change la logique d'un .py (construction et injection des adaptateurs, Fakes à la place des réels, signatures des cas d'usage), pas seulement un nom, une place ou une annotation."
---

# Lots 9 à 20 sautés : le geste change le code

**Sautés, sans aucun changement.** La vague 1 ne prend que les renommages, déplacements, annotations et frontmatters.

- **Lots 9 et 10**, `solidai-adaptateur-construit-hors-composition` (51 erreurs) : retirer la construction d'un réel et le faire injecter par le point de composition. Le câblage change.
- **Lots 11 à 15**, `solidai-test-applicatif-importe-un-reel` (178 erreurs) : remplacer un réel par son Fake dans un test. Le test change, et beaucoup de ports n'ont pas encore de Fake typé (`solidai-port-sortant-sans-fake`, 46 erreurs).
- **Lots 16 à 20**, `solidai-dto-non-gele` (107 erreurs) : la table des gestes dit « geler le DTO », mais toutes les erreurs de ces lots sont l'autre moitié de H8, « the use case … does not take one DTO of dtos/ ». Le geste réel est de changer la signature de chaque cas d'usage pour qu'il prenne un DTO, puis ses appelants et ses tests. Aucune de ces 107 erreurs ne se corrige par `frozen=True`.

Le tri range les lots 16 à 20 en mécaniques parce que la table des gestes ne distingue pas les deux variantes de `solidai-dto-non-gele`.
Une ligne de variante (`dto-non-gele (cas-d-usage-sans-dto)` → jugement) dans `table-des-gestes.tsv` les sortirait des mécaniques.
