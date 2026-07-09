# adapter_i_continuous_acquisition_ads131a04 — Intention

## Rationale

Adaptateur Real pour l'acquisition continue (streaming) depuis l'ADS131A04. Contrairement à `adapter_i_acquistion_port_ads131a04` (acquisition synchrone one-shot), cet adaptateur gère le mode streaming de l'ADC avec callback ou queue.

## Responsibility

- Configurer l'ADS131A04 en mode streaming continu.
- Recevoir les échantillons en continu et les transmettre via callback ou publication sur le bus.

## Design

- Distinct de l'adaptateur one-shot : le mode streaming de l'ADS131A04 utilise un protocole différent (DMA/interruption MCU).
- Utilisé par `ContinuousAcquisitionExecutor`.
