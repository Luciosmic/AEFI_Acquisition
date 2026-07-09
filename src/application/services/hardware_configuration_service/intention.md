# Hardware Configuration Service

## Rationale
Ce service applicatif fournit un point d'entrée unique pour découvrir et configurer les paramètres avancés des équipements hardware. Il permet à l'UI d'interroger et modifier la configuration sans connaître les modules infrastructure concrets.

## Responsibility
- Exposer la liste des identifiants hardware disponibles (`list_hardware_ids`).
- Fournir le nom d'affichage et les spécifications de paramètres pour chaque équipement (`get_hardware_display_name`, `get_parameter_specs`).
- Router une configuration (dictionnaire clé-valeur) vers le fournisseur hardware correspondant (`apply_config`).
- Persister une configuration comme valeur par défaut (`save_config_as_default`).

## Design
- Agrège une liste de `IHardwareAdvancedConfigurator` indexée par `hardware_id` au moment de la construction.
- Utilise le polymorphisme : chaque appel est routé vers le fournisseur identifié par `hardware_id` sans branchement conditionnel.
- Les specs de paramètres sont obtenues via la méthode de classe `get_parameter_specs()` pour éviter la dépendance à l'état de l'instance.
