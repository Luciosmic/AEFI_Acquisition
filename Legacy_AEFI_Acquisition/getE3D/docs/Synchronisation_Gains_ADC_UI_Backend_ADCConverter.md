MOC : 
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation : 
Tags : #NoteAtomique 
Date : 2025-07-04
***

# Problème/Contexte

Dans le cadre du développement du banc d'acquisition AD9106/ADS131A04, il est crucial d'assurer la cohérence entre la configuration matérielle effective des gains ADC et la conversion logicielle des codes ADC en tension. Cette synchronisation est essentielle pour garantir la traçabilité scientifique et la reproductibilité des mesures.

# Pistes/Réponse

**Chaîne de synchronisation des gains ADC** :

1. L'utilisateur choisit/modifie le gain ADC dans l'UI (ex : ComboBox sur chaque canal).
2. L'UI transmet la demande de gain au backend (contrôleur ou AcquisitionManager).
3. Le backend applique le gain matériel via SerialCommunicator (commande envoyée à l'ADC, confirmation matérielle).
4. Le backend met à jour l'ADCConverter avec le mapping `{canal: gain}` via `set_channel_gains`.
5. L'UI affiche les valeurs converties en passant uniquement le numéro de canal à l'ADCConverter, qui utilise le gain effectivement appliqué.

**Schéma textuel** :
```
[Utilisateur]
    ↓ (choix gain)
[UI] ---(demande)--> [Backend/SerialCommunicator] ---(applique)--> [ADC Hardware]
    ↑                                                        |
    |                                                        ↓
[UI] <---(conversion, affichage)--- [ADCConverter] <---(mapping gain à jour)
```

**Points clés pour la traçabilité scientifique** :
- Le gain utilisé pour la conversion logicielle est toujours celui appliqué matériellement.
- Toute modification de gain passe par le backend, qui garantit la cohérence entre hardware et logiciel.
- Le mapping `{canal: gain}` peut être loggé/exporté avec les données pour garantir la reproductibilité.
- Séparation stricte des responsabilités :
    - L'UI affiche et transmet les demandes.
    - Le backend applique et confirme la configuration.
    - L'ADCConverter convertit selon la configuration effective.

**Recommandations** :
- Toujours valider la confirmation matérielle avant de mettre à jour l'ADCConverter.
- Logger toute modification de gain pour audit.
- Exporter le mapping des gains avec les données expérimentales.

# Références
- Voir la section 7.3 du fichier [[AD9106_ADS131A04_Visualization_GUI_tasks.md]] pour la checklist de synchronisation des gains ADC.
- Documentation du module `adc_converter.py` pour l'API de conversion.

# Liens
[[AD9106_ADS131A04_Visualization_GUI_tasks.md]] - Checklist détaillée des tâches de synchronisation des gains ADC, pour garantir la cohérence entre UI, backend et conversion logicielle. 