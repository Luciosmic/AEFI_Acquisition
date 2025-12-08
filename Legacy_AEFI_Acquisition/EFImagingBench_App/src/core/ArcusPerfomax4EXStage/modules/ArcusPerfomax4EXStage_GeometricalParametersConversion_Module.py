# Module de conversion géométrique pour le banc Arcus Performax
# Unité de base : incrément (inc)
# Conversion : 1 inc = 43.6 µm

INC_TO_UM = 43.6
UM_TO_CM = 1e-4
CM_TO_UM = 1e4
RECT_X_MAX_INC = 29121
RECT_Y_MAX_INC = 28160


# Conversion de base

def inc_to_um(inc):
    return inc * INC_TO_UM

def um_to_inc(um):
    return int(round(um / INC_TO_UM))

def um_to_cm(um):
    return um * UM_TO_CM

def cm_to_um(cm):
    return cm * CM_TO_UM

def inc_to_cm(inc):
    return inc * INC_TO_UM * UM_TO_CM

def cm_to_inc(cm):
    """
    Convertit une position en cm en incrément le plus proche,
    retourne (inc, cm_effectif) où cm_effectif est la vraie valeur atteignable.
    """
    um = cm_to_um(cm)
    inc = int(round(um / INC_TO_UM))
    cm_effectif = inc_to_cm(inc)
    return inc, cm_effectif

def clamp_cm_to_inc(cm):
    """
    Alias de cm_to_inc pour compatibilité :
    retourne (inc, cm_effectif)
    """
    return cm_to_inc(cm)

def get_bench_limits_cm():
    x_max_cm = inc_to_cm(RECT_X_MAX_INC)
    y_max_cm = inc_to_cm(RECT_Y_MAX_INC)
    return x_max_cm, y_max_cm

def clamp_rect_cm(x_min, x_max, y_min, y_max):
    x_max_cm, y_max_cm = get_bench_limits_cm()
    x_min = max(0, min(x_min, x_max_cm))
    x_max = max(0, min(x_max, x_max_cm))
    y_min = max(0, min(y_min, y_max_cm))
    y_max = max(0, min(y_max, y_max_cm))
    return x_min, x_max, y_min, y_max


