# bench_configuration — Intention

## Rationale

La racine `Calibration` portait deux choses qui ne changent pas pour la même raison : les règles de calibration (capteur, géométrie des sources, transmission mécanique, phase de détection synchrone) et les règles sur les composants du banc (quels composants sont caractérisés, lequel est monté). Un remontage du banc change la configuration sans rien calibrer, et une calibration ne remonte rien. Sans racine propre, la configuration restait un dossier sans racine d'agrégat, et la règle de place du domaine (D4, D7) la refusait.

## Responsibility

- Enregistrer la caractérisation d'un composant (`record_hardware_component_characterization`) et émettre `HardwareComponentCharacterized`. Enregistrer deux fois sous le même nom complète l'historique du composant.
- Monter un composant (`mount_hardware_component`) : refusé (`ValueError`) tant qu'il n'est pas caractérisé, no-op journalisé s'il est déjà monté, sinon retourne la sélection et émet `HardwareComponentMounted`.
- Dire les deux règles de lecture, une seule fois : le montage courant est la dernière sélection (`current_mounting`, `mounted_component_name`), la caractérisation courante est la dernière entrée du composant (`current_characterization`, `is_component_already_recorded`).
- Résoudre la signature matérielle courante (`resolve_current_hardware_signature`) : les cartes et le capteur montés, le gabarit de repli ne comblant qu'un genre sans composant monté, avec un avertissement (configuration incomplète).

## Design

- `@dataclass` mutable, comme `Calibration` : seule la liste interne `_domain_events` est un état, vidée par la propriété `domain_events`. Le dépôt fait foi pour le catalogue et les montages, la racine ne les garde pas en mémoire.
- Aucune dépendance au bus d'événements : la racine ajoute à sa liste, le service d'application publie.
- Les méthodes de lecture sont statiques : elles ne dépendent d'aucun état de la racine, seulement des séquences que le dépôt fournit.
- Corps repris de `Calibration` sans changement de règle. La calibration importe la configuration (genre de composant, signature matérielle), jamais l'inverse.
