# Encodeur AMT112Q-V — fiche d'intégration banc

Encodeur incrémental modulaire Same Sky (ex-CUI Devices), série AMT11, monté sur l'arbre
arrière des moteurs pas-à-pas Igus, lu par les entrées codeur du contrôleur Arcus PMX-4EX-SA.
Récupéré le 2026-10-02 depuis https://www.sameskydevices.com/amt-resources.

## Documents

| Fichier | Contenu |
| --- | --- |
| `amt11-v.pdf` | Datasheet AMT11 rev 1.11 (06/2026) — remplace l'ancien `ENCODEUR_amt11.pdf` rev 1.09 |
| `amt-assembly-instructions.pdf` | Procédure de montage (outils A/C, sleeve, base, capot) |
| `amt-encoder-mounting-troubleshooting-guide.pdf` | Défauts de montage typiques (applicable AMT11) |
| `amt-viewpoint-user-guide.pdf` | Logiciel AMT Viewpoint (résolution, zéro, diagnostics) |

Les `.txt` sont l'extraction texte des PDF (recherche grep).

## Référence décodée

`AMT11` `2` = radial · `Q` = sortie line driver RS-422 différentielle (A/Ā, B/B̄, Z/Z̄) · `-V` = kit
programmable (résolution par Viewpoint, **2048 PPR par défaut**).

## Chiffres clés pour le banc

| Grandeur | Valeur | Source |
| --- | --- | --- |
| Alimentation | 5 V (4.5–5.5), 16 mA typ. à vide | datasheet |
| Démarrage | 200 ms, **encodeur immobile pendant le démarrage** | datasheet note 1 |
| Résolution par défaut | 2048 PPR → **8192 counts/tour** (PMX décode en 4X) | datasheet + PMX (compteurs de position, `PE`) |
| Index Z | 1 impulsion/tour, position réglable numériquement (commande série `0`) | datasheet p.8 |
| Précision | 0.2° | datasheet |
| Vitesse max à 2048 PPR | 8000 RPM | datasheet |
| Arbre moteur requis | dépassement ≥ 9 mm, tolérance Ø +0/−0.015 mm | datasheet p.2 |
| Arbre Igus MOT-AN-S-060-035-060 | Ø 8.00 mm → sleeve **bleu (8 mm)** | `Moteur_Igus.txt` |
| Sens | A en avance sur B en rotation CCW vue de face | datasheet |
| Entrées PMX | A/B/Z différentiel, 5 MHz max, +5 V fourni (< 200 mA total) | PMX §4.7, §4.15 |
| Ratio StepNLoop attendu (1/16 → 3200 pulses/tour) | SLR = 3200 / 8192 = **0.390625** | PMX §6.22 |

## Câblage AMT112Q (17 pts, JAE FI-W17S) → PMX-4EX-SA (8 pts, 3.81 mm)

| AMT pin | Signal | PMX pin |
| --- | --- | --- |
| 6 | +5 V | 2 |
| 4 | GND | 1 |
| 10 / 11 | A+ / A− | 8 (A) / 7 (/A) |
| 8 / 9 | B+ / B− | 6 (B) / 5 (/B) |
| 12 / 13 | Z+ / Z− | 4 (Z) / 3 (/Z) |
| 1 / 2 / 14 | TX_ENC / RX_ENC / MCLRB (UART 115200 8N1, 5 V) | non câblé — réservé zéro/programmation |

Paires torsadées blindées (A, B, Z). Datasheet : relier le GND encodeur au châssis moteur au plus près.

## Points d'attention

- **Aucun câble ni module de programmation catalogue pour l'AMT11** : la gamme AMT-PGRM / AMT-xxC
  actuelle couvre AMT12x/13x/2x/33x, pas le connecteur 17 pts. Câble à fabriquer (connecteur JAE
  FI-W17S + contacts). Viewpoint inutilisable sans module → on reste à 2048 PPR par défaut,
  suffisant. Changer de résolution = contacter Same Sky.
- Le zéro d'index peut se régler sans Viewpoint : envoyer l'octet ASCII `0` (0x30) sur RX_ENC via
  un adaptateur USB-UART **5 V** ; `Q` = redémarrage. Stocké en non-volatile.
- Le montage/démontage du capot est limité à ~3 cycles (fatigue de la base).
- Polarité de sens réglable côté PMX : commande `PO[axe]`, bit 4 « Encoder Direction » (§6.21).
- Lecture côté logiciel : commandes ASCII `PE` (4 axes) / `E[axe]` via `self._stage.query(...)`
  déjà utilisé dans `driver_arcus_performax4EX.py` ; pylablib expose aussi `get_encoder()`.
