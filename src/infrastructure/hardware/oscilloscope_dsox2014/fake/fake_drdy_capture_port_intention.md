# fake_drdy_capture_port — Intention

## Rationale

La vraie capture exige l'oscilloscope branché sur DRDY. Sans ce fake, la
caractérisation de l'ODR ne serait ni testable ni utilisable en mode mock ;
et un fake qui rendrait toujours 1 kHz cacherait le cas qui compte : un OSR
écrit mais non appliqué par la puce.

## Responsibility

- Fronts descendants à `f_MOD / OSR`, l'OSR lu sur une source injectée (le
  port d'OSR simulé), sur la fenêtre demandée, avec la gigue mesurée au banc.
- `applied_oversampling_ratio` : simuler une puce qui ignore le registre.
- `fail_reason` : simuler l'absence d'instrument (même mode d'échec que le
  réel).

## Design

- Constantes issues de la mesure du 2026-10-02 (période DRDY 1000,000 µs à
  OSR 4096, écart-type des intervalles 0,229 µs pour un pas de 0,5 µs) — pas
  des valeurs arbitraires (standard de fidélité des doubles). La gigue vient
  de l'échantillonnage de l'oscilloscope : elle est proportionnelle au pas
  (fenêtre / 100 000 points), pas constante.
- Pas de forme d'onde brute simulée (tuples vides) : l'export l'accepte.
- Testé via les tests du service.
