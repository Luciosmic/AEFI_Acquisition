# mechanical_transmission_view_model — Intention

## Rationale

Sans modèle d'affichage, le panneau de l'onglet « Transmission » importerait les DTO de l'application pour écrire « 20,62 µm par incrément » et « manque : … », et chaque changement de formulation obligerait à rouvrir un widget. L'opérateur qui règle le facteur doit lire en une ligne ce qui est appliqué au banc, avec quoi, et depuis quand.

## Responsibility

- Porter, en texte déjà formulé, ce que l'onglet affiche : titre, détail (moteur, driver, date), avertissement de courant du driver.
- Porter les valeurs qui préremplissent le formulaire (micro-pas, courants, µm par incrément) quand une transmission est enregistrée.
- Décimale française (« 20,62 »).

## Design

- Dataclass figée, construite par `MechanicalTransmissionPresenter` à partir des DTO ; aucun import application ni domaine.
- Deux fabriques : `recorded(...)` (transmission courante) et `missing(...)` (rien d'enregistré : ce qui manque et où le saisir).
