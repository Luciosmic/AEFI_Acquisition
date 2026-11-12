"""
Physical bench limits (mm), shared by every scan type.

Hardcoded for MVP. TODO: inject from a bench entity (bench_config.json).
"""

PHYSICAL_X_MAX_MM = 1200.0
PHYSICAL_Y_MAX_MM = 1200.0

# Travel of each axis between the homing switch (increment 0) and the + hard limit
# switch, in controller increments. A fact of the rails, independent of the
# µm-per-increment factor: the travel in mm is this count × that factor, and the
# middle of the bench is half this count. Measured on the bench on 2026-11-12
# ("environ": to be re-read with a homing run to both switches).
X_TRAVEL_INCREMENTS = 58_233
Y_TRAVEL_INCREMENTS = 56_346
