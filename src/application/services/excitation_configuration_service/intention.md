# Excitation Configuration Service

## Rationale
Ce service applicatif expose la configuration du champ d'excitation électromagnétique (mode, fréquence, niveau) à l'interface utilisateur. Il traduit les paramètres UI en valeurs objet domaine avant de les transmettre au port hardware.

## Responsibility
- Appliquer une configuration d'excitation (mode, niveau en %, fréquence en Hz) via `IExcitationPort`.
- Construire les valeurs objets domaine `ExcitationLevel` et `ExcitationParameters` à partir des paramètres bruts.
- Mémoriser la configuration courante pour permettre sa lecture (`get_current_parameters`).

## Design
- Dépend uniquement de `IExcitationPort`, injecté au constructeur.
- L'état courant est initialisé à `ExcitationParameters.off()` pour garantir un démarrage sans excitation.
- La validation des contraintes domaine (`ExcitationLevel` : 0–100 %) est déléguée aux valeurs objets.
