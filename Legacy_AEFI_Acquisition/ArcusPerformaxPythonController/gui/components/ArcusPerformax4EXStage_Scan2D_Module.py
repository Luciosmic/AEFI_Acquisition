class Scan2DConfigurator:
    """
    Générateur/configurateur de trajectoire de scan 2D pour le banc.
    - x_min, x_max, y_min, y_max : bornes du scan (en incréments)
    - N : nombre de lignes (nombre de positions X)
    - mode : 'E' (unidirectionnel) ou 'S' (aller-retour)
    """
    def __init__(self, x_min, x_max, y_min, y_max, N, mode='E'):
        self.x_min = int(x_min)
        self.x_max = int(x_max)
        self.y_min = int(y_min)
        self.y_max = int(y_max)
        self.N = int(N)
        self.mode = mode.upper()
        # Calcul des positions X (lignes)
        if N == 1:
            self.x_list = [self.x_min]
        else:
            self.x_list = [int(round(self.x_min + i*(self.x_max-self.x_min)/(N-1))) for i in range(N)]
        # Calcul des positions Y (balayage complet)
        self.y_list = [self.y_min, self.y_max]
    

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

    def _linspace(self, start, stop):
        """
        Génère une liste d'incréments entre start et stop inclus (pas = 1 incrément)
        """
        if start == stop:
            return [start]
        step = 1 if stop > start else -1
        return list(range(start, stop+step, step))
