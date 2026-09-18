# adapter_lifecycle_MCU — Intention

## Rationale

Adaptateur gérant le cycle de vie de la connexion série au MCU (ouverture port COM/USB, vérification, fermeture). Séparé des adaptateurs AD9106 et ADS131A04 car le cycle de vie de la connexion série est une préoccupation transverse à tous les périphériques MCU.

## Responsibility

- Ouvrir le port série au MCU avec les bons paramètres (baudrate, timeout).
- Vérifier la connectivité (handshake ou ping).
- Fermer proprement la connexion au shutdown.
- Contribuer à `IHardwareInitializationPort` via le composite.
- À `initialize_all()`, appliquer la config résolue reçue de `MCUCompositionRoot` :
  - ADC (`_configure_adc`) et modes AC/DC des DDS (`_configure_dds`, registres 38/39) : écriture
    registre directe, ces réglages ne sont exposés dans aucun panel donc aucun risque de
    double-lecteur.
  - Fréquence + gain/phase/offset des 4 canaux DDS : **délégués** à
    `AD9106AdvancedConfigurator.apply_config()` (écrivain unique partagé avec le panel Hardware
    Advanced Config) via `nested_channels_to_flat_config()` — pas d'écriture registre propre ici,
    ce qui garantit que les events de sync (`ExcitationFrequencyChanged`,
    `DdsChannelConfigChanged`) sont publiés même au boot.
  - MCU (`_configure_mcu`) : persiste simplement `n_avg` résolu dans `mcu_last_config.json` — pas
    de registre hardware, ce fichier est relu en direct par `ADS131A04Adapter.acquire_sample()`
    à chaque acquisition.

## Design

- **Séparation lifecycle / contrôle hardware** : la connexion série est établie une fois au démarrage, puis tous les controllers (AD9106, ADS131A04) partagent le même `MCUSerialCommunicator`.
- Reçoit `ad9106_configurator: Optional[IHardwareAdvancedConfigurator]` en injection (depuis
  `MCUCompositionRoot`) — sans lui, la config DDS au boot n'est pas appliquée (warning loggé,
  pas de crash).
