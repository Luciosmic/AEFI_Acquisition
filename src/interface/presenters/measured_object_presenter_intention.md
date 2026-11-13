# measured_object_presenter — Intention

## Rationale

Deux panneaux (Scan, Continuous Reading) proposent l'objet mesuré. Sans
presenter commun, chacun appellerait le service à sa façon, et un objet mesuré
enregistré depuis l'un n'apparaîtrait pas dans l'autre avant redémarrage.

## Responsibility

- Pousser la liste des objets mesurés connus (`measured_objects_listed`) au démarrage et
  après chaque `MeasuredObjectRegistered`, quel que soit le panneau d'origine.
- Transmettre une demande « Nouvel objet mesuré… » au service et rapporter son
  issue : `measured_object_registered(measured_object, already_registered)` ou
  `registration_failed(raison)`.
- Transmettre un renommage ou une suppression du panneau « Objets mesurés » et
  rapporter son issue en mots : `management_done(texte)` ou
  `management_failed(raison)`. La liste suit par `MeasuredObjectRenamed` et
  `MeasuredObjectDeleted`, comme après un enregistrement.

## Design

- `QObject`, signaux Qt uniquement ; aucune règle d'orthographe ici (elle est
  dans l'aggregate `MeasuredObjectRegistry`).
- Un seul presenter pour tous les `MeasuredObjectSelector` : c'est le sélecteur qui
  a fait la demande qui sélectionne l'objet mesuré rendu.
