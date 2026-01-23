# Calibration des Angles de Projection

## Convention de Rotation

**Important :** Les rotations utilisent la convention **extrinsèque 'XYZ'** (rotations autour d'axes fixes du laboratoire), cohérente avec `TransformationService` et le reste de l'application.

- **X, Y, Z (majuscules)** : Rotations extrinsèques (axes fixes du laboratoire)
- Ordre de composition : R = R_z * R_y * R_x (appliquées dans cet ordre)
- Transformation : R transforme Sensor → Source (bench)
  - E_probe = R^-1 * E_bench (champ dans le repère capteur)
  - E_bench = R * E_probe (champ dans le repère banc)

## Matrices de Rotation

Les matrices de rotation pour chaque axe sont définies comme suit :

**Rotation autour de X (fixe) :** $$R_x = \begin{bmatrix} 1 & 0 & 0 \ 0 & \cos\theta_x & -\sin\theta_x \ 0 & \sin\theta_x & \cos\theta_x \end{bmatrix}$$

**Rotation autour de Y (fixe) :** $$R_y = \begin{bmatrix} \cos\theta_y & 0 & \sin\theta_y \ 0 & 1 & 0 \ -\sin\theta_y & 0 & \cos\theta_y \end{bmatrix}$$

**Rotation autour de Z (fixe) :** $$R_z = \begin{bmatrix} \cos\theta_z & \sin\theta_z & 0 \ -\sin\theta_z & \cos\theta_z & 0 \ 0 & 0 & 1 \end{bmatrix}$$

**Composition (extrinsèque XYZ) :** $$R = R_z \cdot R_y \cdot R_x$$

## Procédure de Calibration Automatique

La calibration utilise une **optimisation par moindres carrés** pour trouver les angles qui maximisent l'amplitude complexe du signal dans la direction attendue.

### Principe

Pour chaque configuration d'excitation :
- **X_DIR** : Maximiser la composante X après transformation (minimiser Y et Z)
- **Y_DIR** : Maximiser la composante Y après transformation (minimiser X et Z)

### Fonction Objectif

On cherche à minimiser les résidus suivants :

**Pour X_DIR excitation :**
- Résidu Y : composante Y de E_bench après transformation R * E_probe
- Résidu Z : composante Z de E_bench après transformation R * E_probe

**Pour Y_DIR excitation :**
- Résidu X : composante X de E_bench après transformation R * E_probe
- Résidu Z : composante Z de E_bench après transformation R * E_probe

### Algorithme

1. **Acquisition des mesures :**
   - Configuration X_DIR : acquérir N mesures
   - Configuration Y_DIR : acquérir M mesures

2. **Conversion voltages → vecteurs :**
   - Pour chaque mesure : v_i = sqrt(V_i_in_phase² + V_i_quadrature²) * sign(V_i_in_phase)
   - Préserve l'amplitude complexe et le signe

3. **Optimisation :**
   - Utiliser `scipy.optimize.least_squares` (méthode Levenberg-Marquardt)
   - Minimiser la somme des carrés des résidus
   - Retourner les angles optimisés (θ_x, θ_y, θ_z)

### Notes

- Les formules analytiques directes du document original ne sont pas utilisées car elles supposaient une convention de rotation différente (intrinsèque).
- La méthode par optimisation est plus robuste et fonctionne pour tous les angles, pas seulement les cas particuliers.
- Les angles sont exprimés en degrés et utilisent la convention extrinsèque 'XYZ'.
