# Réunion Matthieu & Gilles — 2026-06-19 — Reprise notes software

# SOFTWARE

## UI / Affichage

- Afficher la taille de la visu : ???
- Afficher des pixels carrés : FORCER LE RAPPORT D'ECHELLE DANS L'UI
- Ajouter Toggle sur les corrections phase : IMPLEMENTE

## Scan / Motion

- Sur Home : pas de STOP ni E-STOP
- Choix axe privilégié serpentin : Balayage selon Y car favorable mécaniquement
- Serpentin de Home pas opérationnel : ???

# HARDWARE

## Mécanique

- Equilibrer la colonne avec du poids au dessus

## Bruit

- Sans rien le bruit est TROP correllé... A SURVEILLER CAR POSSIBLEMENT DU A ROTATION REFERENTI

---

## Align Phase — Calibration excitation

Faire l'alignement de phase en excitation Y : moins sensible au changement d'excitation X↔Y (quelques mV pour toutes les fréquences).

### Amplitude résiduelle en excitation Y (tension sur axe non-excité)

| Fréquence | Amplitude |
| ---------- | --------- |
| 1 kHz      | 100 µV   |
| 10 kHz     | 100 mV    |
| 100 kHz    | 700 mV    |
| 150 kHz    | 1,1 V     |

### Mesures croisées X/Y

- À 40 kHz en Y : reste ±5 à 10 mV en X
- À 10 kHz : ±200 mV en X ; −200 à +200 mV en X et −100 à −200 mV en Y
- À 150 kHz : −600 à +600 mV en X et +400 à +880 mV en Y

*(Suite le 2026-04-16)*

---

## Angles — Correction axiale

POUVOIR SAUVEGARDER LA CONFIGURATION

PROBLEME DE SIGNE A CORRIGER

Angles de référence : **35,26° ; −45,00° ; −7,20°**

### Sensibilité par axe d'excitation

**Excitation Y :**

- Teta_X → sur Z
- Teta_Y → sur X (très peu sur Z)
- Teta_Z → sur X et Z croisés

**Excitation X :**

- Teta_X → un peu sur Y
- Teta_Y → sur Z et un peu sur Y croisés
- Teta_Z → sur Y et un peu sur Z

### Conditions nullité

- X Teta_Z : Y = 0
- Y Teta_Y : X = 0
- Y Teta_X : Z = 0

### Exit en X

Angles : 0–35° ; 43,63° ; −2,14°
