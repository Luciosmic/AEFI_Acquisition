# inertial_sensor_presenter — Intention

## Rationale

Le flux du capteur inertiel arrive à 25 Hz depuis un thread de travail, par
l'event bus. Si chaque échantillon redessinait le panneau, l'interface
passerait son temps à se rafraîchir (le panneau n'a besoin que de ~10 Hz pour
être lisible) ; et si le presenter faisait de la logique métier, elle
vivrait dans l'interface. Le presenter est la colle entre le service et le
panneau Qt, rien de plus.

## Responsibility

- Traduire les actions de l'opérateur (connecter, déconnecter, démarrer,
  arrêter) en appels au service `InertialSensorService`.
- S'abonner aux événements domain (échantillon acquis, connexion changée, flux
  en échec) et les traduire en signaux Qt.
- Limiter l'affichage à ~10 Hz : le handler d'événement (thread de travail)
  ne garde que le dernier échantillon ; un `QTimer` du thread Qt émet la
  lecture prête à afficher (`InertialSensorReadingViewModel`).
- Mesurer la cadence réelle à partir des `timestamp_s` des échantillons, sur
  fenêtre glissante (`SampleRateMeter`).

## Design

- Aucun calcul métier : seuls des formats d'affichage et la cadence mesurée
  (grandeur de diagnostic) sont produits ici.
- Le widget ne reçoit jamais de type `domain/` : uniquement des booléens, des
  chaînes et le view model gelé.
- Aucune automatisation cachée : connexion et démarrage sont déclenchés par
  l'opérateur ; le presenter ne reconnecte ni ne redémarre jamais.
- Le timer d'affichage ne tourne que pendant une acquisition.
