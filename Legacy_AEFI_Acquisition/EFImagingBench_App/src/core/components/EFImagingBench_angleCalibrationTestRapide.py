from EFImagingBench_angleCalibrationModule import AngleCalculator

calculator = AngleCalculator()

# Données de test
field_x = {'Ex': 1000, 'Ey': 200, 'Ez': 150}  # Config armatures X
field_y = {'Ex': 180, 'Ey': 950, 'Ez': 120}   # Config armatures Y

# Calcul des angles optimaux
result = calculator.optimize_angles(field_x, field_y)
print(f"Angles: {result['angles']}")  # [θx, θy, θz] en degrés



