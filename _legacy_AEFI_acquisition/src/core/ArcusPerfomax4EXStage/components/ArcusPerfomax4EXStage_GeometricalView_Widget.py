from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt


from .ArcusPerfomax4EXStage_GeometricalParametersConversion_Module import get_bench_limits_cm, clamp_rect_cm

class GeometricalViewWidget(QWidget):
    """
    Widget de visualisation géométrique du banc :
    - Affiche la zone utile (rectangle principal)
    - Affiche la position courante
    - Affiche un sous-rectangle (zone d'intérêt)
    Toutes les valeurs sont en cm.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Dimensions du rectangle principal (en cm)
        self.rect_width_cm, self.rect_height_cm = get_bench_limits_cm()
        # Position courante (en cm)
        self.current_pos_cm = (self.rect_width_cm/2, self.rect_height_cm/2)
        # Sous-rectangle (x_min, x_max, y_min, y_max) en cm
        self.subrect_cm = None  # Pas de sous-rectangle par défaut
        self.setMinimumSize(300, 300)

    def set_rect_size(self, largeur_cm, hauteur_cm):
        self.rect_width_cm = largeur_cm
        self.rect_height_cm = hauteur_cm
        self.update()

    def set_current_position(self, x_cm, y_cm):
       # Clamp la position dans la zone utile
        x = max(0, min(x_cm, self.rect_width_cm))
        y = max(0, min(y_cm, self.rect_height_cm))
        self.current_pos_cm = (x, y)
        self.update()

    def set_subrect(self, x_min_cm, x_max_cm, y_min_cm, y_max_cm):
        # Clamp le sous-rectangle dans la zone utile
        x_min, x_max, y_min, y_max = clamp_rect_cm(x_min_cm, x_max_cm, y_min_cm, y_max_cm)
        self.subrect_cm = (x_min, x_max, y_min, y_max)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # Marge minimale autour du rectangle
        margin = 30
        # Ratio physique du banc
        ratio_physique = self.rect_width_cm / self.rect_height_cm
        # Zone de dessin maximale respectant le ratio
        draw_w = w - 2*margin
        draw_h = h - 2*margin
        if draw_w / draw_h > ratio_physique:
            # Trop large, on réduit la largeur
            draw_w = draw_h * ratio_physique
        else:
            # Trop haut, on réduit la hauteur
            draw_h = draw_w / ratio_physique
        # Centrage
        offset_x = (w - draw_w) / 2
        offset_y = (h - draw_h) / 2
        # Ratio pour conversion cm -> pixels
        x_ratio = draw_w / self.rect_width_cm
        y_ratio = draw_h / self.rect_height_cm
        # Rectangle principal (zone utile)
        painter.setPen(QPen(QColor(30, 100, 200), 2))
        painter.setBrush(QBrush(QColor(200, 220, 255, 60)))
        # Qt exige des int pour les coordonnées/dimensions
        painter.drawRect(int(offset_x), int(offset_y), int(draw_w), int(draw_h))
        # Sous-rectangle (zone d'intérêt)
        if self.subrect_cm:
            x_min, x_max, y_min, y_max = self.subrect_cm
            sx = offset_x + x_min * x_ratio
            # Inversion de l'axe Y pour que 0 soit en bas
            sy = offset_y + (self.rect_height_cm - y_max) * y_ratio
            sw = (x_max - x_min) * x_ratio
            sh = (y_max - y_min) * y_ratio
            painter.setPen(QPen(QColor(200, 50, 50), 2, Qt.DashLine))
            painter.setBrush(QBrush(QColor(255, 100, 100, 60)))
            painter.drawRect(int(sx), int(sy), int(sw), int(sh))
        # Position courante (croix)
        x, y = self.current_pos_cm
        px = offset_x + x * x_ratio
        # Inversion de l'axe Y pour que 0 soit en bas
        py = offset_y + (self.rect_height_cm - y) * y_ratio
        painter.setPen(QPen(QColor(0, 150, 0), 2))
        painter.setBrush(QBrush(QColor(0, 200, 0), Qt.SolidPattern))
        size = 8
        painter.drawEllipse(int(px-size/2), int(py-size/2), int(size), int(size))
        painter.drawLine(int(px-10), int(py), int(px+10), int(py))
        painter.drawLine(int(px), int(py-10), int(px), int(py+10))
        # Affichage des valeurs numériques (optionnel)
        painter.setPen(QPen(Qt.black))
        #painter.drawText(int(offset_x+5), int(offset_y-10), f"Zone utile : {self.rect_width_cm:.1f} x {self.rect_height_cm:.1f} cm (origine en bas à gauche)")
        painter.drawText(int(px+10), int(py-10), f"({x:.2f} ; {y:.2f} cm)")
