# TB6600 Working Configuration

## Tables de référence TB6600

### Microstepping (SW1, SW2, SW3)
| Micro steps | Pulse/rev | SW1 | SW2 | SW3 |
|-------------|-----------|-----|-----|-----|
| 1 (Full) | 200 | ON | ON | OFF |
| 2/A (Half) | 400 | ON | OFF | ON |
| 2/B (Half) | 400 | OFF | ON | ON |
| 4 (1/4) | 800 | ON | OFF | OFF |
| 8 (1/8) | 1600 | OFF | ON | OFF |
| 16 (1/16) | 3200 | OFF | OFF | ON |
| 32 (1/32) | 6400 | OFF | OFF | OFF |

### Current Setting (SW4, SW5, SW6)
| Current (A) | Peak (A) | SW4 | SW5 | SW6 |
|-------------|----------|-----|-----|-----|
| 0.5 | 0.7 | ON | ON | ON |
| 1.0 | 1.2 | ON | OFF | ON |
| 1.5 | 1.7 | ON | ON | OFF |
| 2.0 | 2.2 | ON | OFF | OFF |
| 2.5 | 2.7 | OFF | ON | ON |
| 2.8 | 2.9 | OFF | OFF | ON |
| 3.0 | 3.2 | OFF | ON | OFF |
| 3.5 | 4.0 | OFF | OFF | OFF |

## Configurations qui fonctionnent

### Configuration 1 (1/8 microstepping) - Testée
**DIP Switches:**
- SW1: OFF, SW2: **ON**, SW3: OFF → **8 (1/8)**: 1600 pulses/rev
- SW4: OFF, SW5: **OFF**, SW6: OFF → **3.5A (4.0A Peak)**

**Statut**: ✅ Testée, fonctionne

### Configuration 2 (1/16 microstepping) - FINALE ✅
**DIP Switches:**
- SW1: OFF, SW2: OFF, SW3: **ON** → **16 (1/16)**: 3200 pulses/rev
- SW4: OFF, SW5: OFF, SW6: OFF → **3.5A (4.0A Peak)**

**Statut**: ✅ **CONFIGURATION FINALE** - Testée et validée
**Observations**:
- Le moteur bouge correctement
- Erreur LIMIT si mouvement négatif depuis position 0 (normal, on est à la butée)
- Erreur de position de retour ~30-40 steps (drift possible ou problème de calibration)
- **1/32 ne fonctionne pas** → On reste sur 1/16

### Configuration 3 (1/32 microstepping) - TESTÉE
**DIP Switches:**
- SW1: OFF, SW2: OFF, SW3: **OFF** → **32 (1/32)**: 6400 pulses/rev
- SW4: OFF, SW5: OFF, SW6: OFF → **3.5A (4.0A Peak)**

**Statut**: ❌ Testée, **NE FONCTIONNE PAS** - Aucun mouvement

## Problèmes identifiés

### SW5 (Courant) = ON empêche le mouvement
**Configuration problématique:**
- SW4: OFF, SW5: **ON**, SW6: OFF → **3.0A (3.2A Peak)**
- **Résultat**: ❌ Pas de mouvement

**Configuration qui fonctionne:**
- SW4: OFF, SW5: **OFF**, SW6: OFF → **3.5A (4.0A Peak)**
- **Résultat**: ✅ Mouvement OK

**Conclusion**: 
- Ce n'est PAS un problème de courant trop élevé (3.5A > 3.0A)
- Le problème est spécifique à la configuration 3.0A (SW5=ON, SW4=OFF, SW6=OFF)
- Possible problème hardware ou incompatibilité avec cette configuration spécifique

### Erreurs de position observées
- Retour à 0 donne ~30-40 steps d'erreur
- Possible causes:
  - Drift du moteur (courant trop faible?)
  - Problème de calibration
  - Perte de pas (steps lost)

## Configuration actuelle (SW3=ON)

- **Microstepping**: **1/16** (3200 pulses/rev) - SW1: OFF, SW2: OFF, SW3: ON
- **Courant**: **3.5A (4.0A Peak)** - SW4: OFF, SW5: OFF, SW6: OFF (MAXIMUM)
- **Moteur**: Igus S-AN-060-035-060 (4.2A nominal)
- **Note**: Le courant est au maximum (3.5A), pas au minimum comme pensé initialement

## Tests effectués

1. ✅ **FAIT**: SW3=ON → 1/16 microstepping (3200 pulses/rev) - **FONCTIONNE**
2. ✅ **FAIT**: SW4=OFF, SW5=OFF, SW6=OFF → 3.5A (4.0A Peak) - MAXIMUM
3. ✅ **FAIT**: Test 1/32 microstepping avec courant 3.5A - **NE FONCTIONNE PAS**
4. ⚠️ **À FAIRE**: Calibrer pour 1/16 (3200 pulses/rev) - mettre à jour `microns_per_step`
5. ⚠️ **À FAIRE**: Vérifier si l'erreur de position est due à la calibration ou au drift

## Configuration finale validée

- **Microstepping**: **1/16** (3200 pulses/rev) - SW1: OFF, SW2: OFF, SW3: **ON**
- **Courant**: **3.5A (4.0A Peak)** - SW4: OFF, SW5: OFF, SW6: OFF
- **Moteur**: Igus S-AN-060-035-060 (4.2A nominal)
- **Calibration nécessaire**: Mettre à jour `microns_per_step` pour 1/16

## Notes importantes

- ✅ **1/16 fonctionne** avec courant maximum (3.5A)
- ❌ **1/32 ne fonctionne pas** - Aucun mouvement même avec courant 3.5A
- **Problème identifié**: Configuration 3.0A (SW5=ON) ne fonctionne pas, mais 3.5A (SW5=OFF) fonctionne
- **Calibration**: 
  - Ancienne config (probablement 1/8): 43.6 µm/step
  - Pour 1/16 (3200 pulses/rev): ~21.8 µm/step (43.6 / 2)
  - Actuellement dans config: 10.9 µm/step (pour 1/32) → **À CORRIGER**
- L'erreur de ~30-40 steps suggère soit:
  - Problème de calibration (microns_per_step incorrect)
  - Drift mécanique
  - Perte de pas (mais peu probable avec courant max)

