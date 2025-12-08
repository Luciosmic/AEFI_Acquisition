class Scan2DConfigurator:
    """
    Générateur/configurateur de trajectoire de scan 2D pour le banc.
    - x_min, x_max, y_min, y_max : bornes du scan (en incréments)
    - N : nombre de lignes (nombre de positions X)
    - y_nb : nombre de points par ligne Y (optionnel)
    - timer_ms : temps d'attente entre lignes (optionnel)
    - mode : 'E' (unidirectionnel) ou 'S' (aller-retour)
    
    Identifie les segments actifs (lignes de scan) vs transitions.
    
    Lève une ValueError si les paramètres sont invalides.
    """
    def __init__(self, x_min, x_max, y_min, y_max, N, y_nb=None, timer_ms=0, mode='E'):
        """
        Initialise la configuration de scan 2D.
        x_min/x_max/y_min/y_max en incréments, N=nombre de lignes X (alias x_nb),
        mode dans {'E','S'}. y_nb et timer_ms sont optionnels.
        
        Lève une ValueError si les paramètres sont invalides.
        """
        # Validation des paramètres
        if x_min is None or x_max is None or y_min is None or y_max is None or N is None:
            raise ValueError("Paramètres obligatoires manquants (x_min, x_max, y_min, y_max, N)")
        
        if not isinstance(mode, str) or mode.upper() not in ['E', 'S']:
            raise ValueError(f"Mode '{mode}' invalide. Modes acceptés: 'E' ou 'S'")
            
        try:
            self.x_min = int(x_min)
            self.x_max = int(x_max)
            self.y_min = int(y_min)
            self.y_max = int(y_max)
            self.N = int(N)
            self.mode = str(mode).upper()
            self.y_nb = int(y_nb) if y_nb is not None else int(N)
            self.timer_ms = int(timer_ms)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Erreur de conversion des paramètres: {e}")
            
        # Validation des valeurs
        if self.N < 1:
            raise ValueError(f"Nombre de lignes (N={self.N}) doit être >= 1")
            
        if self.x_min > self.x_max:
            raise ValueError(f"x_min ({self.x_min}) doit être <= x_max ({self.x_max})")
            
        if self.y_min > self.y_max:
            raise ValueError(f"y_min ({self.y_min}) doit être <= y_max ({self.y_max})")

        # Dictionnaire de configuration construit à l'instanciation
        self.config = {
            'x_min': self.x_min,
            'x_max': self.x_max,
            'y_min': self.y_min,
            'y_max': self.y_max,
            'x_nb': self.N,           # same as N but old name for compatibility
            'y_nb': self.y_nb,
            'mode': self.mode,        # 'E' ou 'S'
            'timer_ms': self.timer_ms # wait before new scan line for stabilization purpose (ms)
        }
        # Calcul des positions X (lignes)
        if N == 1:
            self.x_list = [self.x_min]
        else:
            self.x_list = [int(round(self.x_min + i*(self.x_max-self.x_min)/(N-1))) for i in range(N)]
        # Calcul des positions Y (balayage complet)
        self.y_list = [self.y_min, self.y_max]

    def to_dict(self):
        """Retourne une copie de la configuration normalisée (pour export/état)."""
        return dict(self.config)

    # Méthodes d'accès utilitaires
    
    def get_progress(self, idx):
        """
        Retourne (ligne, colonne) pour l'index idx dans la séquence complète
        """
        n_y = len(self._linspace(self.y_min, self.y_max))
        line = idx // n_y
        col = idx % n_y
        return (line, col)

    def get_flyscan_lines(self):
        """
        Génère la séquence (x, y_start, y_end) pour chaque ligne du scan à la volée.
        - En mode E : toujours y_min -> y_max
        - En mode S : lignes paires y_min->y_max, lignes impaires y_max->y_min
        Retourne une liste de tuples (x, y_start, y_end)
        """
        lines = []
        for i, x in enumerate(self.x_list):
            if self.mode == 'E':
                lines.append((x, self.y_min, self.y_max))
            elif self.mode == 'S':
                if i % 2 == 0:
                    lines.append((x, self.y_min, self.y_max))
                else:
                    lines.append((x, self.y_max, self.y_min))
            else:
                raise ValueError("Mode inconnu : 'E' ou 'S' attendu")
        return lines
    
    def get_segmented_trajectory(self):
        """
        Génère la trajectoire complète avec identification des segments.
        Retourne une liste de dictionnaires avec les informations de chaque segment :
        {
            'id': identifiant unique du segment,
            'type': 'scan_line' ou 'transition',
            'start': (x, y) position de départ,
            'end': (x, y) position d'arrivée,
            'line_index': index de la ligne (None pour transitions)
        }
        """
        segments = []
        segment_id = 0
        
        # Position initiale (origine ou première position de scan)
        current_pos = (self.x_list[0], self.y_min)
        
        for i, (x, y_start, y_end) in enumerate(self.get_flyscan_lines()):
            # Transition vers le début de la ligne si nécessaire
            if current_pos != (x, y_start):
                segments.append({
                    'id': f'transition_{segment_id}',
                    'type': 'transition',
                    'start': current_pos,
                    'end': (x, y_start),
                    'line_index': None
                })
                segment_id += 1
            
            # Ligne de scan active
            segments.append({
                'id': f'scan_line_{segment_id}',
                'type': 'scan_line',
                'start': (x, y_start),
                'end': (x, y_end),
                'line_index': i
            })
            segment_id += 1
            current_pos = (x, y_end)
        
        return segments
    
    def get_points_from_segments(self, segments):
        """
        Convertit les segments en liste de points (x, y) avec métadonnées.
        Retourne une liste de tuples (x, y, segment_info)
        """
        points = []
        for segment in segments:
            # Point de départ avec info segment
            points.append((*segment['start'], segment))
            # Point d'arrivée avec info segment
            points.append((*segment['end'], segment))
        return points

    def _linspace(self, start, stop):
        """
        Génère une liste d'incréments entre start et stop inclus (pas = 1 incrément)
        """
        if start == stop:
            return [start]
        step = 1 if stop > start else -1
        return list(range(start, stop+step, step))
