# operator_presenter — Intention

## Rationale

Deux panneaux (Scan, Continuous Reading) proposent l'opérateur. Sans
presenter commun, chacun appellerait le service à sa façon, et un opérateur
enregistré depuis l'un n'apparaîtrait pas dans l'autre avant redémarrage.

## Responsibility

- Pousser la liste des opérateurs connus (`operators_listed`) au démarrage et
  après chaque `OperatorRegistered`, quel que soit le panneau d'origine.
- Transmettre une demande « Nouvel opérateur… » au service et rapporter son
  issue : `operator_registered(operator, already_registered)` ou
  `registration_failed(raison)`.

## Design

- `QObject`, signaux Qt uniquement ; aucune règle d'orthographe ici (elle est
  dans l'aggregate `OperatorRegistry`).
- Un seul presenter pour tous les `OperatorSelector` : c'est le sélecteur qui
  a fait la demande qui sélectionne l'opérateur rendu.
