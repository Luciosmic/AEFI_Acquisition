# adapter_lifecycle_MCU — Intention

## Rationale

Adaptateur gérant le cycle de vie de la connexion série au MCU (ouverture port COM/USB, vérification, fermeture). Séparé des adaptateurs AD9106 et ADS131A04 car le cycle de vie de la connexion série est une préoccupation transverse à tous les périphériques MCU.

## Responsibility

- Ouvrir le port série au MCU avec les bons paramètres (baudrate, timeout).
- Vérifier la connectivité (handshake ou ping).
- Fermer proprement la connexion au shutdown.
- Contribuer à `IHardwareInitializationPort` via le composite.

## Design

- **Séparation lifecycle / contrôle hardware** : la connexion série est établie une fois au démarrage, puis tous les controllers (AD9106, ADS131A04) partagent le même `MCUSerialCommunicator`.
