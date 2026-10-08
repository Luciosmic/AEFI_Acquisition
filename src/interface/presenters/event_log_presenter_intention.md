# event_log_presenter — Intention

## Rationale

Sans presenter, le panneau Logs appellerait le service directement et
déciderait lui-même quand demander une confirmation, ce qui rendrait le flux
« demander → confirmer → supprimer » impossible à tester sans interface Qt.

## Responsibility

- `refresh()` : publie l'état du journal (`summary_updated`).
- `on_purge_requested()` : relit l'état et, s'il y a des sessions à
  supprimer, demande une confirmation à la vue (`purge_confirmation_needed`)
  avec l'aperçu exact de ce qui sera supprimé.
- `on_purge_confirmed()` : supprime via le service, puis republie l'état.

## Design

- Rien n'est supprimé sans passer par `on_purge_confirmed`, que seule la
  boîte de confirmation de la vue déclenche.
- Le compte rendu passe par le logger : il s'affiche dans le panneau Logs,
  à côté du bouton.
- Une erreur du service est loggée, jamais levée vers Qt.
